
# SeasonFeed

Never miss a new TV season. Subscribe to RSS feeds for your favorite shows and get notified when a new season has a premiere date added to TVmaze.

**Live site:** [joetul.github.io/SeasonFeed](https://joetul.github.io/SeasonFeed/)

## How It Works

1. Browse the show list on the site.
2. Click **Copy RSS** to grab a feed URL.
3. Paste it into your RSS reader (FeedFlow, NetNewsWire, etc.).

You can also select multiple shows and export them as an OPML file for bulk import.

Feeds are generated daily using data from the [TVmaze API](https://www.tvmaze.com/api).

## Missing a show?

SeasonFeed is a community-maintained list. Only shows that are manually added and reviewed are included. This keeps the list focused and the feeds reliable.

You can help grow the list in two ways:

- **Request a show** — [open an issue](https://github.com/joetul/SeasonFeed/issues/new?labels=show-request&title=Request%3A+Add+[SHOW+NAME]) with the show name and a [TVmaze](https://www.tvmaze.com) link if possible. We'll add it for you.
- **Add it yourself** — add an entry to `shows.json` and open a pull request.

Shows can be added by name or with an explicit TVmaze ID:

```json
{
  "shows": [
    "Severance",
    { "name": "Andor", "tvmaze_id": 33073 }
  ]
}
```

## License

MIT
