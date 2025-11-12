# Global Header & Footer System - Implementation Guide

## 🎯 Purpose
Centrally manage header and footer across all HTML pages for consistency and easy updates.

## 📁 Files Created

### 1. `js/global-components.js`
- Contains global header and footer HTML
- Dynamically injects header/footer into pages
- Highlights active page link
- Auto-initializes on page load

### 2. `scripts/add-global-components.ps1`
- PowerShell script to automate integration
- Replaces existing headers/footers with placeholders
- Adds required CSS/JS links
- Creates backups before modification

## 🚀 How to Use

### Step 1: Run the PowerShell Script
```powershell
cd C:\Users\apnao\Downloads\DocTools
.\scripts\add-global-components.ps1
```

This will:
- ✅ Backup all HTML files
- ✅ Replace `<header>` with `<div id="global-header-placeholder"></div>`
- ✅ Replace `<footer>` with `<div id="global-footer-placeholder"></div>`
- ✅ Add `<script src="js/global-components.js"></script>` before `</body>`
- ✅ Add CSS links: `header.css` and `footer.css`

### Step 2: Verify Changes
Test a few pages:
- `index.html`
- `jpg-to-pdf.html`
- `dashboard.html`

Check that:
1. Header displays correctly
2. Footer displays correctly
3. Current page link is highlighted
4. User menu works (if logged in)

### Step 3: Commit to Git
```powershell
git add js/global-components.js scripts/add-global-components.ps1
git add *.html
git commit -m "feat: implement centralized global header/footer system"
git push
```

## 🔄 Future Updates

### To Update Header Across All Pages:
1. Edit `js/global-components.js` → `globalHeaderHTML` variable
2. Save file
3. All pages will automatically use new header on next load

### To Update Footer Across All Pages:
1. Edit `js/global-components.js` → `globalFooterHTML` variable
2. Save file
3. All pages will automatically use new footer on next load

### To Add New Page:
Just include this in your HTML:
```html
<head>
    <link rel="stylesheet" href="css/header.css">
    <link rel="stylesheet" href="css/footer.css">
</head>
<body>
    <div id="global-header-placeholder"></div>
    
    <!-- Your page content here -->
    
    <div id="global-footer-placeholder"></div>
    <script src="js/global-components.js"></script>
</body>
```

## 📋 Current Header Features

- Logo with home link
- Navigation dropdowns:
  - Convert to PDF
  - Convert from PDF
  - PDF Editor
  - Image Tools
  - Design Tools
  - Other Tools
- Auth buttons (Sign In, Signup)
- User menu (when logged in)
  - Account Dashboard
  - Billing Details
  - Payment History
  - Orders & Subscriptions
  - Account Center
  - Sign out

## 📋 Current Footer Features

- About section with social links
- Quick Links
- Popular Tools
- Legal links
- Support links
- Copyright notice

## ⚡ Benefits

1. **Single Source of Truth**: Update once, reflects everywhere
2. **Consistency**: All pages have identical header/footer
3. **Easy Maintenance**: No need to edit 50+ HTML files
4. **Active Link Highlighting**: Current page automatically highlighted
5. **Backward Compatible**: Works with existing auth system
6. **No Build Process**: Pure JavaScript, works immediately

## 🔧 Troubleshooting

### Header/Footer Not Showing?
- Check browser console for errors
- Verify `global-components.js` is loaded
- Ensure placeholders exist in HTML

### CSS Not Applied?
- Verify `header.css` and `footer.css` are linked in `<head>`
- Check file paths are correct

### To Revert Changes:
```powershell
# Copy from backup directory created by script
$backupDir = "backups\html-backup-YYYYMMDD-HHMMSS"
Copy-Item "$backupDir\*.html" . -Force
```

## 📊 Status

- ✅ Global components system created
- ✅ PowerShell automation script ready
- ⏳ Awaiting execution on HTML files
- ⏳ Testing required
- ⏳ Git commit pending

## 🎨 Customization

Edit these variables in `js/global-components.js`:
- `globalHeaderHTML` - Header structure
- `globalFooterHTML` - Footer structure
- Add/remove navigation items
- Update links and labels
- Modify styling via CSS files
