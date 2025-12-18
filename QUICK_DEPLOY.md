# Quick Deployment Checklist for Hostinger VPS

## Before You Start

- [ ] VPS IP address and SSH credentials
- [ ] Domain name pointing to VPS IP
- [ ] MySQL database created in Hostinger hPanel
- [ ] Database credentials (username, password, database name)

## Quick Steps

### 1. Connect to VPS

```bash
ssh root@your-vps-ip
```

### 2. Install Basic Tools

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv nginx supervisor git -y
sudo apt install python3-dev default-libmysqlclient-dev build-essential -y
```

### 3. Create Project Directory

```bash
sudo mkdir -p /var/www/h3auctions
sudo chown -R $USER:$USER /var/www/h3auctions
cd /var/www/h3auctions
```

### 4. Upload Your Project

**Option A: Using SCP (from your local machine)**

```bash
scp -r D:\Alkhtm_alawal\h3auctions\* username@your-vps-ip:/var/www/h3auctions/
```

**Option B: Using Git**

```bash
git clone your-repo-url .
```

**Option C: Using FileZilla/SFTP**

- Connect via SFTP
- Upload all files to `/var/www/h3auctions/`

### 5. Set Up Environment

```bash
cd /var/www/h3auctions
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 6. Create .env File

```bash
nano .env
```

Paste this (update with your values):

```env
DEBUG=False
SECRET_KEY=generate-strong-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
LANGUAGE_CODE=ar
TIME_ZONE=Asia/Dubai
USE_PYMYSQL=False
DATABASE_URL=mysql://db_user:db_password@localhost:3306/db_name
```

**Generate secret key:**

```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 7. Database Setup

```bash
source venv/bin/activate
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

### 8. Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/h3auctions
```

Paste this (replace `yourdomain.com`):

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    client_max_body_size 100M;

    location /static/ {
        alias /var/www/h3auctions/staticfiles/;
    }

    location /media/ {
        alias /var/www/h3auctions/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/h3auctions /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 9. Supervisor Configuration

```bash
sudo nano /etc/supervisor/conf.d/h3auctions.conf
```

Paste this:

```ini
[program:h3auctions]
command=/var/www/h3auctions/venv/bin/gunicorn h3auctions.wsgi:application --bind 127.0.0.1:8000 --workers 3
directory=/var/www/h3auctions
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/www/h3auctions/logs/gunicorn.log
```

Create logs directory and start:

```bash
mkdir -p /var/www/h3auctions/logs
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start h3auctions
```

### 10. SSL Certificate (HTTPS)

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 11. Set Permissions

```bash
sudo chown -R www-data:www-data /var/www/h3auctions
sudo chmod -R 755 /var/www/h3auctions
sudo chmod -R 775 /var/www/h3auctions/media
```

### 12. Test

Visit: `https://yourdomain.com`

## Common Commands

**Restart services:**

```bash
sudo systemctl restart nginx
sudo supervisorctl restart h3auctions
```

**View logs:**

```bash
sudo tail -f /var/www/h3auctions/logs/gunicorn.log
sudo tail -f /var/log/nginx/error.log
```

**Update code:**

```bash
cd /var/www/h3auctions
source venv/bin/activate
git pull  # if using git
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo supervisorctl restart h3auctions
```

## Troubleshooting

**Check if services are running:**

```bash
sudo systemctl status nginx
sudo supervisorctl status h3auctions
```

**Check Django:**

```bash
cd /var/www/h3auctions
source venv/bin/activate
python manage.py check
```

**Permission issues:**

```bash
sudo chown -R www-data:www-data /var/www/h3auctions
```
