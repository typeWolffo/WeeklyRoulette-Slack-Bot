package database

import "slices"

import "time"

var ValidDays = []string{
	"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
}

var DayDisplayNames = map[string]string{
	"monday":    "Poniedziałek",
	"tuesday":   "Wtorek",
	"wednesday": "Środa",
	"thursday":  "Czwartek",
	"friday":    "Piątek",
	"saturday":  "Sobota",
	"sunday":    "Niedziela",
}

type ChannelConfig struct {
	ChannelID        string
	Day              string
	Time             string
	Enabled          bool
	LastSelectedUser *string
	CreatedAt        time.Time
	UpdatedAt        time.Time
}

func IsValidDay(day string) bool {
	return slices.Contains(ValidDays, day)
}
