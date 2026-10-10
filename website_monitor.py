#!/usr/bin/env python3
"""Save Markdown snapshots when selected text on a website changes."""
from __future__ import annotations
import hashlib, json, os, re, shutil, subprocess, sys, tempfile, time
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "settings.json"
DEFAULTS = {
    "target_url": "https://example.com/", "target_name": "website", "content_selector": "",
    "check_interval_seconds": 4, "retention_days": 3, "max_consecutive_errors": 5,
    "error_backoff_seconds": [4, 8, 16, 32],
    "output_dir": "~/storage/downloads/WebsiteBackups", "doh_url": "",
    "headers": {}, "android_notifications": True,
}
MAX_RESPONSE_BYTES = 10 * 1024 * 1024
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
IGNORED_TAGS = {"script", "style", "noscript", "svg", "nav", "header", "footer", "aside"}
BLOCK_TAGS = {"address", "article", "blockquote", "dd", "div", "dl", "dt", "fieldset", "figcaption", "figure", "form", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "li", "main", "ol", "p", "pre", "section", "table", "tbody", "td", "th", "thead", "tr", "ul"}
CHALLENGE_MARKERS = ("just a moment", "verify you are human", "attention required", "cf-chl-", "cloudflare ray id", "captcha-challenge")
_notification_warning_shown = False

class MonitorError(Exception):
    """Expected setup, network, or page-reading problem."""

class Node:
    def __init__(self, tag="", attrs=None):
        self.tag, self.attrs, self.children = tag, attrs or {}, []

class PageTreeParser(HTMLParser):
    """Build a small DOM using Python's built-in HTML parser."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root, self.stack = Node("document"), []
        self.stack.append(self.root)
    def handle_starttag(self, tag, attrs):
        node = Node(tag.lower(), dict(attrs))
        self.stack[-1].children.append(node)
        if node.tag not in VOID_TAGS:
            self.stack.append(node)
    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(Node(tag.lower(), dict(attrs)))
    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag.lower():
                del self.stack[index:]
                return
    def handle_data(self, data):
        if data:
            self.stack[-1].children.append(data)

def safe_label(value):
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip()).strip("._-")
    return (value or "website")[:60]

def load_config():
    if not CONFIG_PATH.is_file():
        raise MonitorError("Missing settings.json. Copy settings.example.json to settings.json, edit the target URL, and try again.")
    try:
        with CONFIG_PATH.open(encoding="utf-8-sig") as handle:
            supplied = json.load(handle)
    except (OSError, json.JSONDecodeError) as error:
        raise MonitorError(f"Could not read settings.json: {error}") from error
    if not isinstance(supplied, dict):
        raise MonitorError("settings.json must contain a JSON object.")
    config = {**DEFAULTS, **supplied}
    url = config.get("target_url")
    parts = urlsplit(url) if isinstance(url, str) else None
    if not parts or parts.scheme not in {"http", "https"} or not parts.netloc:
        raise MonitorError("Set target_url to a complete URL beginning with http:// or https://.")
    if not isinstance(config["headers"], dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in config["headers"].items()):
        raise MonitorError("headers must be an object containing text header names and values.")
    try:
        for name in ("check_interval_seconds", "retention_days", "max_consecutive_errors"):
            config[name] = max(1, int(config[name]))
        delays = config["error_backoff_seconds"]
        if not isinstance(delays, list) or not delays:
            raise ValueError("error_backoff_seconds must be a non-empty list")
        config["error_backoff_seconds"] = [max(1, int(item)) for item in delays]
    except (TypeError, ValueError, KeyError) as error:
        raise MonitorError(f"A timing/error setting is invalid: {error}") from error
    config["target_name"] = safe_label(str(config.get("target_name") or "website"))
    config["content_selector"] = str(config.get("content_selector") or "").strip()
    config["doh_url"] = str(config.get("doh_url") or "").strip()
    config["output_dir"] = Path(os.path.expandvars(str(config["output_dir"]))).expanduser()
    return config

def add_cache_buster(url):
    parts = urlsplit(url)
    query = [(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True) if key != "_monitor"]
    query.append(("_monitor", str(int(time.time()))))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))

def decode_body(body, content_type, charset="utf-8"):
    match = re.search(r"charset=([A-Za-z0-9._-]+)", content_type, re.I)
    if match:
        charset = match.group(1)
    try:
        return body.decode(charset, errors="replace")
    except LookupError:
        return body.decode("utf-8", errors="replace")

def fetch_page(config):
    url = add_cache_buster(config["target_url"])
    headers = {"User-Agent": "WebsiteChangeMonitor/1.0", "Cache-Control": "no-cache", **config["headers"]}
    if config["doh_url"]:
        curl = shutil.which("curl")
        if not curl:
            raise MonitorError("doh_url is set but curl is not installed. Install curl or clear doh_url.")
        command = [curl, "--silent", "--show-error", "--location", "--connect-timeout", "15", "--max-time", "30", "--max-filesize", str(MAX_RESPONSE_BYTES), "--ipv4", "--doh-url", config["doh_url"], "--user-agent", headers.pop("User-Agent")]
        for name, value in headers.items():
            command.extend(["--header", f"{name}: {value}"])
        command.extend(["--write-out", "\n__WEBSITE_MONITOR_META__:%{http_code}|%{content_type}", url])
        try:
            result = subprocess.run(command, capture_output=True, timeout=40, check=False)
        except subprocess.TimeoutExpired as error:
            raise MonitorError("curl timed out while connecting to the page.") from error
        except OSError as error:
            raise MonitorError(f"Could not start curl: {error}") from error
        marker = b"\n__WEBSITE_MONITOR_META__:"
        if marker not in result.stdout:
            detail = result.stderr.decode("utf-8", errors="replace").strip()
            raise MonitorError("curl did not return an HTTP status" + (f": {detail}" if detail else "."))
        body, meta = result.stdout.rsplit(marker, 1)
        status_text, separator, content_type_bytes = meta.partition(b"|")
        if not separator:
            raise MonitorError("Could not read the HTTP status returned by curl.")
        try:
            status = int(status_text.decode("ascii", errors="ignore").strip())
        except ValueError as error:
            raise MonitorError("curl returned an invalid HTTP status.") from error
        content_type = content_type_bytes.decode("utf-8", errors="replace").strip()
        if status < 200 or status >= 300:
            raise MonitorError(f"The website returned HTTP {status}.")
    else:
        request = Request(url, headers=headers)
        try:
            with urlopen(request, timeout=30) as response:
                status, content_type = response.status, response.headers.get("Content-Type", "")
                body = response.read(MAX_RESPONSE_BYTES + 1)
                charset = response.headers.get_content_charset() or "utf-8"
        except HTTPError as error:
            raise MonitorError(f"The website returned HTTP {error.code}.") from error
        except (URLError, TimeoutError, OSError) as error:
            raise MonitorError(f"Could not download the page: {error}") from error
        if status < 200 or status >= 300:
            raise MonitorError(f"The website returned HTTP {status}.")
        if len(body) > MAX_RESPONSE_BYTES:
            raise MonitorError("The response is larger than the 10 MiB safety limit.")
        return decode_body(body, content_type, charset), content_type
    if len(body) > MAX_RESPONSE_BYTES:
        raise MonitorError("The response is larger than the 10 MiB safety limit.")
    return decode_body(body, content_type), content_type

def hidden(node):
    attrs = node.attrs
    if "hidden" in attrs or str(attrs.get("aria-hidden", "")).lower() == "true":
        return True
    style = re.sub(r"\s+", "", str(attrs.get("style", "")).lower())
    return "display:none" in style or "visibility:hidden" in style

def node_text(node):
    if node.tag in IGNORED_TAGS or hidden(node):
        return ""
    pieces = []
    for child in node.children:
        if isinstance(child, str):
            pieces.append(child)
        elif child.tag == "br":
            pieces.append("\n")
        else:
            block = child.tag in BLOCK_TAGS
            if block:
                pieces.append("\n")
            pieces.append(node_text(child))
            if block:
                pieces.append("\n")
    return "".join(pieces)

def normalize(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    result = []
    for line in text.split("\n"):
        line = re.sub(r"[\t\f\v ]+", " ", line).strip()
        if line:
            result.append(line)
        elif result and result[-1] != "":
            result.append("")
    return "\n".join(result).strip()

def walk(node):
    for child in node.children:
        if isinstance(child, Node):
            yield child
            yield from walk(child)

def matches(node, selector):
    match = re.fullmatch(r"([A-Za-z][A-Za-z0-9_-]*)?(?:#([A-Za-z0-9_-]+))?(?:\.([A-Za-z0-9_-]+))?", selector.strip())
    if not match or not any(match.groups()):
        raise MonitorError(f"Unsupported selector {selector!r}. Use a tag, #id, .class, tag#id, or tag.class.")
    tag, element_id, class_name = match.groups()
    return ((not tag or node.tag == tag.lower())
            and (not element_id or node.attrs.get("id") == element_id)
            and (not class_name or class_name in str(node.attrs.get("class", "")).split()))

def extract_text(page, content_type, selector_setting):
    if "json" in content_type.lower():
        try:
            envelope = json.loads(page)
        except json.JSONDecodeError:
            envelope = None
        if isinstance(envelope, dict) and "status" in envelope and "content" in envelope:
            if str(envelope.get("status")) != "200":
                raise MonitorError(f"The API returned status {envelope.get('status')}: {str(envelope.get('content'))[:300]}")
            if not isinstance(envelope["content"], str):
                raise MonitorError("The API response content was not text.")
            page, content_type = envelope["content"], "text/plain"
    looks_html = "html" in content_type.lower() or re.search(r"<\s*[a-zA-Z][^>]*>", page[:1000]) is not None
    if not looks_html:
        if selector_setting:
            raise MonitorError("content_selector is set, but the response is not HTML. Clear the selector for plain text/JSON pages.")
        text = normalize(page)
    else:
        parser = PageTreeParser()
        try:
            parser.feed(page)
            parser.close()
        except Exception as error:
            raise MonitorError(f"Could not parse page HTML: {error}") from error
        selectors = [part.strip() for part in selector_setting.split(",") if part.strip()] if selector_setting else ["main", "article", "body"]
        target = None
        for selector in selectors:
            for node in walk(parser.root):
                if matches(node, selector):
                    target = node
                    break
            if target:
                break
        if not target:
            raise MonitorError("None of the configured selectors matched: " + ", ".join(selectors))
        text = normalize(node_text(target))
    if not text:
        raise MonitorError("The selected page content was empty; nothing was saved.")
    if any(marker in text.lower() for marker in CHALLENGE_MARKERS):
        raise MonitorError("The site returned a browser-check or anti-bot challenge, not page text.")
    return text

def state_file(target_url):
    key = hashlib.sha256(target_url.encode("utf-8")).hexdigest()[:20]
    folder = Path.home() / ".website-change-monitor"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"state-{key}.json"

def read_hash(path):
    try:
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
        value = data.get("sha256") if isinstance(data, dict) else None
        return value if isinstance(value, str) else None
    except (OSError, json.JSONDecodeError):
        return None

def write_state(path, digest, url):
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        temp = Path(handle.name)
        json.dump({"target_url": url, "sha256": digest, "updated_at": datetime.now().astimezone().isoformat()}, handle)
        handle.write("\n")
    os.replace(temp, path)

def save_snapshot(text, output_dir, label):
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S_%f")
    destination = output_dir / f"{label}_{stamp}.md"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=output_dir, suffix=".tmp", delete=False) as handle:
        temp = Path(handle.name)
        handle.write(text.rstrip() + "\n")
    os.replace(temp, destination)
    return destination

def cleanup(output_dir, retention_days):
    if not output_dir.exists():
        return 0
    cutoff = time.time() - retention_days * 86400
    removed = 0
    for path in output_dir.glob("*.md"):
        try:
            if path.is_file() and path.stat().st_mtime < cutoff:
                path.unlink()
                removed += 1
        except OSError as error:
            raise MonitorError(f"Could not delete expired snapshot {path.name}: {error}") from error
    return removed

def notify(config, title, message):
    global _notification_warning_shown
    if not config.get("android_notifications", True):
        return
    command = shutil.which("termux-notification")
    if not command:
        if not _notification_warning_shown:
            print("Android notifications unavailable; monitoring continues in the terminal.")
            _notification_warning_shown = True
        return
    try:
        result = subprocess.run([command, "--title", title, "--content", message[:900], "--priority", "high", "--group", "website-monitor"], capture_output=True, timeout=5, check=False)
        if result.returncode and not _notification_warning_shown:
            print("Notification failed; monitoring continues in the terminal.")
            _notification_warning_shown = True
    except (OSError, subprocess.TimeoutExpired):
        if not _notification_warning_shown:
            print("Notification command failed or timed out; monitoring continues in the terminal.")
            _notification_warning_shown = True

def monitor(config):
    url, output_dir = config["target_url"], config["output_dir"]
    state, previous = state_file(url), None
    previous = read_hash(state)
    errors, backoff = 0, config["error_backoff_seconds"]
    interval, max_errors = config["check_interval_seconds"], config["max_consecutive_errors"]
    print(f"Watching: {url}\nSaving snapshots in: {output_dir}")
    print(f"Checking every {interval} seconds. Press Ctrl+C to stop.")
    print(f"Stops after {max_errors} consecutive errors.\n")
    while True:
        started = time.monotonic()
        try:
            removed = cleanup(output_dir, config["retention_days"])
            if removed:
                print(f"Removed {removed} expired snapshot(s).")
            page, content_type = fetch_page(config)
            text = extract_text(page, content_type, config["content_selector"])
            digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
            if previous is None or digest != previous:
                file_path = save_snapshot(text, output_dir, config["target_name"])
                write_state(state, digest, url)
                initial = previous is None
                previous = digest
                now = datetime.now().astimezone()
                if initial:
                    print(f"[{now:%Y-%m-%d %H:%M:%S}] Initial baseline saved: {file_path.name}")
                else:
                    print(f"[{now:%Y-%m-%d %H:%M:%S}] Change saved: {file_path}")
                    pretty_time = now.strftime("%A, %d %B %Y at %I:%M:%S %p %Z")
                    notify(config, "Website edit detected", f"{config['target_name']} changed at {pretty_time}. Snapshot: {file_path.name}")
            else:
                print(f"[{datetime.now().astimezone():%H:%M:%S}] No change.")
            errors = 0
        except Exception as error:
            errors += 1
            detail = str(error).replace("\n", " ")[:700]
            print(f"[{datetime.now().astimezone():%H:%M:%S}] Error {errors}/{max_errors}: {detail}")
            if errors == 1:
                notify(config, "Website monitor error", f"Could not check {config['target_name']}: {detail}")
            if errors >= max_errors:
                print("Stopping after too many consecutive errors. Fix the problem and restart the script.")
                notify(config, "Website monitor stopped", f"Stopped after {max_errors} consecutive errors. Check Termux for details.")
                return 1
            delay = backoff[min(errors - 1, len(backoff) - 1)]
            print(f"Retrying in {delay} seconds.\n")
            time.sleep(delay)
            continue
        time.sleep(max(0, interval - (time.monotonic() - started)))

def main():
    try:
        return monitor(load_config())
    except MonitorError as error:
        print(f"Setup error: {error}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nStopped by user. Existing snapshots are kept.")
        return 0

if __name__ == "__main__":
    raise SystemExit(main())