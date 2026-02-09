package main

import (
	"context"
	"log/slog"
	"os"
	"os/signal"
	"syscall"

	"github.com/joho/godotenv"
	"github.com/typeWolffo/weeklyroulette-bot/internal/bot"
	"github.com/typeWolffo/weeklyroulette-bot/internal/config"
)

func main() {
	_ = godotenv.Load()

	logLevel := slog.LevelInfo
	if os.Getenv("LOG_LEVEL") == "DEBUG" {
		logLevel = slog.LevelDebug
	}
	slog.SetDefault(slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{
		Level: logLevel,
	})))

	slog.Info("starting WeeklyRoulette bot...")

	cfg, err := config.Load()
	if err != nil {
		slog.Error("failed to load config", "error", err)
		os.Exit(1)
	}

	b, err := bot.New(cfg)
	if err != nil {
		slog.Error("failed to create bot", "error", err)
		os.Exit(1)
	}

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		sig := <-sigCh
		slog.Info("received signal, shutting down...", "signal", sig)
		b.Stop()
		cancel()
	}()

	if err := b.Run(ctx); err != nil {
		if ctx.Err() == nil {
			slog.Error("bot error", "error", err)
			os.Exit(1)
		}
	}

	slog.Info("goodbye!")
}
