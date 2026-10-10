# Website Change Monitor

A lightweight Python tool for checking a web page, extracting its readable text, and saving a timestamped Markdown snapshot whenever that text changes. Configure it for ordinary public HTML or text pages on Android Termux or a computer with Python. Optional Termux:API alerts report changes and repeated failures; old snapshots are automatically removed after the retention period.

## What it does

- Checks one HTTP or HTTPS page at a chosen interval.
- Reads a selected HTML element, or tries `main`, `article`, then `body` automatically.
- Saves a first-run baseline quietly, then writes a new `.md` snapshot when text changes.
- Remembers the last text hash across restarts.
- Removes old Markdown snapshots after a configurable number of days.
- Can send Termux notifications for a detected change, the first error in an error streak, and a final stop after too many errors.
- Uses bounded retries with increasing waits instead of endlessly repeating failures.
- Optionally uses curl DNS-over-HTTPS when the device's normal DNS cannot resolve a website.

## Limits

This is a text monitor, not a full browser. It works best with publicly accessible pages whose text is in the initial HTML response. JavaScript-only content, login-required pages, and interactive bot challenges may not work. It does not bypass access controls. A change that appears and disappears between checks can be missed. Follow the site’s terms and choose a considerate polling interval.

## Quick start

1. Install Python 3. For Android, follow [Android and Termux setup](docs/ANDROID_TERMUX.md).
2. Copy `settings.example.json` to `settings.json`.
3. Edit `settings.json` and enter your page address. The sample output folder is set for Termux; on other systems, change `output_dir` to a folder on that device (for example, `~/WebsiteBackups`).
4. Run `python website_monitor.py`.
5. The first successful check saves a baseline. Later changes create timestamped Markdown snapshots.

Read [Configuration](docs/CONFIGURATION.md) for settings, [Troubleshooting](docs/TROUBLESHOOTING.md) for common problems, and the [GitHub beginner guide](docs/GITHUB_BEGINNER_GUIDE.md) to publish the project.

## Configuration example

Your own `settings.json` is ignored by Git. It can contain your private page URL and supported request headers, so do not upload it. The repository contains only this safe example:

~~~json
{
  "target_url": "https://example.com/",
  "target_name": "example-site",
  "content_selector": "",
  "check_interval_seconds": 4,
  "retention_days": 3,
  "max_consecutive_errors": 5,
  "output_dir": "~/storage/downloads/WebsiteBackups",
  "doh_url": ""
}
~~~

A blank selector tries `main`, then `article`, then `body`. Simple selectors such as `#content`, `.post`, or `textarea` can target a specific element. Details are in [Configuration](docs/CONFIGURATION.md).

## Repository contents

- `website_monitor.py` — the monitoring program.
- `settings.example.json` — safe starter configuration.
- `docs/` — setup, configuration, troubleshooting, and GitHub guides.
- `SECURITY.md` and `CONTRIBUTING.md` — project and contribution guidance.
- `LICENSE` — the MIT open-source license.
- `LICENSE_INFO.txt` — plain-language summary of reuse terms.

## License

This project is released under the MIT License. Anyone may use, copy, modify, redistribute, sublicense, or sell the code, including for commercial purposes, as long as copies retain the copyright and license notices. The license includes a no-warranty disclaimer. See [LICENSE](LICENSE) for the full terms and [LICENSE_INFO.txt](LICENSE_INFO.txt) for a short summary. GitHub should identify the repository as MIT-licensed after upload.

## Rentry: original project and how to use it

This project was first created to watch a Rentry page after an edit and preserve the previous text. It has since been shaped for general websites; Rentry remains one supported use case.

For a publicly readable Rentry edit page, set `target_url` in your private `settings.json` to your own edit URL, such as `https://rentry.co/your-page/edit`. If the text is inside a text area, set `content_selector` to `textarea`. Confirm the page can be read without signing in before relying on monitoring.

If the URL needs to be claimed, follow Rentry's current claim process while signed in as appropriate; its claim form is for taken/squatted URLs. Add `SECRET_EMAIL_ADDRESS` in the page metadata if you want Rentry support to have an email for manually resetting the edit code. That email is for recovery; it is not a raw access code and does not automatically issue one. For automated raw access, the current API endpoint uses `https://rentry.co/api/raw/your-page`. Rentry documents `SECRET_RAW_ACCESS_CODE` as a separate passcode and currently says to request it from Rentry support. Claiming a URL, setting a recovery email, and obtaining raw access are separate steps.

For raw access, add the issued code only to the local ignored `settings.json`, like this:

~~~json
{
  "target_url": "https://rentry.co/api/raw/your-page",
  "content_selector": "",
  "headers": {
    "rentry-auth": "YOUR_ISSUED_RAW_ACCESS_CODE"
  }
}
~~~

Keep the other settings from `settings.example.json` too. The monitor reads Rentry's JSON API response and saves its page text into the `.md` snapshot. Never publish the real code or secret email.

A public edit page may work without a raw access code; requirements depend on the page and endpoint. This tool does not create Rentry access codes or grant access to pages you do not own or have permission to monitor. See [Rentry metadata instructions](https://rentry.co/metadata-how), [Rentry overview](https://rentry.co/what), and [Rentry URL claim requests](https://rentry.co/request-url) for current details, including the [Rentry official command-line/API guide](https://github.com/radude/rentry).