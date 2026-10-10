# Website Change Monitor

A lightweight Python tool for checking a web page, extracting its readable text, and saving a timestamped Markdown snapshot whenever that text changes. Configure it for ordinary public HTML or text pages on Android Termux or a computer with Python. Optional Termux:API alerts report changes and repeated failures; old snapshots are automatically removed after the retention period.

> **Using Android?** Start with the [Android and Termux setup guide](docs/ANDROID_TERMUX.md). It walks through the phone setup, editing the settings with nano, notifications, and running the monitor.

## All Markdown files

GitHub displays this README.md on the repository front page. Use these links to open every Markdown guide and project note:

| File | What it covers |
| --- | --- |
| [Project overview](#website-change-monitor) | Summary and quick start |
| [Android and Termux setup](#android-setup-with-termux) | Full Android setup guide |
| [Configuration](#configuration-guide) | All settings and examples |
| [Troubleshooting](#troubleshooting) | Common problems and fixes |
| [GitHub beginner guide](#github-beginner-guide-publish-this-project-neatly) | Publish and maintain this repository |
| [Changelog](#changelog) | Project changes |
| [Contributing](#contributing) | How to suggest improvements |
| [Security and privacy](#security-and-privacy) | Protect private information |

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

## Complete project documentation

The sections below contain the full text of every other Markdown document in this repository. You can read the setup, reference guides, project policies, and changelog here without opening another file. Standalone copies remain in the repository as well.
### Android setup with Termux

This is a beginner walkthrough. Enter commands at the Termux prompt and press Enter. This project has no automatic reboot start; you start the monitor yourself.

#### 1. Install Termux and Termux:API

Install Termux and the separate Termux:API Android app from the same source. Do not mix F-Droid and GitHub builds because add-ons signed by another source may not connect. Termux:API provides Android notifications.

- [Termux installation guidance](https://github.com/termux/termux-app#installation)
- [Termux:API project](https://github.com/termux/termux-api)

Allow notification permission for **Termux:API** in Android settings. Termux's own session/service notice is separate from edit/error notifications sent by `termux-notification`.

#### 2. Install packages and storage access

Open Termux and enter:

~~~sh
pkg update -y && pkg upgrade -y
pkg install python git curl termux-api -y
termux-setup-storage
~~~

Tap **Allow** when Android asks Termux to access files. Backups go to **Downloads/WebsiteBackups** by default.

#### 3. Download the project from GitHub

After you publish the project, replace `YOUR-USERNAME` with your GitHub username. If your repository has a different name, change `website-change-monitor` too.

~~~sh
git clone https://github.com/YOUR-USERNAME/website-change-monitor.git
cd website-change-monitor
cp settings.example.json settings.json
~~~

If you have not uploaded the project yet, copy its files onto the phone and `cd` into that folder instead.

#### 4. Edit settings in nano

Open the local settings file:

~~~sh
nano settings.json
~~~

Change `target_url` to the complete URL you want to monitor. Give `target_name` a short label. Leave `content_selector` blank for an ordinary page; if the content is inside one known element, use a selector such as `main`, `#content`, `.post`, or `textarea`. Change `check_interval_seconds` and `output_dir` if desired. Set `doh_url` only if you need and have tested DNS-over-HTTPS.

Keep the double quotes and commas valid. JSON needs commas between entries but no comma after the final entry. Never share `settings.json` if it contains a private URL or access header.

To save and exit nano:

1. Press **Ctrl+O**. Termux's extra-keys row has Ctrl; on many phones, Volume Down + O also sends Ctrl+O.
2. Press **Enter** to confirm the filename.
3. Press **Ctrl+X** to exit.

#### 5. Run it

~~~sh
python website_monitor.py
~~~

The first successful check saves a baseline silently. A later change saves another `.md` file and sends a notification. It alerts once when a consecutive error streak begins, waits longer between retries, then stops after the configured limit. It deletes snapshots older than `retention_days`.

Find snapshots in your file manager under **Downloads/WebsiteBackups**. Stop the program with **Ctrl+C** in Termux.

#### 6. Background and battery settings

You can switch to another app or press Home while Termux runs. Do not force-stop Termux or swipe away its active session. Android and device manufacturers may still stop background processes, so uninterrupted operation is not guaranteed.

To reduce interruptions, open Android **Settings → Apps → Termux → Battery** and choose **Unrestricted** or **Don't optimize**, if available. Check manufacturer-specific background or auto-cleanup controls too. The [Termux project notes](https://github.com/termux/termux-app#termux-app) warn that Android may kill processes despite battery settings.

Optional: run `termux-wake-lock` in a second Termux session if you want to keep the CPU awake. It can drain battery and may show a persistent Termux notice; it does not guarantee immunity from Android process limits. Run `termux-wake-unlock` when finished.

This repository intentionally has no boot auto-start. After restarting the phone, open Termux and run `cd ~/website-change-monitor` and then `python website_monitor.py`.

#### 7. Test Android notifications

With the Termux:API Android app installed and allowed to notify, run:

~~~sh
termux-notification --title "Monitor test" --content "Android alerts are working"
~~~

If the command is missing, install the `termux-api` package inside Termux. If it runs but no alert appears, check notification permission for the separate Termux:API app and make sure both apps came from the same source.

#### Optional troubleshooting with Codex and ADB over USB

If you use Codex on a computer and want help diagnosing a phone issue, you can connect the Android phone with a USB cable and use Android Debug Bridge (ADB), if ADB is installed and available to Codex's computer environment. On the phone, enable Developer options and USB debugging, unlock it, connect the cable, and approve the computer's fingerprint prompt. On the computer, `adb devices` should list the authorized phone. You can then ask Codex to inspect relevant Termux output or help with read-only diagnostics.

USB debugging gives the connected computer powerful access. Use a computer you trust, review commands before approving them, do not expose `settings.json` or access codes in logs, and turn off USB debugging or revoke the computer authorization when finished. A USB cable alone does not automatically give Codex access; the computer needs ADB and a permitted way for Codex to use it.

#### iPhone note

This Termux setup is for Android; Termux is not the iPhone app for this project. iOS allows only specific kinds of scheduled or continuing background work, so a general script that polls every few seconds should not be expected to run continuously after leaving its app. Apple's documentation describes those background modes as limited and system-managed: [background execution modes](https://developer.apple.com/documentation/Xcode/configuring-background-execution-modes) and [long-running tasks](https://developer.apple.com/documentation/BackgroundTasks/performing-long-running-tasks-on-ios-and-ipados). For an iPhone, the practical option is to run the monitor on an always-on computer or server and view its snapshots or alerts on the phone.

---

### Configuration guide

The program reads `settings.json` from the same folder as `website_monitor.py`. Copy `settings.example.json` to `settings.json`, then edit that local file. Git ignores `settings.json` because it may contain private URLs or request headers.

#### Settings

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

#### Selecting page text

The default automatic choice is the first available `main`, `article`, or `body` element. You can specify one simple selector:

- `main` or `article` selects a tag.
- `#content` selects an element with `id="content"`.
- `.post-body` selects an element with that class.
- `div#content` or `section.post-body` combines a tag with an ID or class.
- `main,article` tries selectors in order.

Complex CSS selectors (descendant selectors, attributes, or pseudo-classes) are not supported. Common navigation, header/footer, script, and hidden elements are skipped. Whitespace is normalized so cosmetic spacing changes usually do not trigger a snapshot. If a server returns plain text or JSON, leave the selector blank.

#### DNS-over-HTTPS

Normally leave `doh_url` blank. If the phone's regular DNS cannot find a host but curl succeeds using DNS-over-HTTPS, install curl and set `doh_url` to that working endpoint. For example: `https://one.one.one.one/dns-query`. A set `doh_url` makes the script use curl and IPv4. If curl is missing or the DoH service is unavailable, monitoring reports an error and follows the configured retry limit.

#### Access headers and privacy

If a website officially supports a request header, add it to `headers` in your local `settings.json`. For example, the shape is `"headers": {"Header-Name": "private-value"}`. Do not put real access codes, passwords, cookies, API keys, or private page URLs in the script or in files you upload to GitHub. Do not use this monitor to evade site protections or access pages without permission.

#### Baselines, changes, and retention

The first successful check stores the current text as a baseline and sends no edit alert. Later it compares a SHA-256 hash; changed text is saved as a timestamped `.md` snapshot. The hash state is stored under `~/.website-change-monitor/` and is separate from the repository. On each check it permanently deletes `.md` files in the output folder whose modification time is older than `retention_days`.

#### Polling load

The sample uses 4 seconds to match the original quick-check use case. That can make up to 900 requests per hour. Increase the interval for normal use, follow the website's rules, and avoid aggressive polling. No polling interval can guarantee that a short-lived edit is captured.

---

### Troubleshooting

#### “Missing settings.json”

From the project folder run `cp settings.example.json settings.json`, then edit it with `nano settings.json`. It must sit next to `website_monitor.py`.

#### DNS or “could not resolve host”

First see whether the page opens in your phone or computer browser. If the browser works but Termux cannot resolve the address, check Android Private DNS/network DNS. If you confirmed curl's DNS-over-HTTPS option works, install curl and set `doh_url` in your private `settings.json` to that endpoint. Cloudflare's endpoint is `https://one.one.one.one/dns-query`. Restart the script after editing. If it still fails, the site or network may be unreachable from Termux.

#### HTTP status errors

Check that the URL is correct and publicly reachable from the same device. HTTP 404 often means the URL path is wrong. HTTP 403 may mean the site requires permission, an officially supported request header, or blocks automated traffic. Do not bypass login, anti-bot pages, or access controls. Use an official API or ask the site owner for an authorized method.

#### Browser-check or anti-bot challenge

The monitor refuses to save a challenge page as if it were real content. It is not a full browser and does not bypass Cloudflare or other site protections. Use an official API/feed or another authorized access method.

#### Selector not found

The selector may not match the HTML returned by the server. Try `main`, `article`, `#content`, or `.post`, or clear `content_selector` to use automatic selection. A desktop browser's **View page source** can show whether content is present before JavaScript executes. Only a simple tag, ID, class, tag-plus-ID/class, or comma-separated list is supported.

#### Selected content empty

The selected element may be empty, the content may require JavaScript, or the site may require sign-in. Check that the page is available without signing in and choose the element containing its text. The monitor does not run JavaScript.

#### No Android notification

Run the manual `termux-notification` test in the Android guide. Confirm the Termux:API app is installed, notification permission is enabled for that app, and both Termux and Termux:API came from the same source. Missing notifications do not stop the monitor; messages still appear in the Termux session.

#### It stopped after consecutive errors

Read the last error in Termux, fix the URL, selector, DNS, permission, or network issue, then restart `python website_monitor.py`. The script sends one alert at the start of an error streak, backs off, and stops at the configured limit rather than retrying forever.

#### Backups are missing

Check `output_dir` in `settings.json`. On Termux, run `termux-setup-storage` and allow access. The first successful check creates a baseline; later files are saved only when the selected text changes. Old `.md` files are removed after `retention_days`.

#### Duplicates or many notifications

Make sure only one monitor process is running for that target. Stop extra sessions with Ctrl+C. This program is designed to run as one process per target.

#### The app was stopped with the screen off

Some Android releases and phone brands aggressively stop background programs. Set Termux battery use to Unrestricted/Don't optimize and review manufacturer-specific background settings. These improve the chance of continued operation but cannot guarantee it.

---

### GitHub beginner guide: publish this project neatly

This walkthrough uses GitHub in a web browser. You do not need Git commands on your computer to publish the files. Anyone can view and copy a public repository, so check for private information first.

#### Before starting

1. Sign in at [github.com](https://github.com/).
2. Unzip the downloaded project archive if you downloaded the ZIP. Open the `website-change-monitor` folder.
3. Upload `settings.example.json`, but never upload your personal `settings.json`, saved backups, access codes, cookies, or private URLs.
4. Read `LICENSE` and `LICENSE_INFO.txt`. The project uses the MIT License, which allows anyone to use, modify, and redistribute the code if they retain the license notice.

#### 1. Create a new, empty repository

1. Select the **+** button at the upper right of GitHub and choose **New repository**, or go to [github.com/new](https://github.com/new).
2. Set **Repository name** to `website-change-monitor`.
3. For the description, use the text in `GITHUB_DESCRIPTION.txt`.
4. Choose **Public** so anyone can view and use the open-source project under its MIT terms. A Private repository would limit who can see it.
5. Do not check **Add a README file**, **Add .gitignore**, or **Choose a license**. The project already includes `README.md`, `.gitignore`, and its MIT `LICENSE` file, which you will upload.
6. Select **Create repository**.

#### 2. Upload the files in your browser

1. On the new repository page, select **Add file → Upload files**.
2. Open the local `website-change-monitor` folder. Select all files and folders *inside* it, then drag them to the upload area. This should put `README.md` at the top level of the repository instead of inside an extra nested folder.
3. Include `.gitignore`, `.gitattributes`, and `.editorconfig` if the uploader accepts hidden items. The `.github` folder contains optional issue forms only; if GitHub says it is hidden or refuses it, remove/skip that folder and continue with the other files.
4. Check the upload list. It should include `settings.example.json`, but not `settings.json`, backups, or private data.
5. In **Commit changes**, enter `Add website change monitor project files` as the commit message.
6. Select **Commit changes** to save the files.

GitHub's browser upload currently allows up to 100 files at once and 25 MiB per file. This project is within those limits. If the browser refuses any hidden file, finish uploading the ordinary files first. Hidden files are easy to add afterward using **Add file → Create new file**; type the full path, such as `.gitignore` or `.github/ISSUE_TEMPLATE/bug_report.yml`, into the filename box, paste the contents from the matching local file, and commit. The `.github` issue forms are optional and do not affect the monitor. The `.gitignore` is useful for keeping local settings and backups out of future uploads, so add it if it was skipped.

#### 3. Check that it looks right

After the upload, return to the repository's **Code** tab. Confirm that the README appears below the file list and `docs` is present. If the uploader rejected hidden items, add `.gitignore` and optionally `.github/ISSUE_TEMPLATE` later using the instructions above. Also check:

- `.gitignore` is present.
- `settings.example.json` is present.
- `settings.json` is absent.
- No backup `.md` files, personal email, private URL, or access code is present.

If you accidentally publish a password or access code, treat it as exposed and revoke/change it with the service. Deleting a file in a later commit does not remove the old value from Git history.

#### 4. Set the About box and topics

On the repository page, use the edit/gear control in the **About** area. Set the description to the contents of `GITHUB_DESCRIPTION.txt`. Add a few relevant topics from `GITHUB_TOPICS.txt`, such as `python`, `website-monitor`, `termux`, `android`, and `change-detection`. Leave Website blank unless you have a project page. Topics help others find the code; don't add tags for features the project does not provide.

A social preview image is optional. If you make one later, do not include any monitored private URL, page text, or credentials.

#### 5. Confirm the MIT license

The project already includes an MIT `LICENSE`. This permissive open-source license lets anyone use, copy, modify, distribute, sublicense, or sell the code, including commercially, provided the copyright and license notices stay with copies or substantial portions. It also provides the warranty disclaimer written in the license. Do not select an extra license during repository creation. Read the full [LICENSE](LICENSE) before publishing. The copyright line currently names the project contributors; you may personalize it with your name or GitHub username if you prefer.

#### 6. Keep the repository in good shape

- Make small updates with descriptive commit messages, for example `Explain custom page selectors`.
- Keep local settings, secrets, state, and backups out of GitHub.
- Use the **Issues** tab for bug reports and ideas. Included forms remind people not to post credentials.
- Update `CHANGELOG.md` when users will notice a change.
- Review every upload or change before committing it.
- Explain limitations honestly; Android battery controls and network behavior vary by device.

#### Official GitHub references

- [Create a repository](https://docs.github.com/en/get-started/start-your-journey/creating-a-repository-for-your-project-on-github)
- [Upload files to a repository](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository)
- [Choose a repository license](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)

---

### Changelog

Notable user-facing changes are recorded here.

#### Unreleased

- Generalized the original Rentry monitor for configurable public web pages.
- Added local JSON settings, simple content selectors, optional headers and curl DNS-over-HTTPS, persistent change state, retention cleanup, bounded retries, and optional Termux notifications.
- Added Android/Termux, configuration, troubleshooting, GitHub, ADB, and iPhone guidance.
- Released the project under the MIT License.

---

### Contributing

Suggestions and bug reports are welcome. For a large change, open an issue first to discuss the approach.

#### Before proposing a change

- Check existing issues for duplicates.
- Describe the affected page type or use case.
- Remove private URLs, credentials, cookies, and page contents from examples and screenshots.
- Keep the project dependency-light and compatible with standard Python where possible.
- Do not add code that bypasses authentication, paywalls, bot protection, or site access rules.

#### Pull requests

- Keep changes focused and explain what and why.
- Update relevant documentation when behavior or settings change.
- Do not include local `settings.json`, state files, or backup `.md` files.
- Describe expected behavior and known limitations.

The project owner should review code and dependency changes before merging. See `LICENSE` for reuse terms.

---

### Security and privacy

#### Protect local settings

`settings.json` may contain private page URLs or request headers and is excluded by `.gitignore`. Do not upload it. Keep access codes, cookies, passwords, and API keys off GitHub, issue reports, screenshots, and commit messages.

If a credential is exposed, revoke or rotate it with the service that issued it. Deleting a file in a later commit does not remove the secret from Git history.

#### Respect access rules

Monitor only pages you own or are authorized to access. This program makes ordinary HTTP requests; it does not bypass logins, challenges, rate limits, or access controls. Respect the website's terms and choose an appropriate polling interval.

#### Report a security concern

Do not post credentials or private page content in a public issue. Contact the repository owner privately if you believe you found a vulnerability. This project does not currently promise a response time or private advisory process.
