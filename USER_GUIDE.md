# User Guide: OneDrive/SharePoint CLI Downloader

This tool allows you to mirror or download the contents of a publicly shared OneDrive or SharePoint folder to your local machine without needing a Microsoft account.

## Quick Start

### 1. Prerequisites

Ensure you have **Python 3.9+** installed on your system.

### 2. Setup

1. Clone this repository or download the `sharepoint_public_sync.py` script.
2. Create a `.env` file in the same directory as the script with the following content:
   ```env
   SHAREPOINT_URL=https://your-public-folder-link-here
   DOWNLOAD_DIR=./Downloads/MyFolder
   MIRROR_DELETE=true
   TIMEOUT_SECONDS=90
   ```

### 3. Running the tool

Run the script using Python:

```bash
python3 sharepoint_public_sync.py
```

## Command Line Options

You can override `.env` settings using command line flags:

| Flag                   | Description                                        | Example                                  |
| :--------------------- | :------------------------------------------------- | :--------------------------------------- |
| `--url <link>`         | Override the SharePoint URL                        | `--url https://1drv.ms/f/s!...`          |
| `--destination <path>` | Change where files are saved                       | `--destination ./backup`                 |
| `--dry-run`            | Show what would happen without downloading         | `--dry-run`                              |
| `--no-delete`          | Keep local files that were removed from the remote | `--no-delete`                            |
| `--threads <num>`      | Number of parallel downloads (default: 4)          | `--threads 8`                            |
| `--exclude <pattern>`  | Skip files matching the glob pattern               | `--exclude "*.tmp" --exclude "private*"` |

## Troubleshooting

### "This does not appear to be a public SharePoint folder link"

Ensure the link is a **folder** link, not a file link, and that it is shared as "Anyone with the link can view." Test the link in an incognito window; if it asks for a login, it won't work.

### "Temporary SharePoint error; retrying..."

SharePoint sometimes limits request rates. The tool automatically retries with an exponential backoff. If this persists, try reducing the `--threads` count.
