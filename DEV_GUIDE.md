# Developer Guide — CLI Sync

## Design in one minute

The script reads the public HTML page for a shared folder, extracts the temporary drive endpoint and access token Microsoft exposes for that share, then walks the folder through the corresponding API. It uses only the Python standard library.

```text
Public folder link → shared-folder metadata → recursive file listing
                                            → compare local ETags
                                            → download changed files → save state
```

## Key pieces

| Area                          | Responsibility                                                                             |
| ----------------------------- | ------------------------------------------------------------------------------------------ |
| `SharePointClient`            | Requests, cookies, retry/backoff, folder metadata, and downloads.                          |
| `sync()`                      | Filtering, change detection, parallel downloads, optional deletion, and state persistence. |
| `safe_target()`               | Ensures remote paths cannot write outside the selected destination.                        |
| `.sharepoint-sync-state.json` | Stores remote ETags and sizes for incremental syncs.                                       |

## Local development

The project has no install step. Create a `.env` from `.env.example`, then safely inspect a real public share:

```bash
cp .env.example .env
python3 sharepoint_public_sync.py --dry-run
```

Use a dedicated test destination. A normal run with mirroring enabled can delete local files that are absent from the remote share.

## Implementation notes

- Downloads use `ThreadPoolExecutor`; `--threads` controls concurrency.
- HTTP `429`, `500`, `502`, `503`, and `504` responses are retried with exponential backoff.
- Files are written to a temporary sibling file and atomically moved into place after a successful download.
- Path containment is checked before every write to protect against directory traversal.

## Extending the tool

- Update public-share parsing in `public_folder_metadata()` if Microsoft changes the shared-folder page.
- Adjust traversal in `list_files()` for new metadata or pagination behavior.
- Add filters around the `exclude_patterns` handling in `sync()`.
- Keep new write paths behind `safe_target()` and preserve the temporary-file download behavior.

## License

This project is licensed under the [MIT License](LICENSE).
