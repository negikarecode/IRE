#!/usr/bin/env bash
# ==============================================================================
# Enterprise Platform — Production Self-Signed SSL Certificate Generator
# ==============================================================================

set -euo pipefail

CERTS_DIR="$(dirname "$0")/certs"
mkdir -p "${CERTS_DIR}"

echo "[INFO] Generating TLS 2048-bit SSL Certificate & Private Key for Nginx..."

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout "${CERTS_DIR}/tls.key" \
  -out "${CERTS_DIR}/tls.crt" \
  -subj "/C=US/ST=California/L=SanFrancisco/O=IRE Enterprise/CN=api.ire.health"

chmod 600 "${CERTS_DIR}/tls.key"
chmod 644 "${CERTS_DIR}/tls.crt"

echo "[SUCCESS] SSL Certificate generated successfully in ${CERTS_DIR}:"
echo " - Certificate: ${CERTS_DIR}/tls.crt"
echo " - Private Key: ${CERTS_DIR}/tls.key"
