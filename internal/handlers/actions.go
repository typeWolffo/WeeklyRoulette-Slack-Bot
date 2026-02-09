package handlers

import (
	"context"
	"fmt"
	"log/slog"

	"github.com/slack-go/slack"
	"github.com/typeWolffo/weeklyroulette-bot/internal/database"
	"github.com/typeWolffo/weeklyroulette-bot/internal/services"
)

type ActionHandler struct {
	roulette  *services.RouletteService
	scheduler *services.SchedulerService
}

func NewActionHandler(roulette *services.RouletteService, scheduler *services.SchedulerService) *ActionHandler {
	return &ActionHandler{
		roulette:  roulette,
		scheduler: scheduler,
	}
}

func (h *ActionHandler) HandleConfigModalSubmission(view slack.View, client *slack.Client) error {
	channelID := view.PrivateMetadata
	values := view.State.Values

	var day, timeStr string
	var enabled bool

	for _, blockValues := range values {
		if selectVal, ok := blockValues["day_select"]; ok {
			day = selectVal.SelectedOption.Value
		}
		if selectVal, ok := blockValues["time_select"]; ok {
			timeStr = selectVal.SelectedOption.Value
		}
		if selectVal, ok := blockValues["enabled_select"]; ok {
			enabled = selectVal.SelectedOption.Value == "true"
		}
	}

	if day == "" || timeStr == "" {
		return fmt.Errorf("missing required fields")
	}

	ctx := context.Background()
	config := &database.ChannelConfig{
		ChannelID: channelID,
		Day:       day,
		Time:      timeStr,
		Enabled:   enabled,
	}

	if err := h.roulette.DB().SaveChannelConfig(ctx, config); err != nil {
		slog.Error("failed to save channel config", "error", err)
		return fmt.Errorf("saving config: %w", err)
	}

	h.scheduler.ForceUpdateSchedules()

	statusText := "enabled"
	if !enabled {
		statusText = "disabled"
	}

	dayName := database.DayDisplayNames[day]
	message := fmt.Sprintf(
		"✅ Configuration saved!\n\n"+
			"📅 Day: %s\n"+
			"🕒 Time: %s (Polish time)\n"+
			"🔄 Status: %s",
		dayName, timeStr, statusText,
	)

	_, _, err := client.PostMessage(channelID,
		slack.MsgOptionText(message, false),
	)
	if err != nil {
		slog.Warn("failed to send confirmation message", "error", err)
	}

	slog.Info("channel config saved",
		"channel", channelID,
		"day", day,
		"time", timeStr,
		"enabled", enabled,
	)

	return nil
}

func (h *ActionHandler) HandleBlockAction(action *slack.BlockAction) {
	slog.Debug("block action received", "action_id", action.ActionID, "value", action.SelectedOption.Value)
}
