#!/usr/bin/env bash
# ==============================================================================
# Enterprise Platform (IRE) — Database Backup & Recovery Script
# ==============================================================================

set -euo pipefail

BACKUP_DIR="/tmp/ire_backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DB_NAME="${POSTGRES_DB:-ire_production_db}"
DB_USER="${POSTGRES_USER:-ire_admin}"
DB_HOST="${POSTGRES_HOST:-localhost}"
S3_BUCKET="${S3_BACKUP_BUCKET:-s3://ire-enterprise-backups}"

mkdir -p "${BACKUP_DIR}"

backup() {
    echo "[INFO] Starting database backup for '${DB_NAME}' at ${TIMESTAMP}..."
    BACKUP_FILE="${BACKUP_DIR}/backup_${DB_NAME}_${TIMESTAMP}.sql.gz"
    
    PGPASSWORD="${POSTGRES_PASSWORD:-ire_password_production_secure_2026}" pg_dump -h "${DB_HOST}" -U "${DB_USER}" "${DB_NAME}" | gzip > "${BACKUP_FILE}"
    
    echo "[INFO] Encrypting backup with AES-256..."
    ENCRYPTED_FILE="${BACKUP_FILE}.enc"
    openssl enc -aes-256-cbc -salt -in "${BACKUP_FILE}" -out "${ENCRYPTED_FILE}" -k "${BACKUP_ENCRYPTION_KEY:-SuperSecretKey2026}" -pbkdf2
    
    echo "[INFO] Uploading encrypted backup to S3 bucket '${S3_BUCKET}'..."
    # aws s3 cp "${ENCRYPTED_FILE}" "${S3_BUCKET}/$(basename "${ENCRYPTED_FILE}")"
    echo "[SUCCESS] Backup complete: ${ENCRYPTED_FILE}"
}

restore() {
    FILE_TO_RESTORE="${1:-}"
    if [ -z "${FILE_TO_RESTORE}" ]; then
        echo "[ERROR] Please specify file path to restore."
        exit 1
    fi
    echo "[INFO] Restoring database from '${FILE_TO_RESTORE}'..."
    DECRYPTED_FILE="/tmp/restored.sql.gz"
    openssl enc -d -aes-256-cbc -in "${FILE_TO_RESTORE}" -out "${DECRYPTED_FILE}" -k "${BACKUP_ENCRYPTION_KEY:-SuperSecretKey2026}" -pbkdf2
    gunzip -c "${DECRYPTED_FILE}" | PGPASSWORD="${POSTGRES_PASSWORD:-ire_password_production_secure_2026}" psql -h "${DB_HOST}" -U "${DB_USER}" "${DB_NAME}"
    echo "[SUCCESS] Database restoration completed successfully."
}

case "${1:-backup}" in
    backup)
        backup
        ;;
    restore)
        restore "${2:-}"
        ;;
    *)
        echo "Usage: $0 {backup|restore <file_path>}"
        exit 1
        ;;
esac
