# Android setup with Termux

This is a beginner walkthrough. Enter commands at the Termux prompt and press Enter. This project has no automatic reboot start; you start the monitor yourself.

## 1. Install Termux and Termux:API

Install Termux and the separate Termux:API Android app from the same source. Do not mix F-Droid and GitHub builds because add-ons signed by another source may not connect. Termux:API provides Android notifications.

- [Termux installation guidance](https://github.com/termux/termux-app#installation)
- [Termux:API project](https://github.com/termux/termux-api)

Allow notification permission for **Termux:API** in Android settings. Termux's own session/service notice is separate from edit/error notifications sent by `termux-notification`.

## 2. Install packages and storage access

Open Termux and enter:

~~~sh
pkg update -y && pkg upgrade -y
pkg install python git curl termux-api -y
termux-setup-storage
~~~

Tap **Allow** when Android asks Termux to access files. Backups go to **Downloads/WebsiteBackups** by default.

## 3. Download the project from GitHub

After you publish the project, replace `YOUR-USERNAME` with your GitHub username. If your repository has a different name, change `website-change-monitor` too.

~~~sh
git clone https://github.com/YOUR-USERNAME/website-change-monitor.git
cd website-change-monitor
cp settings.example.json settings.json
~~~

If you have not uploaded the project yet, copy its files onto the phone and `cd` into that folder instead.

## 4. Edit settings in nano

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

## 5. Run it

~~~sh
python website_monitor.py
~~~

The first successful check saves a baseline silently. A later change saves another `.md` file and sends a notification. It alerts once when a consecutive error streak begins, waits longer between retries, then stops after the configured limit. It deletes snapshots older than `retention_days`.

Find snapshots in your file manager under **Downloads/WebsiteBackups**. Stop the program with **Ctrl+C** in Termux.

## 6. Background and battery settings

You can switch to another app or press Home while Termux runs. Do not force-stop Termux or swipe away its active session. Android and device manufacturers may still stop background processes, so uninterrupted operation is not guaranteed.

To reduce interruptions, open Android **Settings → Apps → Termux → Battery** and choose **Unrestricted** or **Don't optimize**, if available. Check manufacturer-specific background or auto-cleanup controls too. The [Termux project notes](https://github.com/termux/termux-app#termux-app) warn that Android may kill processes despite battery settings.

Optional: run `termux-wake-lock` in a second Termux session if you want to keep the CPU awake. It can drain battery and may show a persistent Termux notice; it does not guarantee immunity from Android process limits. Run `termux-wake-unlock` when finished.

This repository intentionally has no boot auto-start. After restarting the phone, open Termux and run `cd ~/website-change-monitor` and then `python website_monitor.py`.

## 7. Test Android notifications

With the Termux:API Android app installed and allowed to notify, run:

~~~sh
termux-notification --title "Monitor test" --content "Android alerts are working"
~~~

If the command is missing, install the `termux-api` package inside Termux. If it runs but no alert appears, check notification permission for the separate Termux:API app and make sure both apps came from the same source.

## Optional troubleshooting with Codex and ADB over USB

If you use Codex on a computer and want help diagnosing a phone issue, you can connect the Android phone with a USB cable and use Android Debug Bridge (ADB), if ADB is installed and available to Codex's computer environment. On the phone, enable Developer options and USB debugging, unlock it, connect the cable, and approve the computer's fingerprint prompt. On the computer, `adb devices` should list the authorized phone. You can then ask Codex to inspect relevant Termux output or help with read-only diagnostics.

USB debugging gives the connected computer powerful access. Use a computer you trust, review commands before approving them, do not expose `settings.json` or access codes in logs, and turn off USB debugging or revoke the computer authorization when finished. A USB cable alone does not automatically give Codex access; the computer needs ADB and a permitted way for Codex to use it.

## iPhone note

This Termux setup is for Android; Termux is not the iPhone app for this project. iOS allows only specific kinds of scheduled or continuing background work, so a general script that polls every few seconds should not be expected to run continuously after leaving its app. Apple's documentation describes those background modes as limited and system-managed: [background execution modes](https://developer.apple.com/documentation/Xcode/configuring-background-execution-modes) and [long-running tasks](https://developer.apple.com/documentation/BackgroundTasks/performing-long-running-tasks-on-ios-and-ipados). For an iPhone, the practical option is to run the monitor on an always-on computer or server and view its snapshots or alerts on the phone.