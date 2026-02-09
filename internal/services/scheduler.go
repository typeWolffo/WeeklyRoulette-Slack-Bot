package services

import (
	"context"
	"fmt"
	"log/slog"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/go-co-op/gocron"
	"github.com/typeWolffo/weeklyroulette-bot/internal/database"
)

type SchedulerService struct {
	scheduler *gocron.Scheduler
	roulette  *RouletteService
	db        *database.Repository
	mu        sync.RWMutex
	jobs      map[string]*gocron.Job
	polandTZ  *time.Location
	running   bool
}

func NewSchedulerService(roulette *RouletteService, db *database.Repository) (*SchedulerService, error) {
	polandTZ, err := time.LoadLocation("Europe/Warsaw")
	if err != nil {
		return nil, fmt.Errorf("loading timezone: %w", err)
	}

	s := gocron.NewScheduler(time.UTC)

	return &SchedulerService{
		scheduler: s,
		roulette:  roulette,
		db:        db,
		jobs:      make(map[string]*gocron.Job),
		polandTZ:  polandTZ,
	}, nil
}

func (s *SchedulerService) convertPolishTimeToUTC(timeStr string) (string, error) {
	parts := strings.Split(timeStr, ":")
	if len(parts) != 2 {
		return timeStr, fmt.Errorf("invalid time format: %s", timeStr)
	}

	hour, err := strconv.Atoi(parts[0])
	if err != nil {
		return timeStr, fmt.Errorf("invalid hour: %s", parts[0])
	}

	minute, err := strconv.Atoi(parts[1])
	if err != nil {
		return timeStr, fmt.Errorf("invalid minute: %s", parts[1])
	}

	now := time.Now().In(s.polandTZ)
	polishTime := time.Date(now.Year(), now.Month(), now.Day(), hour, minute, 0, 0, s.polandTZ)
	utcTime := polishTime.UTC()

	return fmt.Sprintf("%02d:%02d", utcTime.Hour(), utcTime.Minute()), nil
}

func dayToWeekday(day string) time.Weekday {
	switch strings.ToLower(day) {
	case "monday":
		return time.Monday
	case "tuesday":
		return time.Tuesday
	case "wednesday":
		return time.Wednesday
	case "thursday":
		return time.Thursday
	case "friday":
		return time.Friday
	case "saturday":
		return time.Saturday
	case "sunday":
		return time.Sunday
	default:
		return time.Monday
	}
}

func (s *SchedulerService) scheduleChannelRoulette(config *database.ChannelConfig) error {
	if !config.Enabled {
		return nil
	}

	utcTime, err := s.convertPolishTimeToUTC(config.Time)
	if err != nil {
		slog.Warn("failed to convert time to UTC", "time", config.Time, "error", err)
		utcTime = config.Time
	}

	jobKey := fmt.Sprintf("%s_%s_%s", config.ChannelID, config.Day, config.Time)

	channelID := config.ChannelID
	job, err := s.scheduler.Every(1).Week().Weekday(dayToWeekday(config.Day)).At(utcTime).Do(func() {
		slog.Info("running scheduled roulette", "channel", channelID)
		ctx := context.Background()

		result, err := s.roulette.SendRouletteMessage(ctx, channelID, false)
		if err != nil {
			slog.Error("scheduled roulette failed", "channel", channelID, "error", err)
			return
		}

		if result.Success {
			slog.Info("roulette completed", "channel", channelID, "selected", result.SelectedMember.Name)
		} else {
			slog.Error("roulette failed", "channel", channelID, "error", result.Error)
		}
	})

	if err != nil {
		return fmt.Errorf("scheduling roulette: %w", err)
	}

	s.mu.Lock()
	s.jobs[jobKey] = job
	s.mu.Unlock()

	slog.Info("scheduled roulette",
		"channel", config.ChannelID,
		"day", config.Day,
		"polish_time", config.Time,
		"utc_time", utcTime,
	)

	return nil
}

func (s *SchedulerService) UpdateSchedules() {
	slog.Info("updating roulette schedules")

	s.mu.Lock()
	s.scheduler.Clear()
	s.jobs = make(map[string]*gocron.Job)
	s.mu.Unlock()

	ctx := context.Background()
	configs, err := s.db.GetAllEnabledConfigs(ctx)
	if err != nil {
		slog.Error("failed to get enabled configs", "error", err)
		return
	}

	if len(configs) == 0 {
		slog.Info("no enabled roulette configurations found")
		return
	}

	for _, config := range configs {
		if err := s.scheduleChannelRoulette(config); err != nil {
			slog.Error("failed to schedule channel", "channel", config.ChannelID, "error", err)
		}
	}

	slog.Info("updated schedules", "count", len(configs))
}

func (s *SchedulerService) Start() {
	s.mu.Lock()
	if s.running {
		s.mu.Unlock()
		slog.Warn("scheduler is already running")
		return
	}
	s.running = true
	s.mu.Unlock()

	s.UpdateSchedules()
	s.scheduler.StartAsync()
	slog.Info("scheduler started")
}

func (s *SchedulerService) Stop() {
	s.mu.Lock()
	defer s.mu.Unlock()

	if !s.running {
		return
	}

	slog.Info("stopping scheduler")
	s.scheduler.Stop()
	s.running = false
	s.jobs = make(map[string]*gocron.Job)
	slog.Info("scheduler stopped")
}

func (s *SchedulerService) ForceUpdateSchedules() {
	s.mu.RLock()
	running := s.running
	s.mu.RUnlock()

	if running {
		s.UpdateSchedules()
	} else {
		slog.Warn("scheduler is not running, schedules will be updated when started")
	}
}

func (s *SchedulerService) GetScheduleInfo() []map[string]interface{} {
	s.mu.RLock()
	defer s.mu.RUnlock()

	var jobsInfo []map[string]interface{}

	for jobKey, job := range s.jobs {
		parts := strings.Split(jobKey, "_")
		if len(parts) >= 3 {
			channelID := strings.Join(parts[:len(parts)-2], "_")
			day := parts[len(parts)-2]
			timeStr := parts[len(parts)-1]

			var nextRun string
			if nextRunTime := job.NextRun(); !nextRunTime.IsZero() {
				nextRun = nextRunTime.Format(time.RFC3339)
			}

			jobsInfo = append(jobsInfo, map[string]interface{}{
				"channel_id": channelID,
				"day":        day,
				"time":       timeStr,
				"next_run":   nextRun,
				"job_key":    jobKey,
			})
		}
	}

	return jobsInfo
}
