default:
    @just --list

_activate_venv:
    source .venv/bin/activate

_uv_sync: _activate_venv
    # Sync project deps into the local .venv using the active environment mode
    uv sync --active

run: _uv_sync
    # Run uvicorn inside the local .venv via uv's active-environment mode
    VIRTUAL_ENV=.venv uv run -- python -m uvicorn backend:app --reload
