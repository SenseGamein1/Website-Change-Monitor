# Troubleshooting

## “Missing settings.json”

From the project folder run `cp settings.example.json settings.json`, then edit it with `nano settings.json`. It must sit next to `website_monitor.py`.

## DNS or “could not resolve host”

First see whether the page opens in your phone or computer browser. If the browser works but Termux cannot resolve the address, check Android Private DNS/network DNS. If you confirmed curl's DNS-over-HTTPS option works, install curl and set `doh_url` in your private `settings.json` to that endpoint. Cloudflare's endpoint is `https://one.one.one.one/dns-query`. Restart the script after editing. If it still fails, the site or network may be unreachable from Termux.

## HTTP status errors

Check that the URL is correct and publicly reachable from the same device. HTTP 404 often means the URL path is wrong. HTTP 403 may mean the site requires permission, an officially supported request header, or blocks automated traffic. Do not bypass login, anti-bot pages, or access controls. Use an official API or ask the site owner for an authorized method.

## Browser-check or anti-bot challenge

The monitor refuses to save a challenge page as if it were real content. It is not a full browser and does not bypass Cloudflare or other site protections. Use an official API/feed or another authorized access method.

## Selector not found

The selector may not match the HTML returned by the server. Try `main`, `article`, `#content`, or `.post`, or clear `content_selector` to use automatic selection. A desktop browser's **View page source** can show whether content is present before JavaScript executes. Only a simple tag, ID, class, tag-plus-ID/class, or comma-separated list is supported.

## Selected content empty

The selected element may be empty, the content may require JavaScript, or the site may require sign-in. Check that the page is available without signing in and choose the element containing its text. The monitor does not run JavaScript.

## No Android notification

Run the manual `termux-notification` test in the Android guide. Confirm the Termux:API app is installed, notification permission is enabled for that app, and both Termux and Termux:API came from the same source. Missing notifications do not stop the monitor; messages still appear in the Termux session.

## It stopped after consecutive errors

Read the last error in Termux, fix the URL, selector, DNS, permission, or network issue, then restart `python website_monitor.py`. The script sends one alert at the start of an error streak, backs off, and stops at the configured limit rather than retrying forever.

## Backups are missing

Check `output_dir` in `settings.json`. On Termux, run `termux-setup-storage` and allow access. The first successful check creates a baseline; later files are saved only when the selected text changes. Old `.md` files are removed after `retention_days`.

## Duplicates or many notifications

Make sure only one monitor process is running for that target. Stop extra sessions with Ctrl+C. This program is designed to run as one process per target.

## The app was stopped with the screen off

Some Android releases and phone brands aggressively stop background programs. Set Termux battery use to Unrestricted/Don't optimize and review manufacturer-specific background settings. These improve the chance of continued operation but cannot guarantee it.