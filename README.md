# Palanaeum

Palanaeum is a Django web application and REST API for transcribing, archiving, tagging, and searching spoken events (such as Q&As, panels, and livestreams), complete with audio/image source management, audio snippet extraction, user collections, and staff moderation workflows.

---

## Tech Stack & Dependencies

### Runtime & Core Services

- **Python 3.12** & **Django 6.0** (`Django==6.0.10`) with **Django REST Framework** (`3.18.2`).
- **PostgreSQL** (`postgres:17` in `docker-compose.yml`) — **Required.** Palanaeum relies on PostgreSQL-specific full-text search and query features (`SearchVectorField`, `GinIndex`, `DISTINCT ON`, and raw `to_tsquery` SQL). SQLite is not supported.
- **Redis** (`redis:8` in `docker-compose.yml`) — Used as:
  - the Celery message broker and result backend,
  - the Django cache backend (`default`, `search`, and `config` caches, plus `cached_db` sessions) when `PALA_CACHE_CONFIG=redis`, and
  - the `sorl-thumbnail` key-value store (`THUMBNAIL_KVSTORE`).
- **Celery** (`celery==5.7.0`) — Runs background tasks in `palanaeum/tasks.py` (audio transcoding to MP3, snippet extraction/muting, ZIP backups, and a periodic 6-hour `upload_new_sources_to_cloud` beat task).

### System Dependencies

- **`ffmpeg` & `ffprobe`** (plus `libavcodec-extra` in Docker) — Required at runtime for probing audio duration, transcoding uploaded audio to MP3, cutting audio snippets, and muting audio segments.
- **PostgreSQL client libraries** (`postgresql-client` in Docker; `psycopg[binary]` in `requirements.txt`).

### Key Python Packages

Installed via `requirements.txt` (runtime) and `requirements-dev.txt` (adds test coverage):

- **Configuration & Dev**: `django-environ`, `django-extensions` (`runserver_plus`), `Werkzeug`, `django-debug-toolbar` (enabled when `PALA_DEBUG=True`)
- **Database, Cache & Tasks**: `psycopg[binary]`, `redis`, `celery`
- **Content, Media & Search**: `nh3` (HTML sanitization), `Pillow`, `sorl-thumbnail`, `lxml` (HTML diffs in entry version history), `requests` (URL title scraping & Backblaze B2 API), `pytz`
- **API**: `djangorestframework`, `django-filter`, `django-cors-headers`
- **Testing & Coverage**: `factory_boy`, `coverage` (in `requirements-dev.txt`)

---

## Local Development Setup

You can run Palanaeum either entirely inside Docker Compose or in a hybrid setup (Dockerized Postgres & Redis + local Python virtualenv).

### Option 1: Full Docker Compose Stack

1. Start all services (`db`, `redis`, `web`, and `celery`):
   ```bash
   docker compose up --build
   ```
   (`web` runs `manage.py runserver_plus` on `http://127.0.0.1:9000/`, with the repository bind-mounted at `/app` for live reload.)

2. On first launch, apply migrations and create a superuser:
   ```bash
   docker compose exec web python manage.py migrate
   docker compose exec web python manage.py createsuperuser
   ```

3. After pulling new changes (which may include updated requirements or migrations):
   ```bash
   docker compose up --build
   docker compose exec web python manage.py migrate
   ```

> **Note:** `docker-compose.yml` sets `PALA_ENV_FILE=/dev/null` and injects container-specific environment variables (`PALA_DB_HOST=db`, `PALA_DB_USER=docker`, `PALA_DB_PASSWORD=docker`, `PALA_CACHE_CONFIG=redis`) so container config does not conflict with a host `.env` file.

### Option 2: Hybrid Local Setup (Local Python + Docker Postgres & Redis)

1. Start PostgreSQL and Redis in Docker:
   ```bash
   docker compose up -d --wait db redis
   ```

2. Create a Python 3.12 virtual environment and install dependencies:
   ```bash
   python3.12 -m venv .venv
   .venv/bin/pip install -r requirements-dev.txt
   ```
   *(Use `-r requirements.txt` if you do not need `coverage`.)*

3. Create your local `.env` from `.env.example` and match the Docker PostgreSQL credentials:
   ```bash
   cp .env.example .env
   ```
   In `.env`, set at least:
   ```dotenv
   PALA_DEBUG=True
   PALA_DB_HOST=127.0.0.1
   PALA_DB_PORT=5432
   PALA_DB_NAME=palanaeum
   PALA_DB_USER=docker
   PALA_DB_PASSWORD=docker
   PALA_REDIS_HOST=127.0.0.1
   PALA_REDIS_PORT=6379
   PALA_CACHE_CONFIG=redis
   ```

4. Run database migrations, create a superuser, and start the development server:
   ```bash
   .venv/bin/python manage.py migrate
   .venv/bin/python manage.py createsuperuser
   .venv/bin/python manage.py runserver_plus
   ```
   Palanaeum will be available at `http://127.0.0.1:9000/`.

5. *(Optional)* Start a local Celery worker if you are working on audio uploads, snippet creation/muting, or cloud uploads:
   ```bash
   .venv/bin/celery -A palanaeum worker -l info
   ```
   To also run periodic tasks (`upload_new_sources_to_cloud` every 6 hours), run Celery Beat in another terminal:
   ```bash
   .venv/bin/celery -A palanaeum beat -l info
   ```

> **Audio playback note:** Django's development server does not support HTTP byte-range requests (`206 Partial Content`), so seeking inside audio files in the browser requires serving media through a production web server such as Nginx (see `deploy/nginx/`).

---

## Running the Test Suite

Palanaeum uses Django's built-in test runner configured via `TEST_RUNNER = "palanaeum.tests.runner.PalanaeumTestRunner"` in `palanaeum/settings.py`.

### Prerequisites & Isolation

- **PostgreSQL must be running** (`docker compose up -d --wait db`) and your configured `PALA_DB_USER` must have permission to create and drop the `test_palanaeum` database (the `docker` role in `docker-compose.yml` has this by default).
- **Live Redis and Celery workers are not required.** `PalanaeumTestRunner` (`palanaeum/tests/runner.py`) isolates every test run from local development state by:
  - redirecting `MEDIA_ROOT`, `CONFIG_UPLOADS`, `UPLOAD_DIRECTORY`, `CHUNKS_DIRECTORY`, and `BACKUP_DIR` to a temporary directory cleaned up after the run,
  - overriding `CACHES` (`default`, `search`, `config`) to `DummyCache` (and rebinding module-level caches when individual tests opt into `LocMemCache`),
  - switching `sorl-thumbnail` to `cached_db_kvstore` and Celery to `memory://`,
  - using `MD5PasswordHasher` for fast user/auth setup, and
  - resetting `GlobalRequestKeeper` thread-local requests and active timezones before and after each test.
- **`ffmpeg` / `ffprobe` is optional:** most task tests mock `subprocess.run`, while `test_transcode_source_real_ffmpeg_smoke` in `palanaeum/tests/test_tasks.py` performs a real WAV-to-MP3 transcode if both binaries are present on `PATH` and automatically skips otherwise.

### Test & Coverage Commands

Using the local virtual environment:

```bash
# Run the full test suite (203 tests)
.venv/bin/python manage.py test

# Verbose output
.venv/bin/python manage.py test --verbosity=2

# Run a single test module, class, or test method
.venv/bin/python manage.py test palanaeum.tests.test_search
.venv/bin/python manage.py test palanaeum.tests.test_models.EventModelTests

# Run with line and branch coverage (configured in .coveragerc)
.venv/bin/coverage run manage.py test
.venv/bin/coverage report
```

Or inside the Docker `web` container:

```bash
docker compose exec web python manage.py test
```

> **Note on `@unittest.expectedFailure`:** Tests covering known pre-existing application bugs assert the intended behavior and are marked with `@unittest.expectedFailure` (currently `39` of `203` tests, so the suite reports `OK (expected failures=39)`). Fixing one of those bugs will immediately report an `unexpected success` so the marker can be removed.

---

## Configuration & Environment Variables

All Django settings live in `palanaeum/settings.py`, powered by `django-environ`. Every project-specific environment variable uses the `PALA_` prefix, loaded from the environment or `.env` (override path with `PALA_ENV_FILE`). See `.env.example` for all supported variables:

| Area | Key Variables | Notes |
| --- | --- | --- |
| Core & Security | `PALA_DEBUG`, `PALA_SECRET_KEY`, `PALA_ALLOWED_HOSTS`, `PALA_CSRF_TRUSTED_ORIGINS` | `PALA_SECRET_KEY` is **required** whenever `PALA_DEBUG=False` (including `collectstatic` builds). |
| Appearance | `PALA_STYLE`, `PALA_TINYMCE_API_KEY` | `PALA_STYLE` must be `blue` (default), `green`, or `pink`. Compiled CSS lives under `palanaeum/static/palanaeum/css/` (SCSS sources in `palanaeum/sass/`). |
| Database | `PALA_DB_HOST`, `PALA_DB_PORT`, `PALA_DB_NAME`, `PALA_DB_USER`, `PALA_DB_PASSWORD` | PostgreSQL connection parameters. |
| Redis & Cache | `PALA_REDIS_HOST`, `PALA_REDIS_PORT`, `PALA_REDIS_DB`, `PALA_CACHE_CONFIG` | `PALA_CACHE_CONFIG` accepts `dummy` (default) or `redis`. |
| Storage Paths | `PALA_MEDIA_ROOT`, `PALA_BACKUP_DIR`, `PALA_UPLOAD_DIRECTORY`, `PALA_CHUNKS_DIRECTORY` | Media, backups, and Fine Uploader chunk directories. |
| Email | `PALA_EMAIL_HOST`, `PALA_EMAIL_PORT`, `PALA_EMAIL_USER`, `PALA_EMAIL_PASSWORD`, `PALA_EMAIL_BACKEND`, `PALA_ADMINS` | Defaults to `console.EmailBackend` when `PALA_EMAIL_HOST` is empty. |

### Runtime Site Configuration & `Sites` Module

- **Site config (`/admin/`):** Runtime settings (`page_title`, `default_page_length`, review notices, upload size limits, audio bitrate, Backblaze B2 cloud credentials, logo/favicons, navbar items, and related sites) are stored in the `ConfigEntry` table (initialized on `migrate`) and edited through Palanaeum's built-in admin interface at `/admin/` (superuser accounts only).
- **Sites module:** Django's `django.contrib.sites` framework is enabled (`PALA_SITE_ID`, default `1`). Update the `Site` record's domain and display name in the database (for example via `manage.py shell`) for feeds, sitemaps, and password-reset emails.

---

## Useful Management Commands

```bash
# Rebuild PostgreSQL full-text search vectors (EntrySearchVector)
python manage.py rebuild_search_index

# Generate sample events for local development
python manage.py generate_and_insert_test_events -n 5

# Create a ZIP backup (dumpdata + media/) in PALA_BACKUP_DIR
python manage.py backup

# Batch re-transcode audio sources/snippets or upload ready sources to cloud storage
python manage.py transcode_all
python manage.py upload_to_cloud

# Collect static files (provide PALA_SECRET_KEY if PALA_DEBUG=False)
PALA_SECRET_KEY=build-only-key python manage.py collectstatic --noinput
```

*(Note: `palanaeum/management/commands/fix_bad_uploads.py` is a legacy one-off script without a `BaseCommand` class and should not be invoked via `manage.py`.)*

---

## REST API, Feeds & Sitemaps

- **REST API (`/api/`):** Read-only DRF viewsets for `events`, `upcoming_events`, `tags`, `entry`, `search_entry`, and `random_entry` (with browsable login at `/api-auth/`). Default rate throttles are `30/min` (anonymous) and `10/second` (authenticated).
- **Generating API tokens:**
  ```bash
  python manage.py drf_create_token <username>
  ```
  Send the token in the HTTP `Authorization` header:
  ```http
  Authorization: Token <your_token_here>
  ```
- **Feeds & Sitemap:**
  - `/recent/feed/` and `/events/<id>-<slug>/feed/` (RSS feeds)
  - `/sitemap.xml` (event sitemap)

---

## Deployment, Contributing & License

- Deployment manifests and server configs (`k8s/`, `nginx/`, `supervisor/`, `uwsgi/`) live under `deploy/`, alongside the root `Dockerfile` and `docker-compose.yml`.
- See `CONTRIBUTING.md` for contribution guidelines and community channels.
- Licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)** — see `LICENSE`.
