#!/usr/bin/env bash
# Instala ou atualiza a API na VPS (Ubuntu). Uso:
#   sudo git clone https://github.com/JefersonQueiroga/chamados-api.git /opt/chamados-api
#   sudo bash /opt/chamados-api/deploy.sh
set -euo pipefail

DOMINIO="${DOMINIO:-api-chamados.jefersonqueiroga.com.br}"
EMAIL="${EMAIL:-}"
PORTA="${PORTA:-8011}"
PASTA="/opt/chamados-api"
DADOS="/var/lib/chamados-api"
USUARIO="chamados"

[ "$(id -u)" -eq 0 ] || { echo "Rode com sudo."; exit 1; }
[ -f "$PASTA/main.py" ] || { echo "O projeto precisa estar em $PASTA."; exit 1; }

echo "==> Conferindo a porta 80"
if ss -ltnp | grep ':80 ' >/dev/null && ! ss -ltnp | grep ':80 ' | grep nginx >/dev/null; then
  echo "A porta 80 está em uso por outro programa (não é o Nginx):"
  ss -ltnp | grep ':80 '
  echo "Ajuste manualmente antes de continuar."
  exit 1
fi
if ss -ltn | grep ":$PORTA " >/dev/null && ! systemctl is-active --quiet chamados-api; then
  echo "A porta $PORTA já está em uso. Rode de novo com PORTA=outra_porta."
  exit 1
fi

echo "==> Instalando pacotes"
apt-get update -y
apt-get install -y python3 python3-venv python3-pip nginx certbot python3-certbot-nginx sqlite3 git curl
timedatectl set-timezone America/Sao_Paulo || true

echo "==> Usuário e pastas"
id "$USUARIO" >/dev/null 2>&1 || useradd --system --home "$DADOS" --shell /usr/sbin/nologin "$USUARIO"
mkdir -p "$DADOS/backups"
chown -R "$USUARIO:$USUARIO" "$DADOS"

echo "==> Ambiente Python"
[ -d "$PASTA/.venv" ] || python3 -m venv "$PASTA/.venv"
"$PASTA/.venv/bin/pip" install -q --upgrade pip
"$PASTA/.venv/bin/pip" install -q -r "$PASTA/requirements.txt"

if [ ! -f "$PASTA/.env" ]; then
  echo "==> Criando .env"
  cat > "$PASTA/.env" <<ENV
CHAVE_PROFESSOR=$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')
URL_BANCO=sqlite:///$DADOS/chamados.db
LIMITE_POR_MINUTO=60
URL_API=https://$DOMINIO
ENV
fi
chown root:"$USUARIO" "$PASTA/.env"
chmod 640 "$PASTA/.env"

echo "==> Serviço systemd"
cat > /etc/systemd/system/chamados-api.service <<SVC
[Unit]
Description=API Chamados de Manutenção IFRN
After=network.target

[Service]
User=$USUARIO
Group=$USUARIO
WorkingDirectory=$PASTA
ExecStart=$PASTA/.venv/bin/uvicorn main:app --host 127.0.0.1 --port $PORTA
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
SVC
systemctl daemon-reload
systemctl enable chamados-api >/dev/null
systemctl restart chamados-api

echo "==> Nginx"
if [ ! -f /etc/nginx/sites-available/chamados-api ] || ! grep -q "listen 443" /etc/nginx/sites-available/chamados-api; then
  cat > /etc/nginx/sites-available/chamados-api <<NGX
server {
    listen 80;
    server_name $DOMINIO;

    location / {
        proxy_pass http://127.0.0.1:$PORTA;
        proxy_set_header Host \$host;
        proxy_set_header X-Forwarded-For \$remote_addr;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
NGX
fi
ln -sf /etc/nginx/sites-available/chamados-api /etc/nginx/sites-enabled/chamados-api
nginx -t
systemctl reload nginx

if ufw status 2>/dev/null | grep "Status: active" >/dev/null; then
  ufw allow OpenSSH >/dev/null
  ufw allow "Nginx Full" >/dev/null
fi

echo "==> HTTPS"
IP_SERVIDOR=$(curl -4 -s https://ifconfig.me || true)
IP_DOMINIO=$(getent ahostsv4 "$DOMINIO" | awk 'NR==1{print $1}' || true)
if [ -n "$IP_DOMINIO" ] && [ "$IP_DOMINIO" = "$IP_SERVIDOR" ]; then
  if [ -n "$EMAIL" ]; then CONTATO="-m $EMAIL"; else CONTATO="--register-unsafely-without-email"; fi
  certbot --nginx -d "$DOMINIO" --non-interactive --agree-tos --redirect $CONTATO || echo "Certbot falhou; a API segue em HTTP."
else
  echo "O domínio $DOMINIO ainda não aponta para este servidor ($IP_SERVIDOR)."
  echo "Crie o registro A no DNS e rode este script de novo para ativar o HTTPS."
fi

echo "==> Backup diário"
cat > /etc/cron.d/chamados-api <<CRON
0 3 * * * $USUARIO sqlite3 $DADOS/chamados.db ".backup $DADOS/backups/chamados-\$(date +\%F).db" && find $DADOS/backups -name '*.db' -mtime +14 -delete
CRON

sleep 2
echo
if curl -fs "http://127.0.0.1:$PORTA/" >/dev/null; then echo "API no ar!"; else echo "A API não respondeu. Veja: journalctl -u chamados-api -n 50"; fi
echo "Swagger: https://$DOMINIO/docs"
echo "Chave do professor (coloque no .env do seu computador):"
grep CHAVE_PROFESSOR "$PASTA/.env"
