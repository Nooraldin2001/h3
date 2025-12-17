# H3 Auctions - Coming Soon Page

A simple, minimal "Coming Soon" webpage ready for deployment to Hostinger hosting.

## Files Included

- `index.html` - Main HTML file
- `styles.css` - Stylesheet for the page
- `README.md` - This file

## Deployment to Hostinger

### Method 1: Using Hostinger File Manager

1. **Log in to Hostinger**
   - Go to [hpanel.hostinger.com](https://hpanel.hostinger.com)
   - Log in with your Hostinger account credentials

2. **Access File Manager**
   - Navigate to **Files** → **File Manager**
   - Open the `public_html` folder (this is your website's root directory)

3. **Upload Files**
   - Click **Upload** button
   - Select both `index.html` and `styles.css` files
   - Wait for the upload to complete

4. **Verify**
   - Visit your domain (www.h3auctions.ae) to see the "Coming Soon" page

### Method 2: Using FTP

1. **Get FTP Credentials**
   - In Hostinger hPanel, go to **Files** → **FTP Accounts**
   - Note your FTP host, username, and password

2. **Connect via FTP Client**
   - Use an FTP client like FileZilla, WinSCP, or Cyberduck
   - Connect using your FTP credentials
   - Navigate to the `public_html` directory

3. **Upload Files**
   - Upload `index.html` and `styles.css` to the `public_html` folder
   - Ensure `index.html` is in the root of `public_html`

4. **Verify**
   - Visit your domain to confirm the page is live

## Domain Configuration

### Pointing Your Domain to Hostinger

If you haven't already pointed your domain to Hostinger:

1. **Get Hostinger Nameservers**
   - In Hostinger hPanel, go to **Domains** → **Your Domain**
   - Find the nameservers (usually something like `ns1.dns-parking.com` and `ns2.dns-parking.com`)

2. **Update Domain DNS**
   - Log in to your domain registrar (where you purchased www.h3auctions.ae)
   - Update the nameservers to point to Hostinger's nameservers
   - DNS propagation can take 24-48 hours

### Alternative: Using A Record

If you prefer to use A records instead of nameservers:

1. Get your Hostinger server IP address from hPanel
2. In your domain registrar's DNS settings, add an A record:
   - **Host**: @ (or www)
   - **Value**: Your Hostinger server IP
   - **TTL**: 3600 (or default)

## Customization

### Updating Contact Information

Edit `index.html` and update the contact details in the contact section:

```html
<p><strong>Email:</strong> <a href="mailto:your-email@h3auctions.ae">your-email@h3auctions.ae</a></p>
```

### Changing Colors or Styling

Modify `styles.css` to adjust colors, fonts, or layout according to your preferences.

## Support

For Hostinger-specific support:
- Visit [Hostinger Support](https://www.hostinger.com/support)
- Contact Hostinger support through your hPanel

## Notes

- The page is fully responsive and will work on all devices
- No server-side processing is required - it's a simple static HTML page
- Make sure both `index.html` and `styles.css` are in the same directory (`public_html`)

