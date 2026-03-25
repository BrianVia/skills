---
name: r2-upload
description: Upload images or files to R2 CDN (media.brianvia.com). Use when you need to upload a local file, screenshot, or image URL to get a public CDN link. Useful for AI agents that need to host images or files.
argument-hint: "<file-path-or-url> [-d directory]"
allowed-tools: Bash(r2upload *), Bash(curl *)
---

# R2 CDN Upload

Upload files to Brian's R2 CDN at `media.brianvia.com` and return a public URL.

## CLI Location

The `r2upload` CLI is at `/Users/via/Development/Personal/media-uploader/cli/r2upload` and symlinked to `/usr/local/bin/r2upload`.

## Usage

### Upload a local file

```bash
r2upload /path/to/file.png
```

Returns: `https://media.brianvia.com/<uuid>.png`

### Upload to a specific directory

```bash
r2upload /path/to/file.png -d blog/2024
```

Returns: `https://media.brianvia.com/blog/2024/<uuid>.png`

### Upload from a URL

```bash
r2upload --url https://example.com/image.png
```

### Upload from URL to a directory

```bash
r2upload --url https://example.com/image.png -d screenshots
```

### List files in the bucket

```bash
r2upload --list
r2upload --list some-directory
```

## Behavior

- All filenames are replaced with UUIDs to avoid collisions
- Original file extension is preserved
- The API supports images, videos, audio, documents, and archives
- Returns the public CDN URL on stdout; errors go to stderr
- Exit code 0 on success, 1 on failure

## When to Use

- You've taken a screenshot and need to host it somewhere
- You need to attach an image to a PR, Linear ticket, or Slack message
- You're generating diagrams or charts that need a public URL
- Any time an AI agent needs a publicly accessible file URL

## API Base

The upload API is at `https://upload.flatmeadow.com`. Files are served from `https://media.brianvia.com`. Override with `R2_API_BASE` env var.
