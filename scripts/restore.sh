#!/usr/bin/env bash
set -euo pipefail
: "${RESTORE_DATABASE:?Set a NEW isolated restore database name}"
: "${BACKUP_FILE:?Set the backup file path}"
[[ "$RESTORE_DATABASE" =~ ^restore_[a-zA-Z0-9_]+$ ]] || { echo 'Restore database must start with restore_'; exit 1; }
docker compose exec -T postgres createdb -U company "$RESTORE_DATABASE"
docker compose exec -T postgres pg_restore -U company --exit-on-error -d "$RESTORE_DATABASE" < "$BACKUP_FILE"
printf 'Restored into isolated database %s; verify before switching traffic.\n' "$RESTORE_DATABASE"
