# Public SharePoint Folder Sync

Download or mirror any **publicly shared SharePoint folder** with Python's standard library. No Microsoft account, rclone configuration, OAuth app, or third-party package is required.

The script opens the public sharing link on every run, obtains SharePoint's temporary anonymous token in memory, lists the folder recursively, and downloads new or changed files. It never writes a password, cookie, or access token to disk.

> Use this only for folders the owner intentionally made public and that you are allowed to download.

## Requirements

- Python 3.9+
- A public SharePoint **folder** link that opens in a private/incognito browser window without signing in

Check Python:

```bash
python3 --version
```

## Quick start

1. Clone/download this repository.
2. Create private local configuration (ignored by Git):

   ```bash
   cp .env.example .env
   ```

3. Edit `.env` and set `SHAREPOINT_URL` to your public folder URL.
4. Preview all changes before downloading:

   ```bash
   python3 sharepoint_public_sync.py --dry-run
   ```

5. Run the sync:

   ```bash
   python3 sharepoint_public_sync.py
   ```

On Linux/macOS you can also use:

```bash
./sync-sharepoint.sh --dry-run
./sync-sharepoint.sh
```

## Configuration

Copy [`.env.example`](.env.example) to `.env`; only `.env` needs editing.

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `SHAREPOINT_URL` | Yes | — | Public SharePoint folder link. |
| `DOWNLOAD_DIR` | No | `Download` | Destination directory; relative paths are resolved from `.env`. |
| `MIRROR_DELETE` | No | `true` | `true` makes an exact mirror; `false` only downloads/updates. |
| `TIMEOUT_SECONDS` | No | `90` | Per-request network timeout. |

Example:

```dotenv
SHAREPOINT_URL=https://contoso-my.sharepoint.com/:f:/g/personal/teacher_contoso_com/ABC123?e=XYZ987
DOWNLOAD_DIR=course-notes
MIRROR_DELETE=false
TIMEOUT_SECONDS=120
```

`.env` supports blank lines, `#` comments, quoted values, and optional `export` prefixes. Do not commit it—it may contain an unlisted link.

## Commands

```bash
python3 sharepoint_public_sync.py [--env PATH] [--url URL] \
  [--destination PATH] [--dry-run] [--no-delete]
```

- `--dry-run`: show downloads/deletions; change nothing.
- `--no-delete`: one-run override that preserves local files even if `MIRROR_DELETE=true`.
- `--env configs/course.env`: use another configuration file.
- `--url URL` and `--destination PATH`: override `.env` settings, useful for automation. Avoid putting sensitive/unlisted URLs in shell history or CI logs.

## Sync behavior

- The linked SharePoint folder becomes the root of `DOWNLOAD_DIR`.
- New or changed files download into a temporary file, then move atomically into place.
- `.sharepoint-sync-state.json` in the destination records remote ETags so unchanged files are skipped later.
- `MIRROR_DELETE=true` removes local files no longer on SharePoint. Run `--dry-run` first and keep unrelated files out of the destination.
- Temporary network failures and SharePoint 429/5xx responses are retried automatically.

## Scheduling

### Linux/macOS cron

Run every day at 7 PM (replace paths with real absolute paths):

```cron
0 19 * * * /usr/bin/python3 /absolute/path/sharepoint_public_sync.py --env /absolute/path/.env >> /absolute/path/sharepoint-sync.log 2>&1
```

Test the command manually first. Cron has a minimal environment, so absolute paths matter.

### Windows Task Scheduler

Create a Basic Task and configure:

- **Program/script:** full path to `python.exe`
- **Add arguments:** `C:\path\sharepoint_public_sync.py --env C:\path\.env`
- **Start in:** the directory containing the script

## Troubleshooting

| Symptom | What to do |
| --- | --- |
| Link works only after sign-in | It is not public. Use an authenticated tool such as rclone instead. |
| `SharePoint did not supply ...` | Paste an active public **folder** sharing link, not a file link or logged-in browser URL. |
| HTTP 403 | The link may be revoked, downloads may be blocked, or sharing is no longer anonymous. |
| HTTP 429 / 503 | The script retries. If it still fails, wait and run it again. |
| Files disappeared locally | `MIRROR_DELETE=true` is an exact mirror. Use `false` or `--no-delete` going forward. |

## Limitations and security

- Only public SharePoint **folder** links are supported. A single-file link cannot be mirrored as a folder.
- The anonymous SharePoint token expires. The script refreshes it on each run; do not copy tokens into `.env`.
- The folder owner can revoke access or block downloads at any time.
- Treat `DOWNLOAD_DIR` as script-managed whenever deletion is enabled.
