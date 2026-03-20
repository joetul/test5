#!/usr/bin/env python3
"""Generate per-show RSS feeds for TV season updates using TVmaze."""

import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent
SHOWS_PATH = ROOT / "shows.json"
FEEDS_DIR = ROOT / "feeds"
DATA_DIR = ROOT / "data"
STATE_PATH = DATA_DIR / "state.json"
INDEX_PATH = FEEDS_DIR / "index.json"

ATOM_NS = "http://www.w3.org/2005/Atom"
API_BASE = "https://api.tvmaze.com"
USER_AGENT = "tv-season-rss/1.0"
# TVmaze allows at least 20 calls / 10 seconds per IP. A 0.6s interval keeps
# us below that baseline while avoiding unnecessary passive waiting.
MIN_REQUEST_INTERVAL_SECONDS = float(os.getenv("TVMAZE_MIN_REQUEST_INTERVAL_SECONDS", "0.6"))
RETRY_429_MIN_SECONDS = float(os.getenv("TVMAZE_RETRY_429_MIN_SECONDS", "4"))
RETRY_429_MAX_SECONDS = float(os.getenv("TVMAZE_RETRY_429_MAX_SECONDS", "20"))
MAX_429_RETRIES = int(os.getenv("TVMAZE_MAX_429_RETRIES", "6"))


ET.register_namespace("atom", ATOM_NS)


def slugify(name):
    lowered = (name or "").lower().strip()
    lowered = re.sub(r"[^a-z0-9\s-]", " ", lowered)
    lowered = re.sub(r"\s+", " ", lowered).strip()
    slug = lowered.replace(" ", "-")
    return slug or "show"


def read_json(path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print(f"Invalid JSON in {path}. Using fallback.")
        return fallback


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def now_iso_utc():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def now_rfc822():
    return datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")


def date_to_rfc822(date_text):
    if not date_text:
        return now_rfc822()
    try:
        dt = datetime.strptime(date_text, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
    except ValueError:
        return "Thu, 01 Jan 1970 00:00:00 GMT"


def has_valid_premiere_date(season):
    date_text = season.get("premiereDate")
    if not date_text:
        return False
    try:
        datetime.strptime(date_text, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def unix_to_rfc822(unix_value):
    try:
        value = int(unix_value)
        dt = datetime.fromtimestamp(value, tz=timezone.utc)
        return dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
    except (TypeError, ValueError, OSError):
        return None


def detect_site_url():
    env_site = os.getenv("SITE_URL", "").strip()
    if env_site:
        return env_site.rstrip("/")

    repository = os.getenv("GITHUB_REPOSITORY", "").strip()
    if repository and "/" in repository:
        owner, repo = repository.split("/", 1)
        return f"https://{owner}.github.io/{repo}"

    return "https://joetul.github.io/SeasonFeed"


def network_name(show_data):
    network = show_data.get("network") or {}
    web_channel = show_data.get("webChannel") or {}
    return network.get("name") or web_channel.get("name") or "Unknown"



class TVmazeClient:
    def __init__(self):
        self.last_request_time = 0.0

    def _respect_rate_limit(self):
        elapsed = time.monotonic() - self.last_request_time
        if elapsed < MIN_REQUEST_INTERVAL_SECONDS:
            time.sleep(MIN_REQUEST_INTERVAL_SECONDS - elapsed)

    @staticmethod
    def _retry_after_delay(exc, attempt_number):
        retry_after = exc.headers.get("Retry-After") if exc.headers else None
        if retry_after:
            try:
                header_delay = float(retry_after)
                return max(RETRY_429_MIN_SECONDS, min(RETRY_429_MAX_SECONDS, header_delay))
            except ValueError:
                pass

        exponential_delay = RETRY_429_MIN_SECONDS * (2 ** max(0, attempt_number - 1))
        return min(RETRY_429_MAX_SECONDS, exponential_delay)

    def get_json(self, url):
        retries = 0
        while True:
            self._respect_rate_limit()
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    self.last_request_time = time.monotonic()
                    body = response.read().decode("utf-8")
                    return json.loads(body)
            except urllib.error.HTTPError as exc:
                self.last_request_time = time.monotonic()
                if exc.code == 429:
                    retries += 1
                    if retries > MAX_429_RETRIES:
                        print(f"Too many 429 retries for {url}. Skipping.")
                        return None
                    retry_delay = self._retry_after_delay(exc, retries)
                    print(f"429 from TVmaze for {url}. Waiting {retry_delay:.1f}s and retrying.")
                    time.sleep(retry_delay)
                    continue
                if exc.code == 404:
                    return None
                print(f"HTTP {exc.code} for {url}. Skipping.")
                return None
            except urllib.error.URLError as exc:
                self.last_request_time = time.monotonic()
                print(f"URL error for {url}: {exc}. Skipping.")
                return None
            except json.JSONDecodeError:
                self.last_request_time = time.monotonic()
                print(f"Invalid JSON returned by {url}. Skipping.")
                return None


def resolve_show(spec, state, client):
    if isinstance(spec, str):
        requested_name = spec.strip()
        explicit_id = None
    elif isinstance(spec, dict):
        requested_name = str(spec.get("name", "")).strip()
        explicit_id = spec.get("tvmaze_id")
    else:
        return None

    if not requested_name:
        return None

    state_entry = state.get(slugify(requested_name), {})
    cached_id = state_entry.get("tvmaze_id")

    if explicit_id or cached_id:
        tvmaze_id = explicit_id or cached_id
        return client.get_json(f"{API_BASE}/shows/{tvmaze_id}")

    encoded = urllib.parse.quote(requested_name, safe="")
    return client.get_json(f"{API_BASE}/singlesearch/shows?q={encoded}")


def season_sort_key(season):
    premiere = season.get("premiereDate") or ""
    number = season_number(season)
    return number, premiere


def season_number(season):
    number = season.get("number")
    try:
        return int(number)
    except (TypeError, ValueError):
        return 0


def compute_last_build_date(seasons):
    """Return the RFC 822 date of the most recent season premiere, or epoch."""
    parsed_dates = []
    for season in seasons:
        date_text = season.get("premiereDate")
        if not date_text:
            continue
        try:
            parsed_dates.append(datetime.strptime(date_text, "%Y-%m-%d"))
        except ValueError:
            continue
    if parsed_dates:
        latest = max(parsed_dates).replace(tzinfo=timezone.utc)
        return latest.strftime("%a, %d %b %Y %H:%M:%S GMT")

    return "Thu, 01 Jan 1970 00:00:00 GMT"


def format_date_human(date_text):
    """Convert YYYY-MM-DD to a human-readable date, e.g. '18 March 2026'."""
    if not date_text or date_text == "TBD":
        return date_text or "TBD"
    try:
        dt = datetime.strptime(date_text, "%Y-%m-%d")
        return dt.strftime("%-d %B %Y")
    except ValueError:
        return date_text


def build_item_description(premiere, finale, episode_text, season_url):
    p = format_date_human(premiere)
    f = format_date_human(finale)
    return f"Premiere: {p}\nFinale: {f}\nEpisodes: {episode_text}\n\n{season_url}"


def build_feed(show_data, seasons, slug, site_url):
    show_name = show_data.get("name", "Unknown Show")
    tvmaze_url = show_data.get("url") or f"https://www.tvmaze.com/shows/{show_data.get('id')}"
    feed_url = f"{site_url}/feeds/{slug}.xml"

    rss = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = f"{show_name} Season Alerts"
    ET.SubElement(channel, "description").text = (
        f"New season notifications for {show_name} from TVmaze metadata."
    )
    ET.SubElement(channel, "link").text = tvmaze_url
    ET.SubElement(channel, "language").text = "en"
    ET.SubElement(channel, "lastBuildDate").text = compute_last_build_date(seasons)

    ET.SubElement(
        channel,
        f"{{{ATOM_NS}}}link",
        {
            "href": feed_url,
            "rel": "self",
            "type": "application/rss+xml",
        },
    )

    dated_seasons = [season for season in seasons if has_valid_premiere_date(season)]
    sorted_seasons = sorted(dated_seasons, key=season_sort_key, reverse=True)
    for season in sorted_seasons:
        number = season_number(season)
        premiere = season.get("premiereDate") or "TBD"
        finale = season.get("endDate") or "TBD"
        episode_count = season.get("episodeOrder")
        episode_text = str(episode_count) if episode_count is not None else "Unknown"
        season_url = season.get("url") or tvmaze_url

        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = f"{show_name} — Season {number}"
        ET.SubElement(item, "description").text = build_item_description(premiere, finale, episode_text, season_url)
        ET.SubElement(item, "guid", {"isPermaLink": "false"}).text = f"seasonfeed:{slug}:s{number}"
        ET.SubElement(item, "pubDate").text = date_to_rfc822(season.get("premiereDate"))
        ET.SubElement(item, "link").text = season_url

    tree = ET.ElementTree(rss)
    ET.indent(tree, space="  ")
    xml_bytes = ET.tostring(rss, encoding="utf-8")
    return b"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" + xml_bytes + b"\n"


def latest_season_number(seasons):
    numbers = [season_number(s) for s in seasons]
    return max(numbers) if numbers else 0


def main():
    FEEDS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    shows_doc = read_json(SHOWS_PATH, {"shows": []})
    show_specs = shows_doc.get("shows", [])
    if not isinstance(show_specs, list):
        print("shows.json must contain a 'shows' array.")
        return 1

    state = read_json(STATE_PATH, {})
    if not isinstance(state, dict):
        state = {}

    client = TVmazeClient()
    site_url = detect_site_url()

    manifest = []
    generated_slugs = set()

    for spec in show_specs:
        show_data = resolve_show(spec, state, client)
        if not show_data:
            print(f"Skipping unresolved show spec: {spec}")
            continue

        show_id = show_data.get("id")
        if not show_id:
            print(f"Skipping show with missing ID: {show_data}")
            continue

        show_name = show_data.get("name", "Unknown Show")
        slug = slugify(show_name)

        seasons = client.get_json(f"{API_BASE}/shows/{show_id}/seasons")
        if seasons is None:
            print(f"Skipping show due to season fetch failure: {show_name}")
            continue
        if not isinstance(seasons, list):
            print(f"Unexpected season payload for {show_name}. Skipping.")
            continue

        latest = latest_season_number(seasons)
        previous_latest = state.get(slug, {}).get("latest_season")
        try:
            previous_latest = int(previous_latest) if previous_latest is not None else None
        except (TypeError, ValueError):
            previous_latest = None

        if previous_latest is not None and latest > previous_latest:
            print(f"NEW SEASON DETECTED: {show_name} ({previous_latest} -> {latest})")

        feed_url = f"{site_url}/feeds/{slug}.xml"

        feed_bytes = build_feed(show_data, seasons, slug, site_url)
        feed_path = FEEDS_DIR / f"{slug}.xml"
        if not feed_path.exists() or feed_path.read_bytes() != feed_bytes:
            feed_path.write_bytes(feed_bytes)
        generated_slugs.add(slug)

        image_data = show_data.get("image") or {}
        tvmaze_url = show_data.get("url") or f"https://www.tvmaze.com/shows/{show_id}"

        manifest.append(
            {
                "name": show_name,
                "slug": slug,
                "feed_url": feed_url,
                "tvmaze_url": tvmaze_url,
                "network": network_name(show_data),
                "status": show_data.get("status") or "Unknown",
                "latest_season": latest,
                "image": image_data.get("medium"),
                "premiered": show_data.get("premiered"),
            }
        )

        existing_state = state.get(slug, {})
        if (
            existing_state.get("tvmaze_id") == show_id
            and existing_state.get("name") == show_name
            and existing_state.get("latest_season") == latest
        ):
            last_checked = existing_state.get("last_checked") or now_iso_utc()
        else:
            last_checked = now_iso_utc()

        state[slug] = {
            "tvmaze_id": show_id,
            "name": show_name,
            "latest_season": latest,
            "last_checked": last_checked,
        }

    for existing_feed in FEEDS_DIR.glob("*.xml"):
        if existing_feed.stem not in generated_slugs:
            existing_feed.unlink()

    manifest.sort(key=lambda item: item.get("name", "").lower())
    write_json(INDEX_PATH, manifest)

    ordered_state = dict(sorted(state.items(), key=lambda item: item[0]))
    write_json(STATE_PATH, ordered_state)

    print(f"Processed {len(manifest)} shows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
