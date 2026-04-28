<!-- blueprint
type: pattern
name: file-upload
version: 1.0.0
requires: [protocol/types, patterns/auth-token]
platform: any
tier: free
-->

# File Upload Blueprint

Pattern for handling file uploads, image processing, storage
management, CDN integration, and signed URL generation. Covers the
full lifecycle from upload through processing to delivery.

## Overview

Most web applications need file handling — profile avatars, content
images, document uploads, media assets. This pattern defines the
upload flow, validation, processing pipeline, storage abstraction,
and delivery mechanisms including signed URLs for private assets
and CDN integration for public assets.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: FileRecord
          fields_used: [id, filename, mime_type, size, visibility, urls, owner_id]
        - name: ErrorResponse
          fields_used: [code, message, category, retryable]
        - name: AgentManifest
          fields_used: [name, version, url, capabilities]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/auth-token
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: AuthToken
          fields_used: [sub, cap, exp]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Design Principles

1. **Validate at ingestion** — verify MIME types from magic bytes, enforce size limits before reading the full body, and sanitize filenames to prevent directory traversal.
2. **Privacy by default** — strip EXIF metadata from images, generate opaque storage keys via UUID, and use signed URLs for private asset access.
3. **Storage abstraction** — decouple upload handling from the storage provider, allowing swap between local, S3, R2, and GCS without application code changes.
4. **Progressive processing** — store the original first, then process variants asynchronously; partial success is acceptable for batch uploads.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: file-upload
      description: Accept, validate, process, and store uploaded files
      parameters:
        - name: file
          type: binary
          required: true
          description: File data as multipart form field
        - name: visibility
          type: string
          required: false
          description: Access level — public or private
        - name: purpose
          type: string
          required: false
          description: Categorization — avatar, content, document, attachment
      inherits: Upload validation pipeline, MIME verification, EXIF stripping
      overridable: true
      override_constraints: Must preserve magic-byte validation and filename sanitization

  types:
    - name: FileRecord
      description: Metadata record for an uploaded file including URLs for all variants
      inherited_by: Types section
    - name: StorageProvider
      description: Interface for put, get, delete, exists, and signed-url operations
      inherited_by: Storage Providers section

  endpoints:
    - path: /files/upload
      description: Upload a single file with validation and processing
      inherited_by: Endpoints section
    - path: /files/upload/batch
      description: Upload multiple files in a single request
      inherited_by: Endpoints section
    - path: /files/:id
      description: Retrieve file metadata
      inherited_by: Endpoints section
    - path: /files/:id/download
      description: Download file or redirect to CDN
      inherited_by: Endpoints section
    - path: /files/:id/signed-url
      description: Generate a time-limited signed download URL for private files
      inherited_by: Endpoints section

  events:
    - topic: file.uploaded
      description: Emitted when a file is successfully uploaded and processed
      payload: {file_id, filename, mime_type, size, visibility, owner_id}
    - topic: file.deleted
      description: Emitted when a file is deleted
      payload: {file_id, owner_id}
```

---

## Specification

### Blueprint Format

```yaml
name: file-upload
version: 1.0.0
description: File upload, processing, and delivery

config:
  max_file_size: 10485760         # 10 MB
  allowed_types:
    - image/jpeg
    - image/png
    - image/webp
    - image/gif
    - application/pdf
  image_processing:
    thumbnails:
      - name: thumb
        width: 150
        height: 150
        fit: cover
      - name: medium
        width: 800
        height: 600
        fit: inside
    format: webp                   # Convert images to webp
    quality: 80
    strip_metadata: true           # Remove EXIF data
  storage:
    provider: local                # local | s3 | r2 | gcs
    base_path: ./uploads
    public_url: /uploads
  cdn:
    enabled: false
    base_url: https://cdn.example.com
  signed_urls:
    enabled: false
    ttl: 3600                      # 1 hour
```

### Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/files/upload` | authenticated | Upload a file |
| POST | `/files/upload/batch` | authenticated | Upload multiple files |
| GET | `/files/:id` | varies | Get file metadata |
| GET | `/files/:id/download` | varies | Download file or redirect to CDN |
| DELETE | `/files/:id` | owner or admin | Delete a file |
| POST | `/files/:id/signed-url` | authenticated | Generate signed download URL |
| GET | `/files` | authenticated | List user's files |

---

## Upload Flow

### Single File Upload (POST /files/upload)

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| file | binary | yes | The file data |
| visibility | string | no | `public` (default) or `private` |
| purpose | string | no | `avatar`, `content`, `document`, `attachment` |
| alt_text | string | no | Alt text for images (accessibility) |

**Processing pipeline:**

```
1. Validate request
   a. Check Content-Length ≤ max_file_size
   b. Check Content-Type against allowed_types
   c. Read file magic bytes to verify actual type (not just header)

2. Generate file record
   a. id = UUID v4
   b. storage_key = "<year>/<month>/<id>/<original_filename>"
   c. Record original filename, size, MIME type

3. Store original file
   a. Write to storage provider at storage_key
   b. Set appropriate permissions (public-read or private)

4. Process (if image)
   a. Strip EXIF metadata (privacy — removes GPS, camera info)
   b. Convert to target format (webp) if configured
   c. Generate thumbnails per config
   d. Store processed variants alongside original:
      - "<storage_key>/original.<ext>"
      - "<storage_key>/thumb.webp"
      - "<storage_key>/medium.webp"

5. Save file record to database

6. Return file metadata with URLs
```

**Response (201 Created):**
```json
{
  "id": "file-a1b2c3d4",
  "filename": "photo.jpg",
  "mime_type": "image/jpeg",
  "size": 2048576,
  "visibility": "public",
  "purpose": "content",
  "alt_text": "Team photo",
  "urls": {
    "original": "/files/file-a1b2c3d4/download",
    "thumb": "/files/file-a1b2c3d4/download?variant=thumb",
    "medium": "/files/file-a1b2c3d4/download?variant=medium"
  },
  "created_at": 1712160000,
  "owner_id": "user-xyz"
}
```

### Batch Upload (POST /files/upload/batch)

**Request:** `multipart/form-data` with multiple `file` fields.

- Maximum 10 files per batch
- Same validation per file
- Returns array of file records (partial success allowed)

**Response:**
```json
{
  "files": [
    {"id": "file-001", "filename": "photo1.jpg", "status": "uploaded"},
    {"id": "file-002", "filename": "photo2.jpg", "status": "uploaded"},
    {"id": null, "filename": "malware.exe", "status": "rejected", "reason": "Type not allowed"}
  ],
  "uploaded": 2,
  "rejected": 1
}
```

---

## Validation

### MIME Type Verification

Do NOT trust the `Content-Type` header alone. Verify the actual
file content:

```
1. Read first 512 bytes of the file
2. Detect MIME type from magic bytes:
   - JPEG: starts with FF D8 FF
   - PNG:  starts with 89 50 4E 47
   - WebP: starts with 52 49 46 46 ... 57 45 42 50
   - GIF:  starts with 47 49 46 38
   - PDF:  starts with 25 50 44 46
3. Compare detected type with Content-Type header
4. If mismatch → reject with 415 Unsupported Media Type
```

### Size Limits

- Check `Content-Length` header before reading body
- Enforce max size during streaming (abort read if exceeded)
- Return 413 Payload Too Large if exceeded

### Filename Sanitization

```
1. Extract filename from Content-Disposition
2. Strip path components (prevent directory traversal)
3. Replace non-alphanumeric characters (except .-_) with underscore
4. Truncate to 255 characters
5. Ensure unique storage key (UUID prefix handles this)
```

---

## Image Processing

### Thumbnail Generation

```
For each configured thumbnail:
  1. Decode source image
  2. Apply fit mode:
     - cover: resize to fill dimensions, crop excess
     - inside: resize to fit within dimensions, preserve aspect ratio
     - fill: stretch to exact dimensions (rarely used)
  3. Encode to target format at configured quality
  4. Store with variant name suffix
```

### EXIF Stripping

All uploaded images MUST have EXIF metadata stripped before storage:
- GPS coordinates (privacy)
- Camera/device info (privacy)
- Orientation tag is applied to pixel data before stripping
  (so the image displays correctly without the EXIF tag)

### Format Conversion

If `config.image_processing.format` is set:
- Original file is stored as-is (preserved)
- Processed variants are converted to the target format
- Animated GIFs are preserved as GIF (not converted to static webp)

---

## Storage Providers

### Storage Interface

| Operation | Signature | Description |
|-----------|-----------|-------------|
| Put | `(key string, data io.Reader, opts PutOpts) → error` | Store file |
| Get | `(key string) → (io.ReadCloser, error)` | Retrieve file |
| Delete | `(key string) → error` | Delete file |
| Exists | `(key string) → (bool, error)` | Check existence |
| SignedURL | `(key string, ttl int) → (string, error)` | Generate signed URL |

### Local Storage

```yaml
storage:
  provider: local
  base_path: ./uploads
  public_url: /uploads
```

- Files stored on the local filesystem
- Served directly by the web server for public files
- Suitable for development and single-server deployments
- `base_path` MUST NOT be inside the source tree

### S3-Compatible Storage

```yaml
storage:
  provider: s3
  bucket: my-uploads
  region: us-east-1
  prefix: weblisk/
  endpoint: ""            # Custom endpoint for S3-compatible (MinIO, R2)
```

- Credentials from environment: `AWS_ACCESS_KEY_ID`,
  `AWS_SECRET_ACCESS_KEY`
- Public files: served via bucket URL or CDN
- Private files: served via signed URLs

### Cloudflare R2

```yaml
storage:
  provider: r2
  bucket: my-uploads
  account_id: ${CF_ACCOUNT_ID}
```

- Uses S3-compatible API with Cloudflare endpoint
- No egress fees — ideal for CDN delivery

---

## Signed URLs

For private files that require authentication to access:

```
POST /files/:id/signed-url

Response:
{
  "url": "https://storage.example.com/uploads/2026/04/file-abc/original.jpg?X-Amz-Signature=...",
  "expires_at": 1712163600
}
```

**Signed URL generation:**
```
1. Verify requester has permission to access the file
2. Generate provider-specific signed URL:
   - S3: presigned GetObject URL
   - R2: presigned URL via S3 API
   - Local: HMAC-signed URL with expiry parameter
3. Return URL with expiry timestamp
```

**Local signed URLs:**
```
path = /uploads/<key>
expiry = now + ttl
signature = HMAC-SHA256(secret, path + expiry)
url = path + "?expires=" + expiry + "&sig=" + hex(signature)
```

The server validates `expires` and `sig` on each request.

---

## CDN Integration

When CDN is enabled, public file URLs point to the CDN instead of
the origin server:

```
Without CDN: /files/file-abc/download
With CDN:    https://cdn.example.com/uploads/2026/04/file-abc/medium.webp
```

### Cache Headers

Public files served with:
```
Cache-Control: public, max-age=31536000, immutable
```

Files are immutable because the storage key includes the file ID.
Updated files get new IDs and new URLs.

### Cache Invalidation

Not needed for normal operations (immutable URLs). For deleted files,
the CDN will naturally stop serving them when the origin returns 404.

---

## File Record

### Database Schema

| Field | Type | Description |
|-------|------|-------------|
| id | string | UUID |
| owner_id | string | User who uploaded |
| filename | string | Sanitized original filename |
| storage_key | string | Storage path |
| mime_type | string | Detected MIME type |
| size | int64 | File size in bytes |
| visibility | string | `public` or `private` |
| purpose | string | `avatar`, `content`, `document`, `attachment` |
| alt_text | string | Image alt text |
| variants | json | Map of variant names to storage keys |
| created_at | int64 | Unix epoch seconds |
| deleted_at | int64 | Soft delete timestamp |

### File Storage Interface

| Operation | Signature | Description |
|-----------|-----------|-------------|
| CreateFile | `(record FileRecord) → error` | Store file metadata |
| GetFile | `(id string) → (FileRecord, error)` | Get file metadata |
| ListFiles | `(ownerID string, filter FileFilter) → ([]FileRecord, error)` | List user files |
| DeleteFile | `(id string) → error` | Soft delete |

---

## Implementation Notes

- File upload MUST use streaming — do NOT buffer the entire file in
  memory before writing to storage
- EXIF stripping MUST happen before any variant is stored (privacy)
- The `Content-Disposition` header should use `attachment` for
  downloads and `inline` for images displayed in the browser
- Deletion is soft — set `deleted_at`, stop serving, and run a
  background cleanup job to purge storage after a retention period
- The upload endpoint MUST enforce per-user rate limits to prevent
  storage abuse (e.g., 100 uploads per hour)
- Uploaded files MUST NOT be executable — set appropriate permissions
  and serve with `X-Content-Type-Options: nosniff`

## Verification Checklist

- [ ] MIME type is verified by reading magic bytes (first 512 bytes), not just the Content-Type header; mismatches return 415
- [ ] Content-Length is checked against `max_file_size` before reading the body; streaming enforces the limit and aborts with 413 if exceeded
- [ ] Filenames are sanitized: path components stripped, non-alphanumeric chars (except `.-_`) replaced, truncated to 255 characters
- [ ] EXIF metadata is stripped from all images before any variant is stored; orientation is applied to pixel data before stripping
- [ ] Animated GIFs are preserved as GIF and not converted to static webp
- [ ] Thumbnails are generated per configured dimensions and fit mode (cover, inside, fill) and stored alongside the original
- [ ] Batch upload accepts max 10 files and returns partial-success responses (per-file status with `uploaded`/`rejected` counts)
- [ ] Signed URL generation verifies requester permission, creates a provider-specific presigned URL, and includes an expiry timestamp
- [ ] Local signed URLs use HMAC-SHA256 with a secret over path + expiry, and the server validates `expires` and `sig` on each request
- [ ] Public files are served with `Cache-Control: public, max-age=31536000, immutable` when CDN is enabled
- [ ] File upload uses streaming — the entire file is NOT buffered in memory before writing to storage
- [ ] Storage `base_path` is not inside the source tree; uploaded files are not executable and are served with `X-Content-Type-Options: nosniff`
- [ ] Per-user upload rate limits are enforced (e.g., 100 uploads per hour)
- [ ] Deletion is soft (sets `deleted_at`); a background cleanup job purges storage after the retention period
