package handlers

import (
	"context"
	"fmt"
	"log/slog"

	"github.com/slack-go/slack"
	"github.com/typeWolffo/weeklyroulette-bot/internal/database"
	"github.com/typeWolffo/weeklyroulette-bot/internal/services"
)

type CommandHandler struct {
	roulette  *services.RouletteService
	scheduler *services.SchedulerService
}

func NewCommandHandler(roulette *services.RouletteService, scheduler *services.SchedulerService) *CommandHandler {
	return &CommandHandler{
		roulette:  roulette,
		scheduler: scheduler,
	}
}

func (h *CommandHandler) Handle(cmd slack.SlashCommand, client *slack.Client) (string, error) {
	text := cmd.Text
	channelID := cmd.ChannelID

	slog.Info("received command", "command", text, "channel", channelID, "user", cmd.UserID)

	switch text {
	case "", "help":
		return h.handleHelp(), nil
	case "config":
		return h.handleConfig(cmd, client)
	case "test":
		return h.handleTest(channelID)
	case "status":
		return h.handleStatus(channelID)
	default:
		slog.Warn("unknown command", "text", text)
		return "❓ Unknown command. Use `/weeklyroulette help` to see available options.", nil
	}
}

func (h *CommandHandler) handleHelp() string {
	return `WeeklyRoulette - Help

Available commands:
• ` + "`/weeklyroulette config`" + ` - configure selection schedule
• ` + "`/weeklyroulette status`" + ` - check current settings
• ` + "`/weeklyroulette test`" + ` - run a test selection
• ` + "`/weeklyroulette help`" + ` - show this help

How it works:
1. Configure day and time for selection
2. Bot automatically picks a random person from channel
3. Selection happens every week at the set time
`
}

func (h *CommandHandler) handleConfig(cmd slack.SlashCommand, client *slack.Client) (string, error) {
	ctx := context.Background()
	currentConfig, _ := h.roulette.DB().GetChannelConfig(ctx, cmd.ChannelID)

	modal := buildConfigModal(cmd.ChannelID, currentConfig)

	_, err := client.OpenView(cmd.TriggerID, modal)
	if err != nil {
		return "", fmt.Errorf("opening config modal: %w", err)
	}

	return "", nil
}

func (h *CommandHandler) handleTest(channelID string) (string, error) {
	slog.Info("starting test roulette", "channel", channelID)

	ctx := context.Background()
	result, err := h.roulette.SendRouletteMessage(ctx, channelID, true)
	if err != nil {
		slog.Error("test roulette failed with error", "channel", channelID, "error", err)
		return "", err
	}

	if result.Success {
		slog.Info("test roulette completed",
			"channel", channelID,
			"selected_user", result.SelectedMember.Name,
			"selected_id", result.SelectedMember.ID,
			"total_members", result.TotalMembers,
		)
		return fmt.Sprintf("✅ Test completed successfully!\n\n%s\n\n💡 *This was just a test. Regular selection will happen automatically according to schedule.*", result.Message), nil
	}

	slog.Warn("test roulette failed", "channel", channelID, "error", result.Error)
	return fmt.Sprintf("❌ Test failed: %s", result.Error), nil
}

func (h *CommandHandler) handleStatus(channelID string) (string, error) {
	ctx := context.Background()
	status := h.roulette.GetChannelStatus(ctx, channelID)
	return status["message"].(string), nil
}

func buildConfigModal(channelID string, currentConfig *database.ChannelConfig) slack.ModalViewRequest {
	defaultDay := "friday"
	defaultTime := "15:00"
	defaultEnabled := true

	if currentConfig != nil {
		defaultDay = currentConfig.Day
		defaultTime = currentConfig.Time
		defaultEnabled = currentConfig.Enabled
	}

	dayOptions := make([]*slack.OptionBlockObject, 0, len(database.ValidDays))
	for _, day := range database.ValidDays {
		displayName := database.DayDisplayNames[day]
		dayOptions = append(dayOptions, slack.NewOptionBlockObject(
			day,
			slack.NewTextBlockObject(slack.PlainTextType, displayName, false, false),
			nil,
		))
	}

	var timeOptions []*slack.OptionBlockObject
	for hour := 9; hour < 17; hour++ {
		for minute := 0; minute < 60; minute += 5 {
			timeStr := fmt.Sprintf("%02d:%02d", hour, minute)
			timeOptions = append(timeOptions, slack.NewOptionBlockObject(
				timeStr,
				slack.NewTextBlockObject(slack.PlainTextType, timeStr, false, false),
				nil,
			))
		}
	}

	var initialDayOption *slack.OptionBlockObject
	for _, opt := range dayOptions {
		if opt.Value == defaultDay {
			initialDayOption = opt
			break
		}
	}

	var initialTimeOption *slack.OptionBlockObject
	for _, opt := range timeOptions {
		if opt.Value == defaultTime {
			initialTimeOption = opt
			break
		}
	}

	enabledText := "Enabled"
	enabledValue := "true"

	if !defaultEnabled {
		enabledText = "Disabled"
		enabledValue = "false"
	}

	initialEnabledOption := slack.NewOptionBlockObject(
		enabledValue,
		slack.NewTextBlockObject(slack.PlainTextType, enabledText, false, false),
		nil,
	)

	blocks := slack.Blocks{
		BlockSet: []slack.Block{
			slack.NewSectionBlock(
				slack.NewTextBlockObject(slack.MarkdownType, "🎲 *Configure weekly selection schedule*", false, false),
				nil, nil,
			),
			slack.NewDividerBlock(),
			slack.NewSectionBlock(
				slack.NewTextBlockObject(slack.MarkdownType, "📅 *Choose day of week:*", false, false),
				nil,
				slack.NewAccessory(slack.NewOptionsSelectBlockElement(
					slack.OptTypeStatic,
					slack.NewTextBlockObject(slack.PlainTextType, "Select day", false, false),
					"day_select",
					dayOptions...,
				).WithInitialOption(initialDayOption)),
			),
			slack.NewSectionBlock(
				slack.NewTextBlockObject(slack.MarkdownType, "🕒 *Choose time (Polish time):*", false, false),
				nil,
				slack.NewAccessory(slack.NewOptionsSelectBlockElement(
					slack.OptTypeStatic,
					slack.NewTextBlockObject(slack.PlainTextType, "Select time", false, false),
					"time_select",
					timeOptions...,
				).WithInitialOption(initialTimeOption)),
			),
			slack.NewSectionBlock(
				slack.NewTextBlockObject(slack.MarkdownType, "🔄 *Status:*", false, false),
				nil,
				slack.NewAccessory(slack.NewOptionsSelectBlockElement(
					slack.OptTypeStatic,
					slack.NewTextBlockObject(slack.PlainTextType, "Select status", false, false),
					"enabled_select",
					slack.NewOptionBlockObject("true", slack.NewTextBlockObject(slack.PlainTextType, "Enabled", false, false), nil),
					slack.NewOptionBlockObject("false", slack.NewTextBlockObject(slack.PlainTextType, "Disabled", false, false), nil),
				).WithInitialOption(initialEnabledOption)),
			),
			slack.NewDividerBlock(),
			slack.NewContextBlock("",
				slack.NewTextBlockObject(slack.MarkdownType, "💡 *Bot will automatically select one person from the channel at the chosen time*", false, false),
			),
		},
	}

	return slack.ModalViewRequest{
		Type:            slack.VTModal,
		CallbackID:      "config_modal",
		Title:           slack.NewTextBlockObject(slack.PlainTextType, "Configuration", false, false),
		Submit:          slack.NewTextBlockObject(slack.PlainTextType, "Save", false, false),
		Close:           slack.NewTextBlockObject(slack.PlainTextType, "Cancel", false, false),
		PrivateMetadata: channelID,
		Blocks:          blocks,
	}
}
