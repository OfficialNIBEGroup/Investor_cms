# Deploy this Django app on the existing Hostinger VPS

This app should use its own domain or subdomain and listen only on `127.0.0.1:8001`. The existing Nginx site can keep port 80; Nginx routes requests for the new hostname to this app. The commands below assume Ubuntu, a DNS record for `investors.nibelimited.com` pointing to `200.97.168.12`, and the project copied to `/var/www/investor-cms`.

## 1. Prepare the server

SSH to the VPS as root (or a sudo-enabled user), then:

```bash
apt update
apt install -y python3-venv python3-pip nginx screen
mkdir -p /var/www/investor-cms
```

Upload/clone this project into `/var/www/investor-cms`. Do not copy a development `.env`, `db.sqlite3`, or local `venv` over existing production data. If you already have production data, back it up before updating files.

## 2. Create the environment and initialize Django

```bash
cd /var/www/investor-cms
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Create a production `.env` in this directory (keep it private; it contains credentials):

```bash
cat > .env <<'EOF'
DJANGO_SECRET_KEY=REPLACE_WITH_A_LONG_RANDOM_SECRET
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=investors.nibelimited.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://investors.nibelimited.com
DJANGO_SECURE_SSL_REDIRECT=True
EMAIL_HOST_USER=your-sending-address@gmail.com
EMAIL_HOST_PASSWORD=your-google-app-password
EOF
chmod 600 .env
```

Generate a secret with `python -c 'import secrets; print(secrets.token_urlsafe(50))'` and replace the placeholder. Set the correct mail credentials, or omit them if email sending is not needed. Then initialize the database, create an admin, and collect static files:

```bash
source venv/bin/activate
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

If you have an existing production `db.sqlite3` and uploaded `media/`, preserve and back them up; migrations do not replace that data.

## 3. Run the app in a named screen session

```bash
cd /var/www/investor-cms
source venv/bin/activate
screen -S investor-cms
```

Inside the screen session, start the app:

```bash
gunicorn nibe_cms.wsgi:application --bind 127.0.0.1:8001 --workers 3 --access-logfile - --error-logfile -
```

Detach and leave it running with **Ctrl+A**, then **D**. Reconnect with `screen -r investor-cms`; list sessions with `screen -ls`. To stop it, reconnect and press **Ctrl+C**, then `exit`. Use a different session name and port if those are already occupied.

## 4. Add a separate Nginx site

Create `/etc/nginx/sites-available/investor-cms` with this configuration. It does not replace the existing `nibelimited.com` site:

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name investors.nibelimited.com;

    location /static/ {
        alias /var/www/investor-cms/staticfiles/;
    }

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site and verify Nginx before reloading:

```bash
ln -s /etc/nginx/sites-available/investor-cms /etc/nginx/sites-enabled/investor-cms
nginx -t
systemctl reload nginx
```

Then issue HTTPS for the subdomain (Hostinger DNS must point to this VPS first):

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d investors.nibelimited.com
```

Open `https://investors.nibelimited.com`. If the project needs uploaded media, configure a deliberate secure media-serving path before exposing `/media/`; this app includes investor document uploads, and serving that directory as a public Nginx alias could disclose private documents.

## Updating the app later

Back up `db.sqlite3`, `.env`, and `media/` first. Copy the updated code, then run `cd /var/www/investor-cms && source venv/bin/activate && pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput`. Restart Gunicorn in the `investor-cms` screen session (Ctrl+C, then rerun its command).

## Important behavior of screen

`screen` keeps Gunicorn alive after you disconnect from SSH, but it does not automatically restart the process after a VPS reboot or a crash. After a reboot, SSH in and start the same named session and Gunicorn command again. A systemd service is preferable if automatic restart on boot is required.
