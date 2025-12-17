# H3 Auctions - Deployment Guide for Hostinger VPS

## Prerequisites

- Hostinger VPS access (SSH credentials)
- Domain name configured and pointing to your VPS IP
- MySQL database created in Hostinger hPanel

## Step 1: Connect to Your VPS

```bash
ssh root@your-vps-ip
# Or
ssh username@your-vps-ip
```

## Step 2: Update System and Install Dependencies

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv -y

# Install MySQL client libraries
sudo apt install python3-dev default-libmysqlclient-dev build-essential pkg-config -y

# Install Nginx (for reverse proxy)
sudo apt install nginx -y

# Install Supervisor (for process management)
sudo apt install supervisor -y
```

## Step 3: Create Project Directory

```bash
# Create directory for your project
sudo mkdir -p /var/www/h3auctions
sudo chown -R $USER:$USER /var/www/h3auctions
cd /var/www/h3auctions
```

## Step 4: Upload Project Files

### Option A: Using Git (Recommended)

```bash
# Install git if not installed
sudo apt install git -y

# Clone your repository (if using Git)
git clone your-repo-url .

# Or initialize and add remote
git init
git remote add origin your-repo-url
git pull origin main
```

### Option B: Using SCP (from your local machine)

```bash
# From your local machine, run:
scp -r /path/to/h3auctions/* username@your-vps-ip:/var/www/h3auctions/
```

### Option C: Using FileZilla/SFTP

- Connect via SFTP to your VPS
- Upload all project files to `/var/www/h3auctions/`

## Step 5: Set Up Python Virtual Environment

```bash
cd /var/www/h3auctions

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt
```

## Step 6: Configure Environment Variables

```bash
# Create .env file
nano .env
```

Add the following content (update with your actual values):

```env
DEBUG=False
SECRET_KEY=your-generated-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
LANGUAGE_CODE=ar
TIME_ZONE=Asia/Dubai
USE_PYMYSQL=False
DATABASE_URL=mysql://db_user:db_password@localhost:3306/db_name
```

**Generate a secret key:**

```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Step 7: Set Up MySQL Database

### In Hostinger hPanel:

1. Go to **Databases** → **MySQL Databases**
2. Create a new database (e.g., `h3auctions_db`)
3. Create a database user
4. Grant all privileges to the user
5. Note the database name, username, and password

### Update .env file with database credentials:

```env
DATABASE_URL=mysql://db_user:db_password@localhost:3306/h3auctions_db
```

## Step 8: Run Django Migrations

```bash
cd /var/www/h3auctions
source venv/bin/activate

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

## Step 9: Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/h3auctions
```

Add the following configuration:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    client_max_body_size 100M;

    location /static/ {
        alias /var/www/h3auctions/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/h3auctions/media/;
        expires 30d;
        add_header Cache-Control "public";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/h3auctions /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Step 10: Configure Supervisor (Process Manager)

```bash
sudo nano /etc/supervisor/conf.d/h3auctions.conf
```

Add the following:

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

Create logs directory:

```bash
mkdir -p /var/www/h3auctions/logs
```

Update Supervisor:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start h3auctions
```

## Step 11: Install Gunicorn

Add gunicorn to requirements.txt, then:

```bash
source venv/bin/activate
pip install gunicorn
```

## Step 12: Set Up SSL Certificate (HTTPS)

### Using Let's Encrypt (Free SSL):

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Follow the prompts to complete SSL setup.

## Step 13: Set Permissions

```bash
cd /var/www/h3auctions
sudo chown -R www-data:www-data /var/www/h3auctions
sudo chmod -R 755 /var/www/h3auctions
sudo chmod -R 775 /var/www/h3auctions/media
sudo chmod -R 775 /var/www/h3auctions/staticfiles
```

## Step 14: Test Your Deployment

1. Visit `http://yourdomain.com` (should redirect to HTTPS)
2. Check admin panel: `https://yourdomain.com/admin/`
3. Test all features (home, draw plate, contact, etc.)

## Troubleshooting

### Check Nginx logs:

```bash
sudo tail -f /var/log/nginx/error.log
```

### Check Gunicorn logs:

```bash
sudo tail -f /var/www/h3auctions/logs/gunicorn.log
```

### Check Supervisor status:

```bash
sudo supervisorctl status h3auctions
```

### Restart services:

```bash
sudo systemctl restart nginx
sudo supervisorctl restart h3auctions
```

### Django errors:

```bash
cd /var/www/h3auctions
source venv/bin/activate
python manage.py check
```

## Maintenance Commands

### Update code:

```bash
cd /var/www/h3auctions
git pull  # if using git
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo supervisorctl restart h3auctions
```

### Clear Django cache:

```bash
python manage.py clearsessions
```

## Security Checklist

- [ ] DEBUG=False in production
- [ ] Strong SECRET_KEY set
- [ ] ALLOWED_HOSTS configured correctly
- [ ] SSL certificate installed
- [ ] Database credentials secure
- [ ] File permissions set correctly
- [ ] Firewall configured (if needed)

## Support

For issues, check:

- Nginx error logs
- Gunicorn logs
- Django logs
- Supervisor status
