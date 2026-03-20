# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Movizz is a Django-based multiplayer web app hosting two guessing games:
- **Movizz** (`quizz` app): Guess movies from quotes or screenshots
- **Lyrizz** (`lyrizz` app): Guess songs from lyrics

The Django project directory is `guess_movie/` (naming inconsistency: repo is `movizz`, Django project is `guess_movie`).

## Development Commands

All Django commands run from the `guess_movie/` directory.

**Start development environment (Docker):**
```bash
docker compose -f docker-compose-dev.yml up
```
This starts MySQL, Redis, and the Django app on port 80.

**Database migrations:**
```bash
cd guess_movie
python manage.py makemigrations
python manage.py migrate
```

**Static files:**
```bash
python manage.py collectstatic --noinput
```

**Translations (after modifying `.po` files in `guess_movie/locale/`):**
```bash
django-admin makemessages --all --ignore=env
django-admin compilemessages --ignore=env
```

**Run dev server manually:**
```bash
python manage.py runserver 0.0.0.0:80
```

## Architecture

### Stack
- **Django 3.1.4** — HTTP views, models, templates
- **Django Channels 3** + **Redis** — WebSocket multiplayer synchronization
- **MySQL** — Primary database
- **Gunicorn + Uvicorn workers** — HTTP server (production)
- **Daphne** — ASGI/WebSocket server (production)
- **Nginx** — Reverse proxy (routes HTTP → Gunicorn, WS → Daphne)
- **Materialize CSS** — Frontend styling

### Multiplayer Real-time Flow
WebSocket consumers (`consumers.py`) handle game state. Players connect via WebSocket → join a Redis channel group → state changes broadcast to all group members. There are separate consumers for:
- Game master (host) vs. player roles
- Quote mode vs. image mode (in `quizz`)
- Lobby, gameplay, and results phases

### URL Structure
- HTTP routes: `quizz/urls.py` (mounted at `/`) and `lyrizz/urls.py` (mounted at `/lyrizz/`)
- WebSocket routes: `quizz/routing.py` and `lyrizz/routing.py`, merged in `guess_movie/asgi.py`

### Environment Detection
`settings.py` uses the `IS_PROD` env variable to toggle debug mode, allowed hosts, HTTPS enforcement, and Redis connection strings. Dev uses `redis://redis:6379`; prod uses an authenticated Redis URL.

### Internationalization
Default language is French (`fr`). English (`en`) is also supported. Translation strings live in `guess_movie/locale/`. After editing `.po` files, run `compilemessages` to regenerate `.mo` files.

### Data
Movie/song content (quotes, lyrics, covers, screenshots) is **not stored in git**. It must be populated via Jupyter notebooks in `notebooks/movizz/` and `notebooks/lyrizz/`, which pull from IMDb, OpenSubtitle, FilmGrab, Spotify, and Genius APIs. Media files go in `guess_movie/media/`.
