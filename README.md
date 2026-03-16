# tv-season-rss

Track upcoming TV season drops and publish one RSS feed per show using only GitHub Actions and GitHub Pages.

This project is fully static and infrastructure-free:

- GitHub Actions fetches TV metadata from TVmaze and regenerates feeds.
- GitHub Pages serves the generated XML feeds and a small browseable landing page.
- No server, no database, no paid API, no package installs.

## Repository Layout

```text
tv-season-rss/
├── .github/
│   └── workflows/
│       └── update-feeds.yml
├── generate_feeds.py
├── shows.json
├── index.html
├── .gitignore
├── LICENSE
├── README.md
├── feeds/
│   └── index.json
└── data/
		└── state.json
```

## 1) Create Your Repository

Use either approach:

1. Fork this repository on GitHub.
2. Or create a new repo named tv-season-rss and copy all files into it.

Push the files to your default branch (for example, main).

## 2) Enable GitHub Pages

1. Open repository Settings.
2. Go to Pages.
3. Under Build and deployment:
4. Source: Deploy from a branch.
5. Branch: main (or your default branch), Folder: /(root).
6. Save.

After deployment, your site URL is usually:

```text
https://<owner>.github.io/<repo>
```

## 3) Enable Actions Write Permissions

The workflow commits updated feeds and state files back to the repository.

1. Open repository Settings.
2. Go to Actions, then General.
3. Under Workflow permissions, select Read and write permissions.
4. Save.

## 4) Edit shows.json

Use plain names for easy setup, or include tvmaze_id for exact matching:

```json
{
	"_comment": "Add shows you want to track. Use a plain string or {\"name\": \"...\", \"tvmaze_id\": 12345} for exact matching.",
	"shows": [
		"Severance",
		{ "name": "Andor", "tvmaze_id": 33073 }
	]
}
```

Every push that changes shows.json triggers feed regeneration automatically.

## 5) Trigger the First Run

1. Open the Actions tab.
2. Select the Update TV Season Feeds workflow.
3. Click Run workflow (workflow_dispatch).

The workflow also runs every 6 hours via cron.

## 6) Subscribe to Feeds

After the workflow runs:

1. Open your GitHub Pages site.
2. Find a show card.
3. Click RSS to copy that show feed URL.
4. Paste into any RSS reader.

Feed files are also available directly under:

```text
https://<owner>.github.io/<repo>/feeds/<show-slug>.xml
```

## 7) Troubleshooting

### Feeds are not generating

- Check Actions logs for generate_feeds.py output.
- Confirm workflow permissions are set to Read and write.
- Confirm shows.json is valid JSON.
- If TVmaze temporarily rate-limits requests, rerun later.

### GitHub Pages site is not working

- Ensure Pages is enabled for branch main and root folder.
- Confirm repository visibility and Pages eligibility.
- Wait a few minutes after first enable; initial publish can be delayed.

### A show is not found or maps incorrectly

- Add an explicit tvmaze_id in shows.json for exact matching.
- You can find IDs by checking the show URL on TVmaze.

### Workflow stopped running after inactivity

GitHub may disable scheduled workflows after about 60 days of inactivity.

- Re-enable it in the Actions UI.
- Or push a small commit to re-activate repository activity.

## 8) Cost

This setup is designed to be completely free for typical personal usage:

- GitHub Actions runs within GitHub free-tier limits.
- GitHub Pages static hosting is free-tier compatible.
- TVmaze API is public and free for metadata queries.

## 9) Legal and Data Scope

This project stores and serves only TV metadata such as:

- Show title
- Season number
- Premiere and finale dates
- Episode count
- Network name

No copyrighted episode video, scripts, or full content is reproduced.

TVmaze API documentation:

https://www.tvmaze.com/api

## 10) License

Licensed under the MIT License. See LICENSE.