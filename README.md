# OneDrive & SharePoint Public Folder Sync

Mirror a publicly shared OneDrive or SharePoint folder to your computer—no Microsoft account, packages, or browser automation required.

> Want a one-time ZIP download instead? Try the [web downloader](https://onedrive-dl.github.io). This repository is the better fit for repeatable local backups and command-line workflows.

## What it does

- Downloads every file in a public shared folder, including nested folders.
- Downloads only files that are missing, changed remotely, or have a different local size.
- Optionally keeps an exact local mirror by removing files deleted remotely.
- Supports preview runs, exclusions, configurable timeouts, and parallel downloads.

## Requirements

- Python 3.9 or newer
- A **public folder** link from OneDrive or SharePoint, shared as **Anyone with the link can view**

No third-party Python dependencies are needed.

## Quick start

1. Download this repository, or save `sharepoint_public_sync.py` and `.env.example` in the same folder.
2. Create your private configuration file:

   ```bash
   cp .env.example .env
   ```

3. Edit `.env` and add the public folder URL:

   ```env
   SHAREPOINT_URL=https://your-public-folder-link
   DOWNLOAD_DIR=Download
   MIRROR_DELETE=true
   TIMEOUT_SECONDS=90
   ```

4. Check the planned changes first:

   ```bash
   python3 sharepoint_public_sync.py --dry-run
   ```

5. Run the sync:

   ```bash
   python3 sharepoint_public_sync.py
   ```

Your files are saved to `DOWNLOAD_DIR`. The tool also creates `.sharepoint-sync-state.json` there to record each downloaded file's SharePoint version marker (eTag, or modification timestamp when an eTag is unavailable).

While a sync is running, the terminal reports when it is fetching the SharePoint file list, checking local files, and completing individual downloads. Messages do not include an `INFO:` prefix.

## Common commands

```bash
# Download to a different folder for this run
python3 sharepoint_public_sync.py --destination ./backups/team-files

# Use a link without creating a .env file
python3 sharepoint_public_sync.py --url 'https://1drv.ms/f/s!example' --destination ./Download

# Download or update files, but never remove local extras
python3 sharepoint_public_sync.py --no-delete

# Skip temporary and private files
python3 sharepoint_public_sync.py --exclude '*.tmp' --exclude 'private*'

# Use more parallel downloads (may increase rate limiting)
python3 sharepoint_public_sync.py --threads 8
```

## Configuration

Settings in `.env` provide the defaults; command-line options take precedence.

| Setting           | Purpose                                                          | Default    |
| ----------------- | ---------------------------------------------------------------- | ---------- |
| `SHAREPOINT_URL`  | Public OneDrive or SharePoint **folder** URL.                    | Required   |
| `DOWNLOAD_DIR`    | Local destination. Relative paths are based on the `.env` file.  | `Download` |
| `MIRROR_DELETE`   | `true` keeps an exact mirror; `false` only downloads or updates. | `true`     |
| `TIMEOUT_SECONDS` | Timeout for each request.                                        | `90`       |

| Option                 | Purpose                                                 |
| ---------------------- | ------------------------------------------------------- |
| `--env <path>`         | Use a configuration file other than `.env`.             |
| `--url <link>`         | Override `SHAREPOINT_URL`.                              |
| `--destination <path>` | Override `DOWNLOAD_DIR`.                                |
| `--dry-run`            | List downloads and deletions without changing files.    |
| `--no-delete`          | Do not remove local files for this run.                 |
| `--threads <number>`   | Number of parallel downloads; default: `4`.             |
| `--exclude <pattern>`  | Exclude a pattern; repeat the option for more patterns. |

## Before you sync

`MIRROR_DELETE=true` means the destination is treated as a mirror. Files in that folder that are not in the shared folder may be removed. Use `--dry-run` before the first run, or use `--no-delete` if you only want additive backups.

The `.env` file can contain a private sharing link. Keep it out of version control; the included `.gitignore` is set up for that.

## Troubleshooting

**“This does not appear to be a public SharePoint folder link”**

Make sure you shared a folder—not a single file—with “Anyone with the link can view.” Open the link in a private/incognito window: if Microsoft asks you to sign in, the tool cannot access it.

**Temporary SharePoint error; retrying**

Microsoft may throttle requests. The tool retries temporary failures automatically. If it continues, lower `--threads` and try again later.

**Nothing is downloaded**

Run with `--dry-run` to see the planned work. Files marked `unchanged` exist locally, match the saved SharePoint version marker, and have the expected size. Missing, changed, or incomplete files are downloaded.

**A local edit was not downloaded again**

The tool detects local edits that change the file size. An edit that preserves the exact same size cannot be detected because the saved version marker describes the SharePoint copy, not the local file's contents. Delete that local file to force a fresh download.

## For developers

See the [Developer Guide](DEV_GUIDE.md) for the architecture, safety model, and contribution notes.

## License

Released under the [MIT License](LICENSE).
