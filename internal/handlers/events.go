package handlers

import (
	"log/slog"

	"github.com/slack-go/slack"
	"github.com/slack-go/slack/slackevents"
)

type EventHandler struct {
	client *slack.Client
}

func NewEventHandler(client *slack.Client) *EventHandler {
	return &EventHandler{
		client: client,
	}
}

func (h *EventHandler) HandleAppMention(event *slackevents.AppMentionEvent) {
	slog.Info("app mentioned", "channel", event.Channel, "user", event.User)

	message := `Hello! I'm WeeklyRoulette bot.

Use ` + "`/weeklyroulette help`" + ` to see available commands.

**Quick start:**
1. ` + "`/weeklyroulette config`" + ` - set up schedule
2. ` + "`/weeklyroulette test`" + ` - run a test
3. ` + "`/weeklyroulette status`" + ` - check settings`

	_, _, err := h.client.PostMessage(event.Channel,
		slack.MsgOptionText(message, false),
	)
	if err != nil {
		slog.Error("failed to respond to mention", "error", err)
	}
}

func (h *EventHandler) HandleMemberJoined(event *slackevents.MemberJoinedChannelEvent) {
	slog.Info("member joined channel", "channel", event.Channel, "user", event.User)
}

func (h *EventHandler) HandleMemberLeft(event *slackevents.MemberLeftChannelEvent) {
	slog.Info("member left channel", "channel", event.Channel, "user", event.User)
}
