#!/bin/bash
# Run on the Hostinger VPS from the Django project folder:
#   sudo bash /var/www/investor-cms/Investor_cms/deploy/apply_domain.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$APP_DIR/.env"
NGINX_AVAIL="/etc/nginx/sites-available/nibelimited"
NGINX_ENABLED="/etc/nginx/sites-enabled/nibelimited"

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root: sudo bash $0"
  exit 1
fi

cd "$APP_DIR"
echo "Using app directory: $APP_DIR"

if [ ! -f "$APP_DIR/manage.py" ]; then
  echo "manage.py not found in $APP_DIR"
  exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
  if [ -f "$(dirname "$APP_DIR")/.env" ]; then
    cp "$(dirname "$APP_DIR")/.env" "$ENV_FILE"
    echo "Copied .env from $(dirname "$APP_DIR")/.env"
  else
    SECRET="$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')"
    cat > "$ENV_FILE" <<EOF
DJANGO_SECRET_KEY=${SECRET}
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=www.nibelimited.com,nibelimited.com,200.97.168.12,localhost,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=https://www.nibelimited.com,https://nibelimited.com,http://www.nibelimited.com,http://nibelimited.com,https://200.97.168.12,http://200.97.168.12
DJANGO_FORCE_SCRIPT_NAME=
DJANGO_SECURE_SSL_REDIRECT=False
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EOF
    chmod 600 "$ENV_FILE"
    echo "Created $ENV_FILE"
  fi
fi

python3 - "$ENV_FILE" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
text = p.read_text(encoding="utf-8")
lines = text.splitlines()
wanted = {
    "DJANGO_DEBUG": "False",
    "DJANGO_ALLOWED_HOSTS": "www.nibelimited.com,nibelimited.com,200.97.168.12,localhost,127.0.0.1",
    "DJANGO_CSRF_TRUSTED_ORIGINS": "https://www.nibelimited.com,https://nibelimited.com,http://www.nibelimited.com,http://nibelimited.com,https://200.97.168.12,http://200.97.168.12",
    "DJANGO_FORCE_SCRIPT_NAME": "",
    "DJANGO_SECURE_SSL_REDIRECT": "False",
}
found = set()
out = []
for line in lines:
    if not line.strip() or line.lstrip().startswith("#") or "=" not in line:
        out.append(line)
        continue
    key = line.split("=", 1)[0].strip()
    if key in wanted:
        out.append(f"{key}={wanted[key]}")
        found.add(key)
    else:
        out.append(line)
for key, value in wanted.items():
    if key not in found:
        out.append(f"{key}={value}")
p.write_text("\n".join(out) + "\n", encoding="utf-8")
print(f"Updated {p} hosts and removed /CMS prefix")
PY

VENV_PIP=""
for candidate in "$APP_DIR/venv/bin/pip" "$(dirname "$APP_DIR")/venv/bin/pip"; do
  if [ -x "$candidate" ]; then
    VENV_PIP="$candidate"
    break
  fi
done

if [ -n "$VENV_PIP" ]; then
  VENV_BIN="$(dirname "$VENV_PIP")"
  "$VENV_PIP" install -r "$APP_DIR/requirements.txt"
  "$VENV_BIN/python" "$APP_DIR/manage.py" collectstatic --noinput
else
  echo "WARNING: venv not found under $APP_DIR or $(dirname "$APP_DIR"); skip pip/collectstatic"
fi

sed "s|/var/www/investor-cms|$APP_DIR|g" "$APP_DIR/deploy/nginx-nibelimited.conf" > "$NGINX_AVAIL"

CERT_DIR=""
for name in www.nibelimited.com nibelimited.com; do
  if [ -f "/etc/letsencrypt/live/$name/fullchain.pem" ]; then
    CERT_DIR="$name"
    break
  fi
done

if [ -n "$CERT_DIR" ]; then
  cat >> "$NGINX_AVAIL" <<EOF

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name www.nibelimited.com nibelimited.com 200.97.168.12;

    ssl_certificate /etc/letsencrypt/live/${CERT_DIR}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${CERT_DIR}/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    client_max_body_size 50M;

    location = /CMS {
        return 301 /;
    }
    location /CMS/static/ {
        rewrite ^/CMS/static/(.*)$ /static/\$1 last;
    }
    location /CMS/media/ {
        rewrite ^/CMS/media/(.*)$ /media/\$1 last;
    }
    location /CMS/ {
        rewrite ^/CMS/(.*)$ /\$1 permanent;
    }

    location /static/ {
        root ${APP_DIR};
        try_files \$uri @app;
        expires 30d;
        add_header Cache-Control "public";
    }

    location /media/ {
        root ${APP_DIR};
        try_files \$uri @app;
    }

    location / {
        proxy_pass http://investor_cms;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_redirect off;
    }

    location @app {
        proxy_pass http://investor_cms;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_redirect off;
    }
}
EOF
  echo "Added HTTPS server using /etc/letsencrypt/live/${CERT_DIR}"
else
  echo "No Let's Encrypt cert found; HTTP only. Run: certbot --nginx -d www.nibelimited.com -d nibelimited.com"
fi

ln -sfn "$NGINX_AVAIL" "$NGINX_ENABLED"
rm -f /etc/nginx/sites-enabled/default /etc/nginx/sites-enabled/investor-cms

for site in /etc/nginx/sites-enabled/*; do
  [ -e "$site" ] || continue
  base="$(basename "$site")"
  if [ "$base" != "nibelimited" ]; then
    echo "NOTE: $base is still enabled. If the domain 400 persists, disable it: rm $site"
  fi
done

nginx -t
systemctl reload nginx

if pgrep -f 'gunicorn nibe_cms.wsgi' >/dev/null 2>&1; then
  pkill -HUP -f 'gunicorn nibe_cms.wsgi' || true
  echo "Sent HUP to Gunicorn so it reloads Django settings"
else
  echo "Gunicorn is not running. Start it from $APP_DIR:"
  echo "  cd $APP_DIR && source venv/bin/activate && gunicorn nibe_cms.wsgi:application --bind 127.0.0.1:8001 --workers 3"
fi

echo
echo "Done. Check:"
echo "  https://www.nibelimited.com/"
echo "  http://nibelimited.com/"
echo "  https://200.97.168.12/"
