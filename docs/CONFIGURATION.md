# Configuration guide

The program reads `settings.json` from the same folder as `website_monitor.py`. Copy `settings.example.json` to `settings.json`, then edit that local file. Git ignores `settings.json` because it may contain private URLs or request headers.

## Settings

| Name | Purpose | Example |
| --- | --- | --- |
| `target_url` | Complete page address. Must begin with HTTP or HTTPS. | `https://example.com/news` |
| `target_name` | Short label used in filenames and alerts. | `news-page` |
| `content_selector` | Element whose text to compare. Blank tries `main`, `article`, then `body`. | `main`, `#content`, `.post` |
| `check_interval_seconds` | Seconds between checks. | `30` |
| `retention_days` | Delete Markdown snapshots older than this. | `3` |
| `max_consecutive_errors` | Exit after this many failed checks in a row. | `5` |
| `error_backoff_seconds` | Delays after successive errors; the final value repeats. | `[4, 8, 16, 32]` |
| `output_dir` | Folder for snapshots. `~` means your home folder. The sample is Termux-oriented; change it on other systems. | `~/WebsiteBackups` or `~/storage/downloads/WebsiteBackups` |
| `doh_url` | Optional curl DNS-over-HTTPS endpoint. Blank uses system DNS. | `https://one.one.one.one/dns-query` |
| `headers` | Optional documented request headers. | `{}` |
| `android_notifications` | Enable Termux:API notifications if available. | `true` |

## Selecting page text

The default automatic choice is the first available `main`, `article`, or `body` element. You can specify one simple selector:

- `main` or `article` selects a tag.
- `#content` selects an element with `id="content"`.
- `.post-body` selects an element with that class.
- `div#content` or `section.post-body` combines a tag with an ID or class.
- `main,article` tries selectors in order.

Complex CSS selectors (descendant selectors, attributes, or pseudo-classes) are not supported. Common navigation, header/footer, script, and hidden elements are skipped. Whitespace is normalized so cosmetic spacing changes usually do not trigger a snapshot. If a server returns plain text or JSON, leave the selector blank.

## DNS-over-HTTPS

Normally leave `doh_url` blank. If the phone's regular DNS cannot find a host but curl succeeds using DNS-over-HTTPS, install curl and set `doh_url` to that working endpoint. For example: `https://one.one.one.one/dns-query`. A set `doh_url` makes the script use curl and IPv4. If curl is missing or the DoH service is unavailable, monitoring reports an error and follows the configured retry limit.

## Access headers and privacy

If a website officially supports a request header, add it to `headers` in your local `settings.json`. For example, the shape is `"headers": {"Header-Name": "private-value"}`. Do not put real access codes, passwords, cookies, API keys, or private page URLs in the script or in files you upload to GitHub. Do not use this monitor to evade site protections or access pages without permission.

## Baselines, changes, and retention

The first successful check stores the current text as a baseline and sends no edit alert. Later it compares a SHA-256 hash; changed text is saved as a timestamped `.md` snapshot. The hash state is stored under `~/.website-change-monitor/` and is separate from the repository. On each check it permanently deletes `.md` files in the output folder whose modification time is older than `retention_days`.

## Polling load

The sample uses 4 seconds to match the original quick-check use case. That can make up to 900 requests per hour. Increase the interval for normal use, follow the website's rules, and avoid aggressive polling. No polling interval can guarantee that a short-lived edit is captured.