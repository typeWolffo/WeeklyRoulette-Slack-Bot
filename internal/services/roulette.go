package services

import (
	"context"
	"fmt"
	"log/slog"
	"math/rand"

	"github.com/slack-go/slack"
	"github.com/typeWolffo/weeklyroulette-bot/internal/database"
)

type Member struct {
	ID       string
	Name     string
	RealName string
	Title    string
}

type RouletteResult struct {
	Success        bool
	Error          string
	SelectedMember *Member
	TotalMembers   int
	Message        string
	IsTest         bool
}

type RouletteService struct {
	client    *slack.Client
	db        *database.Repository
	anthropic *AnthropicService
}

func NewRouletteService(client *slack.Client, db *database.Repository, anthropic *AnthropicService) *RouletteService {
	return &RouletteService{
		client:    client,
		db:        db,
		anthropic: anthropic,
	}
}

func (s *RouletteService) GetChannelMembers(ctx context.Context, channelID string) ([]Member, error) {
	params := &slack.GetUsersInConversationParameters{
		ChannelID: channelID,
	}

	userIDs, _, err := s.client.GetUsersInConversationContext(ctx, params)
	if err != nil {
		return nil, fmt.Errorf("getting channel members: %w", err)
	}

	var activeMembers []Member
	for _, userID := range userIDs {
		user, err := s.client.GetUserInfoContext(ctx, userID)
		if err != nil {
			slog.Warn("failed to get user info", "user_id", userID, "error", err)
			continue
		}

		if user.IsBot || user.Deleted || user.ID == "USLACKBOT" {
			continue
		}

		name := user.Profile.DisplayName
		if name == "" {
			name = user.RealName
		}
		if name == "" {
			name = user.Name
		}

		title := user.Profile.Title
		if title == "" {
			title = "Developer"
		}

		activeMembers = append(activeMembers, Member{
			ID:       user.ID,
			Name:     name,
			RealName: user.RealName,
			Title:    title,
		})
	}

	return activeMembers, nil
}

func (s *RouletteService) SelectRandomMember(members []Member, lastSelectedUserID *string) *Member {
	if len(members) == 0 {
		return nil
	}

	availableMembers := make([]Member, 0, len(members))

	if lastSelectedUserID != nil && len(members) > 1 {
		for _, m := range members {
			if m.ID != *lastSelectedUserID {
				availableMembers = append(availableMembers, m)
			}
		}
		if len(availableMembers) > 0 {
			slog.Info("excluding last selected user", "user_id", *lastSelectedUserID)
		} else {
			availableMembers = members
			slog.Warn("could not exclude last user, using all members")
		}
	} else {
		availableMembers = members
	}

	rand.Shuffle(len(availableMembers), func(i, j int) {
		availableMembers[i], availableMembers[j] = availableMembers[j], availableMembers[i]
	})

	memberNames := make([]string, len(availableMembers))
	for i, m := range availableMembers {
		memberNames[i] = m.Name
	}
	slog.Info("selecting from members", "count", len(availableMembers), "names", memberNames)

	selected := &availableMembers[rand.Intn(len(availableMembers))]
	slog.Info("selected member", "name", selected.Name, "id", selected.ID)

	return selected
}

func (s *RouletteService) RunRoulette(ctx context.Context, channelID string, testMode bool) (*RouletteResult, error) {
	config, err := s.db.GetChannelConfig(ctx, channelID)
	if err != nil {
		return nil, fmt.Errorf("getting channel config: %w", err)
	}

	if config == nil && !testMode {
		return &RouletteResult{
			Success: false,
			Error:   "Channel is not configured. Use `/weeklyroulette config`",
		}, nil
	}

	members, err := s.GetChannelMembers(ctx, channelID)
	if err != nil {
		return nil, fmt.Errorf("getting channel members: %w", err)
	}

	if len(members) == 0 {
		return &RouletteResult{
			Success: false,
			Error:   "No active channel members found",
		}, nil
	}

	var lastSelectedUserID *string
	if config != nil {
		lastSelectedUserID = config.LastSelectedUser
	}

	selectedMember := s.SelectRandomMember(members, lastSelectedUserID)
	if selectedMember == nil {
		return &RouletteResult{
			Success: false,
			Error:   "Failed to select member",
		}, nil
	}

	var kudoMessage string
	if !testMode && s.anthropic.IsConfigured() {
		slackHandle := fmt.Sprintf("<@%s>", selectedMember.ID)
		msg, err := s.anthropic.GenerateKudoRain(ctx, slackHandle, selectedMember.Title)
		if err != nil {
			slog.Warn("failed to generate kudo rain", "error", err)
		} else {
			kudoMessage = msg
		}
		slog.Info("selected member with title", "name", selectedMember.Name, "title", selectedMember.Title)
	}

	var message string
	if kudoMessage != "" && !testMode {
		message = fmt.Sprintf("✨ %s", kudoMessage)
	} else {
		prefix := "🎲 **Test Roulette**"
		if !testMode {
			prefix = "🎯 **Weekly Roulette**"
		}
		message = fmt.Sprintf("%s\n🎉 Selected person: <@%s>\n", prefix, selectedMember.ID)
	}

	if !testMode && config != nil {
		if err := s.db.UpdateLastSelectedUser(ctx, channelID, selectedMember.ID); err != nil {
			slog.Warn("failed to update last selected user", "error", err)
		}
	}

	return &RouletteResult{
		Success:        true,
		SelectedMember: selectedMember,
		TotalMembers:   len(members),
		Message:        message,
		IsTest:         testMode,
	}, nil
}

func (s *RouletteService) SendRouletteMessage(ctx context.Context, channelID string, testMode bool) (*RouletteResult, error) {
	result, err := s.RunRoulette(ctx, channelID, testMode)
	if err != nil {
		return nil, err
	}

	if result.Success {
		_, _, err := s.client.PostMessageContext(ctx, channelID,
			slack.MsgOptionText(result.Message, false),
			slack.MsgOptionDisableLinkUnfurl(),
			slack.MsgOptionDisableMediaUnfurl(),
		)
		if err != nil {
			return &RouletteResult{
				Success: false,
				Error:   fmt.Sprintf("Error sending message: %s", err),
			}, nil
		}
	}

	return result, nil
}

func (s *RouletteService) GetChannelStatus(ctx context.Context, channelID string) map[string]interface{} {
	config, err := s.db.GetChannelConfig(ctx, channelID)
	if err != nil || config == nil {
		return map[string]interface{}{
			"configured": false,
			"message": "❌ Channel is not configured yet.\n" +
				"Use `/weeklyroulette config` to set up schedule.",
		}
	}

	statusEmoji := "✅"
	statusText := "enabled"
	if !config.Enabled {
		statusEmoji = "⏸️"
		statusText = "disabled"
	}

	dayName, ok := database.DayDisplayNames[config.Day]
	if !ok {
		dayName = config.Day
	}

	message := fmt.Sprintf(
		"%s **WeeklyRoulette Status**\n\n"+
			"📅 Day: %s\n"+
			"🕒 Time: %s (Polish time)\n"+
			"🔄 Status: %s\n\n"+
			"💡 Use `/weeklyroulette config` to change settings",
		statusEmoji, dayName, config.Time, statusText,
	)

	return map[string]interface{}{
		"configured": true,
		"enabled":    config.Enabled,
		"config":     config,
		"message":    message,
	}
}

func (s *RouletteService) DB() *database.Repository {
	return s.db
}
