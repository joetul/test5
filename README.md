
# SeasonFeed

Never miss a new TV season. Subscribe to RSS feeds for your favorite shows. Each feed updates when a new season gets a premiere date on TVmaze.

**Live site:** [joetul.github.io/SeasonFeed](https://joetul.github.io/SeasonFeed/)

## How to Use

1. Browse the show list on the site.
2. Click **Copy URL** to grab a feed URL.
3. Paste it into your RSS reader (FeedFlow, NetNewsWire, etc.).

You can also select multiple shows and export them as an OPML file for bulk import.

## How It Works

A script runs daily and fetches season data from the [TVmaze API](https://www.tvmaze.com/api) for every show in `shows.json`. It generates one RSS feed file per show and updates a JSON index. The site is a static HTML page hosted on GitHub Pages that reads the index and lets you browse, search, and copy feed URLs.

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

## Data Attribution

TV show data (season dates, episode counts, images) is provided by [TVmaze](https://www.tvmaze.com) and licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). The data has been adapted (fields selected and dates reformatted). The generated feeds and update pages inherit this license for the data they contain.

## License

The source code for this project is licensed under the [MIT License](LICENSE). The TV show data in the generated feeds is licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) by TVmaze.
