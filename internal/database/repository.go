package database

import (
	"context"
	"database/sql"
	"fmt"
	"time"

	_ "modernc.org/sqlite"
)

type Repository struct {
	db *sql.DB
}

func NewRepository(dbPath string) (*Repository, error) {
	db, err := sql.Open("sqlite", dbPath)
	if err != nil {
		return nil, fmt.Errorf("opening database: %w", err)
	}

	repo := &Repository{db: db}
	if err := repo.migrate(); err != nil {
		return nil, fmt.Errorf("migrating database: %w", err)
	}

	return repo, nil
}

func (r *Repository) migrate() error {
	_, err := r.db.Exec(`
		CREATE TABLE IF NOT EXISTS channel_configs (
			channel_id TEXT PRIMARY KEY,
			day TEXT NOT NULL,
			time TEXT NOT NULL,
			enabled INTEGER NOT NULL DEFAULT 1,
			last_selected_user TEXT,
			created_at TEXT NOT NULL,
			updated_at TEXT NOT NULL
		)
	`)
	return err
}

func (r *Repository) GetChannelConfig(ctx context.Context, channelID string) (*ChannelConfig, error) {
	var cfg ChannelConfig
	var lastUser sql.NullString
	var enabled int
	var createdAt, updatedAt string

	err := r.db.QueryRowContext(ctx, `
		SELECT channel_id, day, time, enabled, last_selected_user, created_at, updated_at
		FROM channel_configs WHERE channel_id = ?
	`, channelID).Scan(
		&cfg.ChannelID, &cfg.Day, &cfg.Time, &enabled,
		&lastUser, &createdAt, &updatedAt,
	)

	if err == sql.ErrNoRows {
		return nil, nil
	}
	if err != nil {
		return nil, fmt.Errorf("querying channel config: %w", err)
	}

	cfg.Enabled = enabled == 1
	if lastUser.Valid {
		cfg.LastSelectedUser = &lastUser.String
	}

	cfg.CreatedAt, _ = time.Parse(time.RFC3339, createdAt)
	cfg.UpdatedAt, _ = time.Parse(time.RFC3339, updatedAt)

	return &cfg, nil
}

func (r *Repository) SaveChannelConfig(ctx context.Context, cfg *ChannelConfig) error {
	now := time.Now().UTC().Format(time.RFC3339)

	enabled := 0
	if cfg.Enabled {
		enabled = 1
	}

	_, err := r.db.ExecContext(ctx, `
		INSERT INTO channel_configs (channel_id, day, time, enabled, last_selected_user, created_at, updated_at)
		VALUES (?, ?, ?, ?, ?, ?, ?)
		ON CONFLICT(channel_id) DO UPDATE SET
			day = excluded.day,
			time = excluded.time,
			enabled = excluded.enabled,
			last_selected_user = excluded.last_selected_user,
			updated_at = excluded.updated_at
	`, cfg.ChannelID, cfg.Day, cfg.Time, enabled, cfg.LastSelectedUser, now, now)

	if err != nil {
		return fmt.Errorf("saving channel config: %w", err)
	}

	return nil
}

func (r *Repository) GetAllEnabledConfigs(ctx context.Context) ([]*ChannelConfig, error) {
	rows, err := r.db.QueryContext(ctx, `
		SELECT channel_id, day, time, enabled, last_selected_user, created_at, updated_at
		FROM channel_configs WHERE enabled = 1
	`)
	if err != nil {
		return nil, fmt.Errorf("querying enabled configs: %w", err)
	}
	defer rows.Close()

	var configs []*ChannelConfig
	for rows.Next() {
		var cfg ChannelConfig
		var lastUser sql.NullString
		var enabled int
		var createdAt, updatedAt string

		if err := rows.Scan(
			&cfg.ChannelID, &cfg.Day, &cfg.Time, &enabled,
			&lastUser, &createdAt, &updatedAt,
		); err != nil {
			return nil, fmt.Errorf("scanning config row: %w", err)
		}

		cfg.Enabled = enabled == 1
		if lastUser.Valid {
			cfg.LastSelectedUser = &lastUser.String
		}
		cfg.CreatedAt, _ = time.Parse(time.RFC3339, createdAt)
		cfg.UpdatedAt, _ = time.Parse(time.RFC3339, updatedAt)

		configs = append(configs, &cfg)
	}

	return configs, rows.Err()
}

func (r *Repository) UpdateLastSelectedUser(ctx context.Context, channelID, userID string) error {
	now := time.Now().UTC().Format(time.RFC3339)

	_, err := r.db.ExecContext(ctx, `
		UPDATE channel_configs
		SET last_selected_user = ?, updated_at = ?
		WHERE channel_id = ?
	`, userID, now, channelID)

	if err != nil {
		return fmt.Errorf("updating last selected user: %w", err)
	}

	return nil
}

func (r *Repository) DeleteChannelConfig(ctx context.Context, channelID string) error {
	_, err := r.db.ExecContext(ctx, `
		DELETE FROM channel_configs WHERE channel_id = ?
	`, channelID)

	if err != nil {
		return fmt.Errorf("deleting channel config: %w", err)
	}

	return nil
}

func (r *Repository) Close() error {
	return r.db.Close()
}
