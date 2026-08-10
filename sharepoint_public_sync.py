#!/usr/bin/env python3
"""Download or mirror a publicly shared SharePoint folder without login."""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, unquote, urlparse
from urllib.request import HTTPCookieProcessor, Request, build_opener

STATE_FILE_NAME = ".sharepoint-sync-state.json"
USER_AGENT = "sharepoint-public-sync/1.0"
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def load_env(path: Path) -> dict[str, str]:
    """Read a small dependency-free KEY=VALUE .env file."""
    if not path.is_file():
        raise RuntimeError(f"Configuration file not found: {path}")
    values: dict[str, str] = {}
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            raise RuntimeError(f"Invalid .env entry at {path}:{number}; expected KEY=VALUE")
        key, value = (part.strip() for part in line.split("=", 1))
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            raise RuntimeError(f"Invalid variable name at {path}:{number}")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key] = value
    return values


def bool_value(value: str, name: str) -> bool:
    if value.lower() in {"1", "true", "yes", "on"}:
        return True
    if value.lower() in {"0", "false", "no", "off"}:
        return False
    raise RuntimeError(f"{name} must be true or false")


class SharePointClient:
    def __init__(self, timeout: int):
        self.timeout = timeout
        self.opener = build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def open(self, url: str, accept: str = "application/json, text/html;q=0.9, */*;q=0.8"):
        request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
        for attempt in range(4):
            try:
                return self.opener.open(request, timeout=self.timeout)
            except HTTPError as error:
                if error.code not in RETRYABLE_STATUS_CODES or attempt == 3:
                    raise
            except URLError:
                if attempt == 3:
                    raise
            delay = 2**attempt
            print(f"Temporary SharePoint error; retrying in {delay}s...", file=sys.stderr)
            time.sleep(delay)
        raise AssertionError("unreachable")

    def get_json(self, url: str) -> dict[str, Any]:
        with self.open(url) as response:
            return json.loads(response.read())

    def public_folder_metadata(self, share_url: str) -> tuple[str, str, str]:
        with self.open(share_url, "text/html, */*;q=0.8") as response:
            page = response.read().decode("utf-8", errors="replace")
            final_url = response.geturl()

        def page_field(name: str) -> str:
            found = re.search(r'"' + re.escape(name) + r'":"([^"]+)"', page)
            if not found:
                raise RuntimeError(f"SharePoint did not supply {name}; check that this is an active public folder link")
            return found.group(1).replace(r"\u002f", "/")

        item_path = unquote(parse_qs(urlparse(final_url).query).get("id", [""])[0])
        library_path = page_field("listUrl")
        if not item_path.startswith(library_path + "/"):
            raise RuntimeError("This does not appear to be a public SharePoint folder link")
        return page_field(".driveUrl"), page_field(".driveAccessToken"), item_path[len(library_path) + 1 :]

    def list_files(self, share_url: str) -> dict[str, dict[str, Any]]:
        drive, token, folder = self.public_folder_metadata(share_url)
        pending = [("", f"{drive}/root:/{quote(folder, safe='/')}:/children?{token}")]
        files: dict[str, dict[str, Any]] = {}
        while pending:
            parent, request_url = pending.pop()
            response = self.get_json(request_url)
            for item in response.get("value", []):
                name = item.get("name")
                if not isinstance(name, str) or not name:
                    raise RuntimeError("SharePoint returned an item without a valid name")
                relative = f"{parent}/{name}" if parent else name
                if "folder" in item:
                    pending.append((relative, f"{drive}/items/{item['id']}/children?{token}"))
                elif "file" in item:
                    download_url = item.get("@content.downloadUrlNoAuth") or item.get("@content.downloadUrl")
                    if not download_url:
                        raise RuntimeError(f"SharePoint did not provide a download URL for {relative}")
                    files[relative] = {"url": download_url, "etag": item.get("eTag", ""), "size": item.get("size", 0)}
            if next_link := response.get("@odata.nextLink"):
                pending.append((parent, next_link))
        return files

    def download(self, url: str, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary_name = ""
        try:
            with self.open(url, "*/*") as response, tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as temp:
                temporary_name = temp.name
                shutil.copyfileobj(response, temp, length=1024 * 1024)
            os.replace(temporary_name, destination)
        except Exception:
            if temporary_name:
                Path(temporary_name).unlink(missing_ok=True)
            raise


def safe_target(destination: Path, relative: str) -> Path:
    target = (destination / relative).resolve()
    if destination.resolve() not in target.parents:
        raise RuntimeError(f"Unsafe path returned by SharePoint: {relative}")
    return target


def load_state(path: Path) -> dict[str, Any]:
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
        return state if isinstance(state, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def sync(client: SharePointClient, share_url: str, destination: Path, dry_run: bool, delete_missing: bool) -> None:
    remote = client.list_files(share_url)
    state_path = destination / STATE_FILE_NAME
    old_state = load_state(state_path)
    print(f"Source:      {share_url}\nDestination: {destination}\nFound {len(remote)} remote file(s).")
    for relative, item in sorted(remote.items()):
        target = safe_target(destination, relative)
        if target.is_file() and old_state.get(relative, {}).get("etag") == item["etag"]:
            print(f"unchanged  {relative}")
        else:
            print(f"download   {relative}")
            if not dry_run:
                client.download(item["url"], target)
    if delete_missing and destination.exists():
        for path in sorted(destination.rglob("*"), reverse=True):
            if path.is_file() and path != state_path and path.relative_to(destination).as_posix() not in remote:
                print(f"delete     {path.relative_to(destination)}")
                if not dry_run:
                    path.unlink()
        if not dry_run:
            for path in sorted(destination.rglob("*"), reverse=True):
                if path.is_dir() and not any(path.iterdir()):
                    path.rmdir()
    if not dry_run:
        destination.mkdir(parents=True, exist_ok=True)
        compact_state = {path: {"etag": item["etag"], "size": item["size"]} for path, item in remote.items()}
        state_path.write_text(json.dumps(compact_state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env", default=".env", help="configuration file (default: .env)")
    parser.add_argument("--url", help="override SHAREPOINT_URL")
    parser.add_argument("--destination", help="override DOWNLOAD_DIR")
    parser.add_argument("--dry-run", action="store_true", help="show changes without writing files")
    parser.add_argument("--no-delete", action="store_true", help="never remove local files for this run")
    args = parser.parse_args()
    env_path = Path(args.env).expanduser()
    settings = load_env(env_path)
    share_url = args.url or settings.get("SHAREPOINT_URL", "")
    if not share_url.startswith(("https://", "http://")):
        raise RuntimeError("Set SHAREPOINT_URL to a public https:// SharePoint folder link")
    destination_text = args.destination or settings.get("DOWNLOAD_DIR", "Download")
    destination = Path(destination_text).expanduser()
    if not destination.is_absolute():
        destination = env_path.parent.resolve() / destination
    timeout = int(settings.get("TIMEOUT_SECONDS", "90"))
    if timeout < 1:
        raise RuntimeError("TIMEOUT_SECONDS must be a positive integer")
    delete_missing = bool_value(settings.get("MIRROR_DELETE", "true"), "MIRROR_DELETE") and not args.no_delete
    sync(SharePointClient(timeout), share_url, destination, args.dry_run, delete_missing)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"sync failed: {error}", file=sys.stderr)
        raise SystemExit(1)
