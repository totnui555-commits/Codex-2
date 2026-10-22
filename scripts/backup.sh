#!/usr/bin/env bash
set -euo pipefail
: "${BACKUP_DIRECTORY:?Set an encrypted private backup directory}"
umask 077
mkdir -p "$BACKUP_DIRECTORY"
backup_path="$BACKUP_DIRECTORY/company-$(date -u +%Y%m%dT%H%M%SZ).dump"
docker compose exec -T postgres pg_dump -U company -Fc company > "$backup_path"
printf 'Backup written to %s\n' "$backup_path"
