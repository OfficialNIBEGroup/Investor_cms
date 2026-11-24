# Deploy this Django app on the existing Hostinger VPS

The public site is bound to:

- `https://www.nibelimited.com/`
- `http://nibelimited.com/`

Gunicorn listens only on `127.0.0.1:8002`. Nginx on port 80/443 routes those hostnames to this app. The commands below assume Ubuntu, DNS for `nibelimited.com` and `www.nibelimited.com` pointing to `200.97.168.12`, and the project copied to `/var/www/investor-cms/Investor_cms`.

The old URL `https://200.97.168.12/CMS/` is redirected to `/` on the same host.

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

Create or update the production `.env` in this directory (keep it private; it contains credentials). If an older `.env` still has `DJANGO_FORCE_SCRIPT_NAME=/CMS` or `investors.nibelimited.com`, replace those values:

```bash
cat > .env <<'EOF'
DJANGO_SECRET_KEY=REPLACE_WITH_A_LONG_RANDOM_SECRET
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=www.nibelimited.com,nibelimited.com,200.97.168.12
DJANGO_CSRF_TRUSTED_ORIGINS=https://www.nibelimited.com,https://nibelimited.com,http://www.nibelimited.com,http://nibelimited.com
DJANGO_FORCE_SCRIPT_NAME=
DJANGO_SECURE_SSL_REDIRECT=False
EMAIL_HOST_USER=your-sending-address@gmail.com
EMAIL_HOST_PASSWORD=your-google-app-password
EOF
chmod 600 .env
```

Generate a secret with `python -c 'import secrets; print(secrets.token_urlsafe(50))'` and replace the placeholder. Keep existing mail credentials if they already work. Then initialize the database, create an admin if needed, and collect static files:

```bash
source venv/bin/activate
python manage.py migrate
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
gunicorn nibe_cms.wsgi:application --bind 127.0.0.1:8002 --workers 3 --access-logfile - --error-logfile -
```

Detach and leave it running with **Ctrl+A**, then **D**. Reconnect with `screen -r investor-cms`; list sessions with `screen -ls`. To stop it, reconnect and press **Ctrl+C**, then `exit`. Use a different session name and port if those are already occupied.

## 4. Bind Nginx to nibelimited.com and www.nibelimited.com

A domain request that shows Django's `Bad Request (400)` means the running app still does not allow that hostname. CSS missing on `https://200.97.168.12/` means Nginx is looking in `staticfiles/` (often empty) while the files live in `static/`, or the HTML still points at `/CMS/static/`.

After copying this code onto the VPS, run it from the Django project folder (the folder that contains `manage.py`):

```bash
sudo bash /var/www/investor-cms/Investor_cms/deploy/apply_domain.sh
```

The script finds that folder itself, creates `.env` if it is missing, and points Nginx at the same path.

That updates `.env` hosts, removes the `/CMS` prefix, installs the Nginx site, points `/static/` at `/var/www/investor-cms/static/`, and reloads Gunicorn.

If you prefer to do it by hand, disable any older site that currently owns these hostnames, then:

```bash
cp /var/www/investor-cms/deploy/nginx-nibelimited.conf /etc/nginx/sites-available/nibelimited
ln -sf /etc/nginx/sites-available/nibelimited /etc/nginx/sites-enabled/nibelimited
nginx -t
systemctl reload nginx
```

Issue HTTPS for the www host (Hostinger DNS must already point both names to this VPS). When certbot asks whether to redirect HTTP to HTTPS, choose **No** so `http://nibelimited.com/` keeps working:

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d www.nibelimited.com -d nibelimited.com
```

Open:

- `https://www.nibelimited.com/`
- `http://nibelimited.com/`

Old `/CMS/` links redirect to the same path at domain root.

If the project needs uploaded media, `/media/` is served from `/var/www/investor-cms/media/`. This directory includes investor document uploads; treat those URLs as confidential.

## Updating the app later

Back up `db.sqlite3`, `.env`, and `media/` first. Copy the updated code, then run `cd /var/www/investor-cms && source venv/bin/activate && pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput`. Restart Gunicorn in the `investor-cms` screen session (Ctrl+C, then rerun its command). Confirm `.env` still has empty `DJANGO_FORCE_SCRIPT_NAME` and the `nibelimited.com` host lists.

## Important behavior of screen

`screen` keeps Gunicorn alive after you disconnect from SSH, but it does not automatically restart the process after a VPS reboot or a crash. After a reboot, SSH in and start the same named session and Gunicorn command again. A systemd service is preferable if automatic restart on boot is required.
