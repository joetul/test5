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

## License

MIT. See `LICENSE`.
