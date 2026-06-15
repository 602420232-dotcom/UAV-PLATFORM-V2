#!/bin/bash
#
# SSL/TLS 证书生成脚本
# 支持开发环境（自签名证书）和生产环境（Let's Encrypt）
# 生成 PKCS12 格式的 keystore
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CERT_DIR="${PROJECT_ROOT}/certs"
ENV="${ENV:-dev}"
DOMAIN="${DOMAIN:-api.uav-platform.com}"
KEYSTORE_PASSWORD="${KEYSTORE_PASSWORD:-changeit}"
DAYS_VALID="${DAYS_VALID:-365}"
KEY_ALIAS="${KEY_ALIAS:-uav-platform}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Generate SSL/TLS certificates for UAV Platform V2

Options:
    -e, --env           Environment: dev|staging|prod (default: dev)
    -d, --domain        Domain name (default: api.uav-platform.com)
    -p, --password      Keystore password (default: changeit)
    -v, --valid-days    Certificate validity days (default: 365)
    -a, --alias         Key alias (default: uav-platform)
    -h, --help          Show this help message

Examples:
    # Development environment (self-signed)
    $(basename "$0") --env dev --domain localhost

    # Production environment (Let's Encrypt)
    $(basename "$0") --env prod --domain api.uav-platform.com

EOF
}

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env)
            ENV="$2"
            shift 2
            ;;
        -d|--domain)
            DOMAIN="$2"
            shift 2
            ;;
        -p|--password)
            KEYSTORE_PASSWORD="$2"
            shift 2
            ;;
        -v|--valid-days)
            DAYS_VALID="$2"
            shift 2
            ;;
        -a|--alias)
            KEY_ALIAS="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# 创建证书目录
mkdir -p "$CERT_DIR"
cd "$CERT_DIR"

log_info "Environment: $ENV"
log_info "Domain: $DOMAIN"
log_info "Output directory: $CERT_DIR"

# 检查 OpenSSL 是否安装
if ! command -v openssl &> /dev/null; then
    log_error "OpenSSL is not installed. Please install OpenSSL first."
    exit 1
fi

OPENSSL_VERSION=$(openssl version | awk '{print $2}')
log_info "OpenSSL version: $OPENSSL_VERSION"

generate_self_signed() {
    log_info "Generating self-signed certificate for development..."

    local key_file="${CERT_DIR}/server.key"
    local cert_file="${CERT_DIR}/server.crt"
    local csr_file="${CERT_DIR}/server.csr"
    local p12_file="${CERT_DIR}/keystore.p12"
    local jks_file="${CERT_DIR}/keystore.jks"
    local truststore_file="${CERT_DIR}/truststore.jks"
    local client_key="${CERT_DIR}/client.key"
    local client_cert="${CERT_DIR}/client.crt"
    local client_p12="${CERT_DIR}/client-keystore.p12"

    # 生成 CA 私钥和证书
    log_info "Generating CA key and certificate..."
    openssl genrsa -out ca.key 4096
    openssl req -x509 -new -nodes -key ca.key -sha256 -days "$DAYS_VALID" \
        -subj "/C=CN/ST=Beijing/L=Beijing/O=UAV Platform/OU=Security/CN=UAV Platform CA" \
        -out ca.crt

    # 生成服务器私钥
    log_info "Generating server private key..."
    openssl genrsa -out "$key_file" 4096

    # 生成服务器 CSR
    log_info "Generating server CSR..."
    openssl req -new -key "$key_file" \
        -subj "/C=CN/ST=Beijing/L=Beijing/O=UAV Platform/OU=API Gateway/CN=$DOMAIN" \
        -out "$csr_file"

    # 创建扩展配置文件
    cat > server.ext << EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = $DOMAIN
DNS.2 = *.uav-platform.com
DNS.3 = localhost
DNS.4 = *.localhost
IP.1 = 127.0.0.1
IP.2 = ::1
EOF

    # 使用 CA 签名服务器证书
    log_info "Signing server certificate with CA..."
    openssl x509 -req -in "$csr_file" -CA ca.crt -CAkey ca.key -CAcreateserial \
        -out "$cert_file" -days "$DAYS_VALID" -sha256 -extfile server.ext

    # 生成 PKCS12 keystore（服务器）
    log_info "Generating PKCS12 keystore for server..."
    openssl pkcs12 -export -in "$cert_file" -inkey "$key_file" \
        -certfile ca.crt -name "$KEY_ALIAS" \
        -out "$p12_file" -password pass:"$KEYSTORE_PASSWORD"

    # 转换为 JKS 格式
    log_info "Converting to JKS keystore..."
    keytool -importkeystore -srckeystore "$p12_file" -srcstoretype PKCS12 \
        -srcstorepass "$KEYSTORE_PASSWORD" -destkeystore "$jks_file" \
        -deststoretype JKS -deststorepass "$KEYSTORE_PASSWORD" -noprompt

    # 生成信任库（包含 CA 证书）
    log_info "Generating truststore..."
    keytool -import -alias ca -file ca.crt -keystore "$truststore_file" \
        -storepass "$KEYSTORE_PASSWORD" -noprompt -trustcacerts

    # 生成客户端证书（用于 mTLS）
    log_info "Generating client certificate for mTLS..."
    openssl genrsa -out "$client_key" 4096
    openssl req -new -key "$client_key" \
        -subj "/C=CN/ST=Beijing/L=Beijing/O=UAV Platform/OU=Service Client/CN=uav-service-client" \
        -out client.csr

    cat > client.ext << EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = clientAuth
EOF

    openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
        -out "$client_cert" -days "$DAYS_VALID" -sha256 -extfile client.ext

    openssl pkcs12 -export -in "$client_cert" -inkey "$client_key" \
        -certfile ca.crt -name "uav-client" \
        -out "$client_p12" -password pass:"$KEYSTORE_PASSWORD"

    # 导出 PEM 格式（用于 Spring Boot SSL Bundle）
    log_info "Exporting PEM format for Spring Boot SSL Bundle..."
    openssl pkcs12 -in "$p12_file" -out server-cert.pem -nokeys -password pass:"$KEYSTORE_PASSWORD"
    openssl pkcs12 -in "$p12_file" -out server-key.pem -nocerts -nodes -password pass:"$KEYSTORE_PASSWORD"
    openssl pkcs12 -in "$client_p12" -out client-cert.pem -nokeys -password pass:"$KEYSTORE_PASSWORD"
    openssl pkcs12 -in "$client_p12" -out client-key.pem -nocerts -nodes -password pass:"$KEYSTORE_PASSWORD"
    cp ca.crt truststore.pem

    # 清理临时文件
    rm -f server.ext client.ext server.csr client.csr ca.srl

    log_info "Self-signed certificates generated successfully!"
    log_info "Files:"
    echo "  Server:"
    echo "    - $cert_file (PEM certificate)"
    echo "    - $key_file (PEM private key)"
    echo "    - $p12_file (PKCS12 keystore)"
    echo "    - $jks_file (JKS keystore)"
    echo "  Client (mTLS):"
    echo "    - $client_cert (PEM certificate)"
    echo "    - $client_key (PEM private key)"
    echo "    - $client_p12 (PKCS12 client keystore)"
    echo "  Trust:"
    echo "    - ca.crt (CA certificate)"
    echo "    - $truststore_file (JKS truststore)"
    echo "    - truststore.pem (PEM truststore)"
    echo "  SSL Bundle:"
    echo "    - server-cert.pem / server-key.pem"
    echo "    - client-cert.pem / client-key.pem"

    # 验证证书
    log_info "Verifying certificate chain..."
    openssl verify -CAfile ca.crt "$cert_file"
    openssl verify -CAfile ca.crt "$client_cert"
}

generate_letsencrypt() {
    log_info "Generating Let's Encrypt certificate for production..."

    if ! command -v certbot &> /dev/null; then
        log_error "Certbot is not installed. Please install certbot first."
        exit 1
    fi

    local cert_path="/etc/letsencrypt/live/$DOMAIN"
    local p12_file="${CERT_DIR}/keystore.p12"
    local jks_file="${CERT_DIR}/keystore.jks"

    # 申请 Let's Encrypt 证书
    log_info "Requesting certificate from Let's Encrypt for $DOMAIN..."
    certbot certonly --standalone -d "$DOMAIN" -d "*.${DOMAIN}" --agree-tos -n \
        --email "admin@${DOMAIN}" || {
        log_error "Failed to obtain Let's Encrypt certificate"
        exit 1
    }

    # 转换为 PKCS12
    log_info "Converting to PKCS12 keystore..."
    openssl pkcs12 -export -in "${cert_path}/fullchain.pem" \
        -inkey "${cert_path}/privkey.pem" \
        -name "$KEY_ALIAS" -out "$p12_file" \
        -password pass:"$KEYSTORE_PASSWORD"

    # 转换为 JKS
    log_info "Converting to JKS keystore..."
    keytool -importkeystore -srckeystore "$p12_file" -srcstoretype PKCS12 \
        -srcstorepass "$KEYSTORE_PASSWORD" -destkeystore "$jks_file" \
        -deststoretype JKS -deststorepass "$KEYSTORE_PASSWORD" -noprompt

    # 复制证书到项目目录
    cp "${cert_path}/fullchain.pem" "${CERT_DIR}/server.crt"
    cp "${cert_path}/privkey.pem" "${CERT_DIR}/server.key"
    cp "${cert_path}/chain.pem" "${CERT_DIR}/chain.crt"

    log_info "Let's Encrypt certificate generated successfully!"
    log_info "Certificate path: $cert_path"
    log_info "Keystore: $p12_file"
    log_info "JKS: $jks_file"

    # 设置自动续期钩子
    log_info "Setting up renewal hook..."
    cat > /etc/letsencrypt/renewal-hooks/deploy/uav-platform.sh << EOF
#!/bin/bash
# Auto-renewal hook for UAV Platform
# Converts renewed certificates to keystore format

DOMAIN="$DOMAIN"
CERT_PATH="/etc/letsencrypt/live/\$DOMAIN"
P12_FILE="$CERT_DIR/keystore.p12"
JKS_FILE="$CERT_DIR/keystore.jks"
PASSWORD="$KEYSTORE_PASSWORD"

openssl pkcs12 -export -in "\${CERT_PATH}/fullchain.pem" \\
    -inkey "\${CERT_PATH}/privkey.pem" \\
    -name "$KEY_ALIAS" -out "\$P12_FILE" \\
    -password pass:"\$PASSWORD"

keytool -importkeystore -srckeystore "\$P12_FILE" -srcstoretype PKCS12 \\
    -srcstorepass "\$PASSWORD" -destkeystore "\$JKS_FILE" \\
    -deststoretype JKS -deststorepass "\$PASSWORD" -noprompt

cp "\${CERT_PATH}/fullchain.pem" "$CERT_DIR/server.crt"
cp "\${CERT_PATH}/privkey.pem" "$CERT_DIR/server.key"

echo "[$(date)] Certificate renewed and converted for UAV Platform" >> /var/log/uav-platform-cert-renewal.log
EOF
    chmod +x /etc/letsencrypt/renewal-hooks/deploy/uav-platform.sh

    log_info "Renewal hook installed at: /etc/letsencrypt/renewal-hooks/deploy/uav-platform.sh"
}

create_k8s_secret() {
    log_info "Creating Kubernetes TLS secret..."

    local namespace="${K8S_NAMESPACE:-uav-platform}"
    local secret_name="uav-platform-tls-secret"

    # 检查 kubectl 是否可用
    if ! command -v kubectl &> /dev/null; then
        log_warn "kubectl not found, skipping Kubernetes secret creation"
        return 0
    fi

    # 创建命名空间（如果不存在）
    kubectl create namespace "$namespace" --dry-run=client -o yaml | kubectl apply -f -

    # 创建 TLS secret
    kubectl create secret tls "$secret_name" \
        --cert="${CERT_DIR}/server.crt" \
        --key="${CERT_DIR}/server.key" \
        --namespace="$namespace" \
        --dry-run=client -o yaml | kubectl apply -f -

    # 创建 CA configmap（用于 mTLS 验证）
    kubectl create configmap uav-platform-ca \
        --from-file=ca.crt="${CERT_DIR}/ca.crt" \
        --namespace="$namespace" \
        --dry-run=client -o yaml | kubectl apply -f -

    log_info "Kubernetes secret '$secret_name' created in namespace '$namespace'"
}

# 主逻辑
case "$ENV" in
    dev|development)
        generate_self_signed
        ;;
    staging)
        generate_self_signed
        ;;
    prod|production)
        generate_letsencrypt
        ;;
    *)
        log_error "Unknown environment: $ENV"
        usage
        exit 1
        ;;
esac

# 创建 Kubernetes secret（可选）
if command -v kubectl &> /dev/null; then
    read -p "Create Kubernetes TLS secret? (y/N): " create_k8s
    if [[ "$create_k8s" =~ ^[Yy]$ ]]; then
        create_k8s_secret
    fi
fi

# 打印环境变量配置
log_info "Add the following environment variables to your .env file:"
cat << EOF

# SSL Configuration
SSL_ENABLED=true
SSL_KEYSTORE=${CERT_DIR}/keystore.p12
SSL_KEYSTORE_PASSWORD=${KEYSTORE_PASSWORD}
SSL_KEYSTORE_TYPE=PKCS12
SSL_KEY_ALIAS=${KEY_ALIAS}

# mTLS Configuration
MTLS_ENABLED=true
MTLS_CLIENT_CERT=${CERT_DIR}/client-cert.pem
MTLS_CLIENT_KEY=${CERT_DIR}/client-key.pem
MTLS_TRUST_CERT=${CERT_DIR}/truststore.pem
MTLS_KEYSTORE=${CERT_DIR}/client-keystore.p12
MTLS_KEYSTORE_PASSWORD=${KEYSTORE_PASSWORD}
MTLS_TRUSTSTORE=${CERT_DIR}/truststore.jks
MTLS_TRUSTSTORE_PASSWORD=${KEYSTORE_PASSWORD}
MTLS_VERIFY_HOSTNAME=true

EOF

log_info "Certificate generation completed!"
log_info "Certificate directory: $CERT_DIR"
