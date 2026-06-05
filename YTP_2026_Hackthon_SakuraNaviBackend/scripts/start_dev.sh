#!/usr/bin/env bash

set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT}/.env.development"
VENV_PY="${ROOT}/.venv/bin/python"
VENV_UV="${ROOT}/.venv/bin/uvicorn"
ALEMBIC="${ROOT}/.venv/bin/alembic"
HAS_PSQL=0

cyan='\033[36m'
green='\033[32m'
yellow='\033[33m'
red='\033[31m'
magenta='\033[35m'
reset='\033[0m'

write_step() { printf "  ${cyan}%s${reset}\n" "$1"; }
write_ok() { printf "  ${green}[OK]${reset} %s\n" "$1"; }
write_warn() { printf "  ${yellow}[!!]${reset} %s\n" "$1"; }
write_err() { printf "  ${red}[ERR]${reset} %s\n" "$1"; }
write_title() { printf "\n${magenta}===  %s  ===${reset}\n" "$1"; }

trim() {
  local s="${1#"${1%%[![:space:]]*}"}"
  s="${s%"${s##*[![:space:]]}"}"
  printf "%s" "$s"
}

strip_quotes() {
  local v="$1"
  if [[ "$v" == \"*\" && "$v" == *\" ]]; then
    printf "%s" "${v:1:${#v}-2}"
    return
  fi
  if [[ "$v" == \'*\' && "$v" == *\' ]]; then
    printf "%s" "${v:1:${#v}-2}"
    return
  fi
  printf "%s" "$v"
}

load_env_file() {
  local file="$1"
  if [[ ! -f "$file" ]]; then
    write_err ".env file not found: $file"
    exit 1
  fi

  while IFS= read -r line || [[ -n "$line" ]]; do
    line="$(trim "$line")"
    [[ -z "$line" || "$line" == \#* ]] && continue
    [[ "$line" != *=* ]] && continue
    local key value
    key="$(trim "${line%%=*}")"
    value="$(trim "${line#*=}")"
    value="$(strip_quotes "$value")"
    export "$key=$value"
  done < "$file"
}

parse_database_url() {
  local url="$1"
  if [[ "$url" =~ ^postgresql\+psycopg://([^:]+):([^@]+)@([^:/]+):?([0-9]+)?/(.+)$ ]]; then
    DB_USER="${BASH_REMATCH[1]}"
    DB_PASS="${BASH_REMATCH[2]}"
    DB_HOST="${BASH_REMATCH[3]}"
    DB_PORT="${BASH_REMATCH[4]:-5432}"
    DB_NAME="${BASH_REMATCH[5]}"
    return
  fi
  write_err "Cannot parse DATABASE_URL: $url"
  exit 1
}

ensure_tools() {
  if command -v psql >/dev/null 2>&1; then
    HAS_PSQL=1
  else
    HAS_PSQL=0
    write_warn "psql not found in PATH. DB connectivity check will use Python fallback."
  fi
  [[ -x "$VENV_PY" ]] || { write_err "python not found: $VENV_PY"; exit 1; }
  [[ -x "$ALEMBIC" ]] || { write_err "alembic not found: $ALEMBIC"; exit 1; }
  [[ -x "$VENV_UV" ]] || { write_err "uvicorn not found: $VENV_UV"; exit 1; }
}

check_db_connection() {
  write_step "Checking database connection ..."
  if [[ "$HAS_PSQL" -eq 1 ]]; then
    if ! out="$(PGPASSWORD="$DB_PASS" psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -c 'SELECT 1' -t -q 2>&1)"; then
      write_err "Cannot connect to database ${DB_NAME}@${DB_HOST}:${DB_PORT}"
      printf "  %s\n" "$out"
      exit 1
    fi
  else
    if ! out="$(PGHOST="$DB_HOST" PGPORT="$DB_PORT" PGUSER="$DB_USER" PGPASSWORD="$DB_PASS" PGDATABASE="$DB_NAME" \
      "$VENV_PY" -c 'import psycopg; conn=psycopg.connect(); cur=conn.cursor(); cur.execute("SELECT 1"); cur.fetchone(); conn.close()' 2>&1)"; then
      write_err "Cannot connect to database ${DB_NAME}@${DB_HOST}:${DB_PORT}"
      printf "  %s\n" "$out"
      exit 1
    fi
  fi
  write_ok "Database connected (${DB_NAME}@${DB_HOST}:${DB_PORT})"
}

alembic_rev_line() {
  local raw="$1"
  local line
  line="$(printf "%s\n" "$raw" | awk 'NF{last=$0} END{print last}')"
  printf "%s" "${line:-"(no revision)"}"
}

run_alembic() {
  (cd "$ROOT" && "$ALEMBIC" "$@" 2>&1)
}

rebuild_database() {
  if [[ "$HAS_PSQL" -ne 1 ]]; then
    write_err "Database rebuild requires psql. Install PostgreSQL client tools and retry."
    exit 1
  fi
  local super_pass out
  write_warn "This will delete all data in ${DB_NAME}."
  read -r -s -p "  Enter postgres superuser password: " super_pass
  printf "\n"

  write_step "Terminating active connections ..."
  PGPASSWORD="$super_pass" psql -U postgres -h "$DB_HOST" -p "$DB_PORT" -d postgres \
    -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${DB_NAME}' AND pid <> pg_backend_pid();" -q >/dev/null

  write_step "Dropping database ${DB_NAME} ..."
  PGPASSWORD="$super_pass" psql -U postgres -h "$DB_HOST" -p "$DB_PORT" -d postgres \
    -c "DROP DATABASE IF EXISTS ${DB_NAME};" -q >/dev/null

  write_step "Creating database ${DB_NAME} ..."
  PGPASSWORD="$super_pass" psql -U postgres -h "$DB_HOST" -p "$DB_PORT" -d postgres \
    -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER} ENCODING 'UTF8';" >/dev/null

  write_step "Granting privileges ..."
  PGPASSWORD="$super_pass" psql -U postgres -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" \
    -c "REVOKE ALL ON SCHEMA public FROM PUBLIC; GRANT USAGE, CREATE ON SCHEMA public TO ${DB_USER}; ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT,INSERT,UPDATE,DELETE ON TABLES TO ${DB_USER}; ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE,SELECT ON SEQUENCES TO ${DB_USER};" -q >/dev/null

  write_step "Running alembic upgrade head ..."
  if ! run_alembic upgrade head; then
    write_err "Migration still failed after rebuild."
    exit 1
  fi
  write_ok "Database rebuilt and migrated."
}

write_title "SakuraNavi Backend — development (macOS/Linux)"
write_step "Loading ${ENV_FILE} ..."
load_env_file "$ENV_FILE"
export APP_ENV=development
write_ok "Environment loaded (APP_ENV=development)"

ensure_tools
parse_database_url "${DATABASE_URL:-}"
check_db_connection

write_step "Checking Alembic migration status ..."
current_raw="$(run_alembic current || true)"
heads_raw="$(run_alembic heads || true)"

if [[ "$current_raw" == *"(head)"* ]]; then
  write_ok "Migration is up to date."
else
  current_line="$(alembic_rev_line "$current_raw")"
  head_line="$(alembic_rev_line "$heads_raw")"
  write_warn "Migration is not latest."
  printf "  Current: %s\n" "$current_line"
  printf "  Head:    %s\n" "$head_line"

  printf "\n"
  read -r -p "  Run alembic upgrade head? [Y/n] " ans
  if [[ -z "${ans:-}" || "$ans" =~ ^[Yy]$ ]]; then
    write_step "Running alembic upgrade head ..."
    if ! run_alembic upgrade head; then
      write_err "alembic upgrade head failed."
      read -r -p "  Rebuild database (destructive)? [y/N] " rebuild
      if [[ "${rebuild:-}" =~ ^[Yy]$ ]]; then
        rebuild_database
      else
        write_warn "Skip rebuild. Starting anyway (schema may be inconsistent)."
      fi
    else
      write_ok "Migration upgraded successfully."
    fi
  else
    write_warn "Skipped migration. Starting anyway (schema may be inconsistent)."
  fi
fi

PORT="${PORT:-8000}"
write_title "Starting uvicorn (development, port ${PORT})"
printf "  ${cyan}http://localhost:%s/docs${reset}\n\n" "$PORT"

exec "$VENV_UV" app.main:app \
  --host 0.0.0.0 \
  --port "$PORT" \
  --loop app.core.event_loop:selector_event_loop \
  --reload \
  --log-level debug
