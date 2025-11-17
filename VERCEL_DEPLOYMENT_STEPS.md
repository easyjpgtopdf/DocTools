# 🚀 Vercel Deployment Guide - easyjpgtopdf.com

## ✅ Current Status
- **Domain:** easyjpgtopdf.com
- **GitHub Repo:** https://github.com/easyjpgtopdf/DocTools
- **Platform:** Vercel (Free Tier)

---

## 📋 Step-by-Step Deployment Process

### 1️⃣ **Vercel Account Setup**

1. Visit: https://vercel.com/signup
2. Sign up with **GitHub account** (easyjpgtopdf)
3. Authorize Vercel to access GitHub repositories

### 2️⃣ **Import Project to Vercel**

1. Go to: https://vercel.com/new
2. Select **Import Git Repository**
3. Choose repository: `easyjpgtopdf/DocTools`
4. Click **Import**

### 3️⃣ **Configure Project Settings**

**Framework Preset:** Other (Static HTML)

**Build Settings:**
- Build Command: (Leave empty)
- Output Directory: `.` (current directory)
- Install Command: (Leave empty)

**Root Directory:** `.` (project root)

**Environment Variables:**
Click "Environment Variables" and add:

| Name | Value | Environment |
|------|-------|-------------|
| `FIREBASE_API_KEY` | Your Firebase API Key | Production |
| `RAZORPAY_KEY_ID` | Your Razorpay Key ID | Production |

**⚠️ Important:** Get these values from your `.env` file

### 4️⃣ **Deploy Project**

1. Click **Deploy** button
2. Wait 1-2 minutes for build
3. Vercel will show: ✅ Deployment Ready
4. You'll get URL: `https://doctools-xyz.vercel.app`

### 5️⃣ **Add Custom Domain (easyjpgtopdf.com)**

**In Vercel Dashboard:**

1. Go to: Project Settings → Domains
2. Click **Add Domain**
3. Enter: `easyjpgtopdf.com`
4. Click **Add**
5. Also add: `www.easyjpgtopdf.com`

**Vercel will show DNS configuration needed:**

```
Type    Name    Value
A       @       76.76.21.21
CNAME   www     cname.vercel-dns.com
```

### 6️⃣ **Configure Domain DNS (GoDaddy/Namecheap/etc.)**

**If using GoDaddy:**

1. Login to: https://dcc.godaddy.com/domains
2. Find domain: easyjpgtopdf.com
3. Click **DNS** → **Manage DNS**

**Add/Update Records:**

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | @ | 76.76.21.21 | 600 |
| CNAME | www | cname.vercel-dns.com | 600 |

**Delete existing A records pointing to old IPs**

4. Click **Save**

**If using Namecheap:**

1. Login to: https://www.namecheap.com
2. Go to: Domain List → Manage
3. Advanced DNS → Add New Record

Same DNS records as above.

### 7️⃣ **Wait for DNS Propagation**

- **Normal Time:** 5-30 minutes
- **Maximum:** Up to 48 hours

**Check DNS Status:**
```bash
nslookup easyjpgtopdf.com
```

Should show: `76.76.21.21`

**Online Checker:**
- https://dnschecker.org/#A/easyjpgtopdf.com

### 8️⃣ **Automatic SSL Certificate**

Vercel will automatically:
1. Detect domain is pointing correctly
2. Issue FREE SSL certificate (Let's Encrypt)
3. Enable HTTPS on your site
4. Redirect HTTP → HTTPS automatically

**Timeline:**
- SSL provisioning: 5-10 minutes after DNS
- Status visible in Vercel → Domains section

### 9️⃣ **Verify Deployment**

**Test URLs:**
1. ✅ https://easyjpgtopdf.com
2. ✅ https://www.easyjpgtopdf.com
3. ✅ https://easyjpgtopdf.com/dashboard.html
4. ✅ https://easyjpgtopdf.com/excel-unlocker.html

**Check Features:**
- Firebase Login/Signup
- Dashboard real-time data
- Payment gateway
- All PDF/image tools

---

## 🔧 Troubleshooting

### Issue 1: "This site can't be reached"

**Causes:**
1. DNS not configured
2. DNS propagation pending
3. Vercel deployment failed

**Fix:**
```bash
# Check DNS
nslookup easyjpgtopdf.com

# Should return: 76.76.21.21
# If not, update DNS records and wait
```

### Issue 2: SSL Certificate Error

**Causes:**
1. DNS not fully propagated
2. Vercel hasn't issued certificate yet

**Fix:**
1. Wait 10-30 minutes
2. Check Vercel → Domains → SSL Status
3. Should show: ✅ Valid Certificate

### Issue 3: "ERR_CONNECTION_REFUSED"

**Causes:**
1. Domain pointing to wrong IP
2. Firewall blocking connection

**Fix:**
1. Verify DNS A record: `76.76.21.21`
2. Clear browser cache
3. Try incognito mode

### Issue 4: "Site not secure" warning

**Causes:**
1. SSL certificate not issued yet
2. Mixed content (HTTP resources on HTTPS page)

**Fix:**
1. Wait for SSL provisioning
2. Check all resources use `https://`

---

## 📊 Deployment Checklist

Before going live, verify:

- [ ] Vercel project imported from GitHub
- [ ] Build completed successfully
- [ ] Domain added to Vercel project
- [ ] DNS A record: `76.76.21.21`
- [ ] DNS CNAME: `cname.vercel-dns.com`
- [ ] DNS propagated (check dnschecker.org)
- [ ] SSL certificate issued (green lock)
- [ ] https://easyjpgtopdf.com loads
- [ ] https://www.easyjpgtopdf.com loads
- [ ] Firebase login works
- [ ] Dashboard displays data
- [ ] Razorpay payment working
- [ ] All tools functional

---

## 🎯 Quick Deploy Commands (After Setup)

**Push changes to GitHub:**
```powershell
git add .
git commit -m "Update: description"
git push origin main
```

**Vercel auto-deploys in 1-2 minutes** ✅

---

## 🔗 Important Links

**Vercel Dashboard:**
- Project: https://vercel.com/dashboard
- Deployments: https://vercel.com/easyjpgtopdf/doctools/deployments
- Domains: https://vercel.com/easyjpgtopdf/doctools/settings/domains

**Domain Registrar:**
- GoDaddy: https://dcc.godaddy.com/domains
- Namecheap: https://www.namecheap.com/myaccount/domain-list/

**DNS Tools:**
- DNS Checker: https://dnschecker.org
- What's My DNS: https://www.whatsmydns.net
- DNS Lookup: https://mxtoolbox.com/DNSLookup.aspx

**SSL Tools:**
- SSL Checker: https://www.sslshopper.com/ssl-checker.html
- SSL Labs: https://www.ssllabs.com/ssltest/

---

## 💰 Pricing

**Vercel Free Tier:**
- ✅ Unlimited deployments
- ✅ Automatic SSL
- ✅ 100GB bandwidth/month
- ✅ Serverless functions (100GB-hours)
- ✅ Custom domain
- ✅ Global CDN

**Cost:** $0/month

**Upgrade (if needed):**
- Pro: $20/month (more bandwidth)
- Enterprise: Custom pricing

---

## 📞 Support

**Vercel Support:**
- Docs: https://vercel.com/docs
- Community: https://github.com/vercel/vercel/discussions
- Email: support@vercel.com

**DNS Help:**
- Check propagation time (usually 5-30 min)
- Clear DNS cache: `ipconfig /flushdns`
- Test from different location/network

---

## 🎉 Post-Deployment

Once live:

1. **Update README.md** with live URL
2. **Test all features** thoroughly
3. **Set up monitoring** (Vercel Analytics)
4. **Enable custom error pages** if needed
5. **Add robots.txt** for SEO
6. **Submit sitemap** to Google Search Console

**Your site will be live at:**
🌐 **https://easyjpgtopdf.com**

---

**Last Updated:** November 17, 2025
**Status:** 🚀 Ready for Production
