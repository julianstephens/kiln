package contract

import "time"

type BuildInfo struct {
	Commit  string    `json:"commit"`
	Date    time.Time `json:"date"`
	Version string    `json:"version"`
}

func NewBuildInfo() (*BuildInfo, error) {
	t, err := time.Parse(time.DateOnly, BuildDate)
	if err != nil {
		return nil, err
	}
	return &BuildInfo{
		Version: BuildVersion,
		Commit:  BuildCommit,
		Date:    t,
	}, nil
}

var (
	BuildVersion = "0.1.0"
	BuildDate    = "unknown"
	BuildCommit  = "unknown"
)
