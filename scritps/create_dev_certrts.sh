#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
# Genera certificados auto-firmados para el stack “jmq_chirpstack_listener”
#  - Crea una CA raíz
#  - Firma un certificado de SERVIDOR para Mosquitto
#  - Firma un certificado de CLIENTE para la aplicación FastAPI
#  - Todos se colocan en app/ctx/dev  (mismo volumen para broker y app)
# ──────────────────────────────────────────────────────────────

set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CTX_DIR="$ROOT_DIR/app/ctx/dev"
mkdir -p "$CTX_DIR"
cd "$CTX_DIR"

# 1) Autoridad certificadora (CA) ─────────────────────────────
openssl req -x509 -new -nodes -days 3650 \
  -keyout ca.key -out ca.crt -sha256 -subj "/CN=jmq-dev-CA"

# 2) Clave privada del servidor ───────────────────────────────
openssl genrsa -out server.key 4096

# 3) CSR del servidor con SAN múltiples ───────────────────────
cat > server.cnf <<'EOF'
[ req ]
default_bits       = 4096
prompt             = no
default_md         = sha256
distinguished_name = dn
req_extensions     = req_ext

[ dn ]
CN = mosquitto_dev

[ req_ext ]
subjectAltName = @alt_names

[ alt_names ]
DNS.1   = mosquitto_dev
DNS.2   = mosquitto
DNS.3   = localhost
IP.1    = 127.0.0.1
EOF

openssl req -new -key server.key -out server.csr -config server.cnf

# 4) Certificado de servidor firmado por la CA ────────────────
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out server.crt -days 3650 -sha256 \
  -extensions req_ext -extfile server.cnf

# 5) Clave y certificado de CLIENTE ───────────────────────────
openssl genrsa -out cert.key 4096
cat > cert.cnf <<'EOF'
[ req ]
default_bits       = 4096
prompt             = no
default_md         = sha256
distinguished_name = dn

[ dn ]
CN = chirpstack_app_dev
EOF

openssl req -new -key cert.key -out cert.csr -config cert.cnf
openssl x509 -req -in cert.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out cert.crt -days 3650 -sha256

# 6) Enlaces con los nombres que espera el certe Python ─────
ln -sf server.crt cert.crt
ln -sf server.key cert.key

echo "✅ Certificados generados en $CTX_DIR"
echo "   - ca.crt (raíz)               -> montar en ambos contenedores"
echo "   - server.crt / server.key     -> Mosquitto"
echo "   - cert.crt / cert.key     -> (opcional) autenticación mutua"
