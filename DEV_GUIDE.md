# Developer Guide: OneDrive/SharePoint CLI Downloader

## Architecture

The tool works by scraping the public HTML view of a shared OneDrive/SharePoint folder to extract a temporary `driveUrl` and `driveAccessToken`. It then uses these to interact with the Microsoft Graph-like API provided for public shares.

### Core Components

- **`SharePointClient`**: Handles HTTP requests, cookie management, and retries. It is designed to be dependency-free, using only `urllib`.
- **`sync` loop**:
  1. Fetches remote file metadata recursively.
  2. Compares remote ETags with a local state file (`.sharepoint-sync-state.json`).
  3. Downloads only new or changed files using a `ThreadPoolExecutor` for performance.
  4. (Optional) Removes local files that no longer exist on the remote.

## Implementation Details

### Path Security

To prevent directory traversal attacks (ZipSlip), the tool uses `safe_target()`. This function resolves the final path and ensures it is still contained within the intended destination directory.

### Performance

The tool implements parallel downloads via `concurrent.futures.ThreadPoolExecutor`. The thread count is configurable to balance speed against the risk of being rate-limited (HTTP 429).

## Contributing

### Development Setup

1. Create a `.env` file as described in the `USER_GUIDE.md`.
2. Use `python3 sharepoint_public_sync.py --dry-run` to test metadata fetching without downloading files.

### Adding Features

- **Filters**: To add new filtering logic, modify the `sync` function's `exclude_patterns` handling.
- **New API Endpoints**: If Microsoft changes the public share API, updates will likely be needed in `public_folder_metadata` and `list_files`.
