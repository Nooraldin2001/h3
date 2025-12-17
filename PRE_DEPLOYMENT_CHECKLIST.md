# Pre-Deployment Checklist

## Information You Need Before Starting

### From Hostinger hPanel:
- [ ] VPS IP Address: 153.92.5.195
- [ ] SSH Username: root
- [ ] SSH Password/Key: A01061601600a@
- [ ] MySQL Database Name: h3auctions_db
- [ ] MySQL Username: h3auctions_db
- [ ] MySQL Password: A0508800121a@
- [ ] MySQL Host: localhost  (usually `localhost`)

### Domain Information:
- [ ] Domain Name: h3auctions.ae
- [ ] Domain pointing to VPS IP: [ ] Yes [0] No

## Files Ready for Deployment

✅ **Created Files:**
- `.gitignore` - Excludes sensitive files
- `DEPLOYMENT.md` - Detailed deployment guide
- `QUICK_DEPLOY.md` - Quick step-by-step guide
- `deploy.sh` - Automated deployment script
- `requirements.txt` - Updated with gunicorn

## What to Upload to VPS

**Upload these files/folders:**
- ✅ All Python files (`.py`)
- ✅ `templates/` folder
- ✅ `static/` folder
- ✅ `plates/` app folder
- ✅ `h3auctions/` project folder
- ✅ `manage.py`
- ✅ `requirements.txt`
- ✅ `passenger_wsgi.py`
- ✅ `deploy.sh`
- ✅ `locale/` folder (translations)

**DO NOT upload:**
- ❌ `db.sqlite3` (use MySQL on production)
- ❌ `__pycache__/` folders
- ❌ `.env` file (create on server)
- ❌ `staticfiles/` (will be generated)
- ❌ `media/` (will be created on server)
- ❌ `venv/` (create on server)

## Quick Start Commands

### 1. Connect to VPS
```bash
ssh root@your-vps-ip
```

### 2. Create .env file on server
```bash
nano .env
```

### 3. Generate Secret Key (run on server)
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 4. Run deployment script (after uploading files)
```bash
chmod +x deploy.sh
./deploy.sh
```

## Important Notes

1. **Database**: Make sure MySQL database is created in Hostinger hPanel before running migrations
2. **Domain**: Point your domain to the VPS IP address in DNS settings
3. **SSL**: Set up SSL certificate after deployment for HTTPS
4. **Backup**: Keep a backup of your local project before deploying

## Support Resources

- Full guide: `DEPLOYMENT.md`
- Quick guide: `QUICK_DEPLOY.md`
- Hostinger Support: https://www.hostinger.com/support

