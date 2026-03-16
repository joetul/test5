# TV Season Tracker RSS

Generate RSS feeds for upcoming TV seasons.

This project tracks shows from TVmaze data and publishes one feed per show in `feeds/`.

## How It Works

- `shows.json` defines the shows to track.
- `generate_feeds.py` fetches TV metadata and builds feed files.
- `feeds/index.json` is the feed directory used by `index.html`.
- `data/state.json` stores lightweight state between runs.

## Project Structure

```text
.
├── generate_feeds.py
├── shows.json
├── index.html
├── feeds/
│   ├── index.json
│   └── *.xml
└── data/
    └── state.json
```

## Shows Configuration

`shows.json` supports either a plain show name or an explicit `tvmaze_id`.

Example:

```json
{
  "shows": [
    "Severance",
    { "name": "Andor", "tvmaze_id": 33073 }
  ]
}
```

## Output

- Per-show RSS files are written to `feeds/<show-slug>.xml`.
- The landing page reads `feeds/index.json`.

## TVmaze API Pacing

This generator follows TVmaze's public guidance of at least `20 calls / 10 seconds` per IP by default.

- Default pacing: `0.6s` between requests (about `16.7 calls / 10s`).
- On HTTP `429`, retries are backed off adaptively (uses `Retry-After` header when provided, otherwise exponential backoff).

Optional environment variables:

- `TVMAZE_MIN_REQUEST_INTERVAL_SECONDS` (default: `0.6`)
- `TVMAZE_RETRY_429_MIN_SECONDS` (default: `4`)
- `TVMAZE_RETRY_429_MAX_SECONDS` (default: `20`)
- `TVMAZE_MAX_429_RETRIES` (default: `6`)

## License

MIT. See `LICENSE`.
