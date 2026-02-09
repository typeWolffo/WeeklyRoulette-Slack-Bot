package bot

import (
	"context"
	"fmt"
	"log/slog"

	"github.com/slack-go/slack"
	"github.com/slack-go/slack/slackevents"
	"github.com/slack-go/slack/socketmode"
	"github.com/typeWolffo/weeklyroulette-bot/internal/config"
	"github.com/typeWolffo/weeklyroulette-bot/internal/database"
	"github.com/typeWolffo/weeklyroulette-bot/internal/handlers"
	"github.com/typeWolffo/weeklyroulette-bot/internal/services"
)

type Bot struct {
	client        *slack.Client
	socketClient  *socketmode.Client
	db            *database.Repository
	roulette      *services.RouletteService
	scheduler     *services.SchedulerService
	cmdHandler    *handlers.CommandHandler
	actionHandler *handlers.ActionHandler
	eventHandler  *handlers.EventHandler
}

func New(cfg *config.Config) (*Bot, error) {
	db, err := database.NewRepository(cfg.GetDatabasePath())
	if err != nil {
		return nil, fmt.Errorf("initializing database: %w", err)
	}

	client := slack.New(
		cfg.SlackBotToken,
		slack.OptionAppLevelToken(cfg.SlackAppToken),
	)

	socketClient := socketmode.New(
		client,
		socketmode.OptionDebug(cfg.Environment == "development"),
	)

	anthropic := services.NewAnthropicService(cfg.AnthropicAPIKey)
	roulette := services.NewRouletteService(client, db, anthropic)

	scheduler, err := services.NewSchedulerService(roulette, db)
	if err != nil {
		return nil, fmt.Errorf("initializing scheduler: %w", err)
	}

	cmdHandler := handlers.NewCommandHandler(roulette, scheduler)
	actionHandler := handlers.NewActionHandler(roulette, scheduler)
	eventHandler := handlers.NewEventHandler(client)

	return &Bot{
		client:        client,
		socketClient:  socketClient,
		db:            db,
		roulette:      roulette,
		scheduler:     scheduler,
		cmdHandler:    cmdHandler,
		actionHandler: actionHandler,
		eventHandler:  eventHandler,
	}, nil
}

func (b *Bot) Run(ctx context.Context) error {
	b.scheduler.Start()
	go b.handleEvents(ctx)

	slog.Info("bot started, connecting to Slack...")

	// socketClient.Run() blocks forever and has no way to stop it,
	// so we run it in a goroutine and use select to unblock on ctx cancel.
	errCh := make(chan error, 1)
	go func() {
		errCh <- b.socketClient.Run()
	}()

	select {
	case <-ctx.Done():
		slog.Info("context cancelled, exiting...")
		return ctx.Err()
	case err := <-errCh:
		return err
	}
}

func (b *Bot) Stop() {
	slog.Info("stopping bot...")
	b.scheduler.Stop()
	if err := b.db.Close(); err != nil {
		slog.Error("error closing database", "error", err)
	}
	slog.Info("bot stopped")
}

func (b *Bot) handleEvents(ctx context.Context) {
	for {
		select {
		case <-ctx.Done():
			return
		case evt := <-b.socketClient.Events:
			slog.Debug("received event", "type", evt.Type)
			switch evt.Type {
			case socketmode.EventTypeSlashCommand:
				slog.Info("slash command received")
				b.handleSlashCommand(evt)
			case socketmode.EventTypeInteractive:
				slog.Info("interactive event received")
				b.handleInteractive(evt)
			case socketmode.EventTypeEventsAPI:
				slog.Info("events API event received")
				b.handleEventsAPI(evt)
			case socketmode.EventTypeConnecting:
				slog.Info("connecting to Slack...")
			case socketmode.EventTypeConnected:
				slog.Info("connected to Slack")
			case socketmode.EventTypeConnectionError:
				slog.Error("connection error")
			case socketmode.EventTypeHello:
				slog.Info("hello from Slack")
			default:
				slog.Debug("unhandled event type", "type", evt.Type)
			}
		}
	}
}

func (b *Bot) handleSlashCommand(evt socketmode.Event) {
	cmd, ok := evt.Data.(slack.SlashCommand)
	if !ok {
		slog.Warn("unexpected slash command data type")
		return
	}

	b.socketClient.Ack(*evt.Request)

	if cmd.Command != "/weeklyroulette" {
		return
	}

	response, err := b.cmdHandler.Handle(cmd, b.client)
	if err != nil {
		slog.Error("command handler error", "error", err)
		response = fmt.Sprintf("❌ Error: %s", err)
	}

	if response != "" {
		_, _, err := b.client.PostMessage(cmd.ChannelID,
			slack.MsgOptionText(response, false),
			slack.MsgOptionResponseURL(cmd.ResponseURL, slack.ResponseTypeEphemeral),
		)
		if err != nil {
			slog.Error("failed to send command response", "error", err)
		}
	}
}

func (b *Bot) handleInteractive(evt socketmode.Event) {
	callback, ok := evt.Data.(slack.InteractionCallback)
	if !ok {
		slog.Warn("unexpected interaction data type")
		return
	}

	switch callback.Type {
	case slack.InteractionTypeViewSubmission:
		if callback.View.CallbackID == "config_modal" {
			b.socketClient.Ack(*evt.Request)
			if err := b.actionHandler.HandleConfigModalSubmission(callback.View, b.client); err != nil {
				slog.Error("modal submission error", "error", err)
			}
		}

	case slack.InteractionTypeBlockActions:
		b.socketClient.Ack(*evt.Request)
		for _, action := range callback.ActionCallback.BlockActions {
			b.actionHandler.HandleBlockAction(action)
		}

	default:
		b.socketClient.Ack(*evt.Request)
	}
}

func (b *Bot) handleEventsAPI(evt socketmode.Event) {
	eventsAPIEvent, ok := evt.Data.(slackevents.EventsAPIEvent)
	if !ok {
		slog.Warn("unexpected events API data type")
		return
	}

	b.socketClient.Ack(*evt.Request)

	switch eventsAPIEvent.Type {
	case slackevents.CallbackEvent:
		innerEvent := eventsAPIEvent.InnerEvent

		switch ev := innerEvent.Data.(type) {
		case *slackevents.AppMentionEvent:
			b.eventHandler.HandleAppMention(ev)
		case *slackevents.MemberJoinedChannelEvent:
			b.eventHandler.HandleMemberJoined(ev)
		case *slackevents.MemberLeftChannelEvent:
			b.eventHandler.HandleMemberLeft(ev)
		}
	}
}
