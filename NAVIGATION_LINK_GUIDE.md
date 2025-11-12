# Navigation Link Kaise Add Karein - Simple Guide

## 🎯 Kahan Edit Karna Hai

**File Location:** `js/global-components.js`

Ye ek hi file hai jisko edit karna hai. Sabhi pages me automatic update ho jayega!

---

## 📝 Example 1: Naya Link "Convert to PDF" Menu Me Add Karna

### Before (Line 19-24):
```javascript
<div class="dropdown-content">
    <a href="jpg-to-pdf.html">JPG to PDF</a>
    <a href="word-to-pdf.html">Word to PDF</a>
    <a href="excel-to-pdf.html">Excel to PDF</a>
    <a href="ppt-to-pdf.html">PowerPoint to PDF</a>
</div>
```

### After (Naya link add kiya):
```javascript
<div class="dropdown-content">
    <a href="jpg-to-pdf.html">JPG to PDF</a>
    <a href="word-to-pdf.html">Word to PDF</a>
    <a href="excel-to-pdf.html">Excel to PDF</a>
    <a href="ppt-to-pdf.html">PowerPoint to PDF</a>
    <a href="png-to-pdf.html">PNG to PDF</a>     <!-- 👈 Naya link -->
</div>
```

---

## 📝 Example 2: Naya Menu Add Karna (Complete Dropdown)

### Kaha Add Karna Hai:
Line 70 ke baad (Other Tools dropdown ke baad)

```javascript
<div class="dropdown">
    <a href="#">Other Tools <i class="fas fa-chevron-down"></i></a>
    <div class="dropdown-content">
        <a href="excel-unlocker/" target="_blank">Excel Unlocker</a>
        <a href="protect-excel.html">Protect Excel Sheet</a>
    </div>
</div>
<!-- 👇 Yahaan naya menu add karo -->
<div class="dropdown">
    <a href="#">SEO Tools <i class="fas fa-chevron-down"></i></a>
    <div class="dropdown-content">
        <a href="keyword-tool.html">Keyword Tool</a>
        <a href="meta-tag-generator.html">Meta Tag Generator</a>
        <a href="sitemap-generator.html">Sitemap Generator</a>
    </div>
</div>
```

---

## 📝 Example 3: Footer Me Link Add Karna

### File: Same `js/global-components.js`
### Location: Line 150-160 (Footer section)

### Before:
```javascript
<div class="footer-section">
    <h3>Popular Tools</h3>
    <ul>
        <li><a href="jpg-to-pdf.html">JPG to PDF</a></li>
        <li><a href="pdf-to-jpg.html">PDF to JPG</a></li>
    </ul>
</div>
```

### After (Naya link add kiya):
```javascript
<div class="footer-section">
    <h3>Popular Tools</h3>
    <ul>
        <li><a href="jpg-to-pdf.html">JPG to PDF</a></li>
        <li><a href="pdf-to-jpg.html">PDF to JPG</a></li>
        <li><a href="new-tool.html">New Tool</a></li>  <!-- 👈 Naya link -->
    </ul>
</div>
```

---

## 🚀 Step-by-Step Process

### Step 1: File Open Karo
```
Path: C:\Users\apnao\Downloads\DocTools\js\global-components.js
```
VS Code me ya kisi bhi editor me open karo.

### Step 2: Line Number Find Karo
- **Header Links:** Line 10-80
- **Footer Links:** Line 85-170

### Step 3: Copy-Paste Pattern
Existing link ko copy karo aur modify karo:
```javascript
<a href="your-page.html">Your Page Name</a>
```

### Step 4: Save File
Ctrl+S ya File → Save

### Step 5: Git Commit
```powershell
cd C:\Users\apnao\Downloads\DocTools
git add js/global-components.js
git commit -m "feat: add new navigation link to header/footer"
git push
```

---

## ✅ Common Patterns

### Single Link (Dropdown ke andar):
```javascript
<a href="page-name.html">Display Name</a>
```

### Complete Dropdown Menu:
```javascript
<div class="dropdown">
    <a href="#">Menu Name <i class="fas fa-chevron-down"></i></a>
    <div class="dropdown-content">
        <a href="link1.html">Link 1</a>
        <a href="link2.html">Link 2</a>
    </div>
</div>
```

### External Link (New Tab):
```javascript
<a href="https://example.com" target="_blank">External Link</a>
```

### Footer List Item:
```javascript
<li><a href="page.html">Page Name</a></li>
```

---

## 🎨 Icons Add Karna (Optional)

```javascript
<a href="page.html"><i class="fas fa-file-pdf"></i> PDF Tool</a>
```

Common Icons:
- `fa-file-pdf` - PDF icon
- `fa-image` - Image icon
- `fa-edit` - Edit icon
- `fa-compress` - Compress icon
- `fa-lock` - Lock/Protect icon

---

## ⚠️ Important Notes

1. **Spelling:** File name exactly match hona chahiye
   - ✅ `jpg-to-pdf.html`
   - ❌ `jpg to pdf.html` (space nahi)

2. **Quotes:** Use double quotes `"` for attributes
   - ✅ `href="page.html"`
   - ❌ `href='page.html'`

3. **Closing Tags:** Always close tags properly
   - ✅ `<a href="...">Text</a>`
   - ❌ `<a href="...">Text` (missing `</a>`)

4. **Indentation:** Keep proper spacing for readability

---

## 🧪 Testing

1. Save file
2. Browser me page refresh karo (Ctrl+F5)
3. Check karo:
   - ✅ Naya link dikhe
   - ✅ Click karne par work kare
   - ✅ All pages me same link dikhe

---

## 🆘 Agar Problem Aaye

1. **Link nahi dikh raha:**
   - Check `global-components.js` saved hai
   - Browser cache clear karo (Ctrl+Shift+Delete)

2. **Link work nahi kar raha:**
   - File name check karo
   - Spelling check karo

3. **Revert karna hai:**
   ```powershell
   git checkout js/global-components.js
   ```

---

## 📞 Need Help?

Mujhe batao kya add karna hai:
1. Link ka naam?
2. File ka naam?
3. Kahan add karna hai (Header ya Footer)?

Main exact code likh dunga! 🚀
