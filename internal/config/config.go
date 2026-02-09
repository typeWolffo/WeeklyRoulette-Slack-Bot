package config

import (
	"fmt"
	"strings"

	"github.com/kelseyhightower/envconfig"
)

type Config struct {
	SlackBotToken      string `envconfig:"SLACK_BOT_TOKEN" required:"true"`
	SlackAppToken      string `envconfig:"SLACK_APP_TOKEN" required:"true"`
	SlackSigningSecret string `envconfig:"SLACK_SIGNING_SECRET" required:"true"`
	AnthropicAPIKey    string `envconfig:"ANTHROPIC_API_KEY"`
	DatabaseURL        string `envconfig:"DATABASE_URL" default:"weeklyroulette.db"`
	Environment        string `envconfig:"ENVIRONMENT" default:"development"`
	LogLevel           string `envconfig:"LOG_LEVEL" default:"INFO"`
}

func Load() (*Config, error) {
	var cfg Config
	if err := envconfig.Process("", &cfg); err != nil {
		return nil, fmt.Errorf("loading config: %w", err)
	}
	return &cfg, nil
}

func (c *Config) IsProduction() bool {
	return c.Environment == "production"
}

func (c *Config) HasAnthropicKey() bool {
	return c.AnthropicAPIKey != ""
}

func (c *Config) GetDatabasePath() string {
	path := c.DatabaseURL
	path = strings.TrimPrefix(path, "sqlite:///")
	path = strings.TrimPrefix(path, "sqlite://")
	return path
}
