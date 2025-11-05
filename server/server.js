const express = require('express');
const cors = require('cors');
const multer = require('multer');
const os = require('os');
const path = require('path');
const fs = require('fs');
const { exec, execSync } = require('child_process');
const { v4: uuidv4 } = require('uuid');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors({ exposedHeaders: ['Content-Length', 'Content-Disposition'] }));
app.use(express.json());
app.use(express.static('public'));
app.use('/previews', express.static('previews'));
app.use('/converted', express.static('converted'));
app.use('/assets', express.static(path.join(__dirname, 'assets')));

// Multer storage to OS temp directory
const upload = multer({ storage: multer.diskStorage({
  destination: (req, file, cb) => cb(null, os.tmpdir()),
  filename: (req, file, cb) => cb(null, `${Date.now()}-${file.originalname}`)
})});

app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

// ROOT ROUTE
app.get('/', (req, res) => {
  res.json({ message: 'Word to PDF API is running!' });
});

// HEALTH ROUTE  
app.get('/api/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date() });
});

function findGhostscriptCmd() {
  if (process.platform === 'win32') {
    return 'gswin64c'; // falls back to PATH resolution
  }
  return 'gs';
}

function execAsync(cmd, opts = {}) {
  return new Promise((resolve, reject) => {
    exec(cmd, { ...opts }, (err, stdout, stderr) => {
      if (err) return reject(Object.assign(err, { stdout, stderr }));
      resolve({ stdout, stderr });
    });
  });
}

// Convert Word to HTML via LibreOffice for consistent Chrome rendering
async function convertWordToHtmlWithLibreOffice(inputPath, outDir) {
  const soffice = process.env.SOFFICE_PATH || 'soffice';
  const cmd = `"${soffice}" --headless --nologo --nofirststartwizard --convert-to html --outdir "${outDir}" "${inputPath}"`;
  await execAsync(cmd);
  const base = path.parse(inputPath).name + '.html';
  const htmlPath = path.join(outDir, base);
  if (!fs.existsSync(htmlPath)) throw new Error('LibreOffice did not produce HTML');
  return htmlPath;
}

async function convertWithLibreOffice(inputPath, outDir) {
  const soffice = process.env.SOFFICE_PATH || 'soffice';
  // LibreOffice headless conversion
  // Filter options note: font embedding is controlled by installed fonts.
  // We still rely on Ghostscript pass to force embed if available.
  const cmd = `"${soffice}" --headless --nologo --nofirststartwizard --convert-to "pdf:writer_pdf_Export" --outdir "${outDir}" "${inputPath}"`;
  await execAsync(cmd);
  // Construct expected PDF name generically for any input extension (docx, doc, rtf, odt, html, etc.)
  const base = path.parse(inputPath).name + '.pdf';
  const pdfPath = path.join(outDir, base);
  if (!fs.existsSync(pdfPath)) throw new Error('LibreOffice did not produce a PDF');
  return pdfPath;
}

async function convertWithMsWord(inputPath, outputPdf) {
  if (process.platform !== 'win32') {
    throw new Error('MS Word engine is only available on Windows');
  }
  // Use PowerShell COM Automation for Word -> PDF. Requires Microsoft Word installed.
  const ps = `
    $ErrorActionPreference = 'Stop'
    $in = '${inputPath.replace(/'/g, "''")}'
    $out = '${outputPdf.replace(/'/g, "''")}'
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    try {
      $doc = $word.Documents.Open($in, $false, $true) # ReadOnly true
      # 17 = wdExportFormatPDF
      # Export with print quality to better preserve layout
      $wdExportFormatPDF = 17
      $wdExportOptimizeForPrint = 0
      # Arg order: OutputFileName, ExportFormat, OpenAfterExport, OptimizeFor, Range, From, To, Item, IncludeDocProps, KeepIRM, CreateBookmarks, DocStructureTags, BitmapMissingFonts, UseISO19005_1
      # Use BitmapMissingFonts=$true to avoid font substitution when fonts are not installed; UseISO19005_1=$true for PDF/A-1a compatibility
      $doc.ExportAsFixedFormat($out, $wdExportFormatPDF, $false, $wdExportOptimizeForPrint, 0, 0, 0, 0, $true, $false, 1, $true, $true, $true)
      $doc.Close()
    } finally {
      $word.Quit()
    }
  `;
  const cmd = `powershell -NoProfile -ExecutionPolicy Bypass -Command "${ps.replace(/"/g, '\\"').replace(/\n/g, '; ')}"`;
  await execAsync(cmd);
  if (!fs.existsSync(outputPdf)) throw new Error('MS Word did not produce a PDF');
  return outputPdf;
}

async function forceEmbedFontsWithGhostscript(inputPdf, outputPdf) {
  const gs = findGhostscriptCmd();
  const cmd = `"${gs}" -dBATCH -dNOPAUSE -dQUIET -sDEVICE=pdfwrite -dCompatibilityLevel=1.7 -dSubsetFonts=false -dEmbedAllFonts=true -sOutputFile="${outputPdf}" "${inputPdf}"`;
  await execAsync(cmd);
  if (!fs.existsSync(outputPdf)) throw new Error('Ghostscript failed to write output');
  return outputPdf;
}

function cleanupFiles(paths) {
  for (const p of paths) {
    if (!p) continue;
    try { fs.unlinkSync(p); } catch (_) {}
  }
}

// User-provided upload storage for Word files to uploads/
const uploadsStorage = multer.diskStorage({
  destination: function (req, file, cb) {
    const uploadDir = 'uploads/';
    if (!fs.existsSync(uploadDir)) {
      fs.mkdirSync(uploadDir, { recursive: true });
    }
    cb(null, uploadDir);
  },
  filename: function (req, file, cb) {
    const uniqueName = Date.now() + '-' + Math.round(Math.random() * 1E9) + path.extname(file.originalname);
    cb(null, uniqueName);
  }
});

const uploadWord = multer({
  storage: uploadsStorage,
  fileFilter: function (req, file, cb) {
    const allowedExtensions = ['.docx', '.doc'];
    const fileExtension = path.extname(file.originalname).toLowerCase();
    if (allowedExtensions.includes(fileExtension)) cb(null, true);
    else cb(new Error('Only Word files (.docx, .doc) are allowed'));
  },
  limits: { fileSize: 100 * 1024 * 1024 }
});

// User-provided conversion using LibreOffice with UTF-8 env
function convertWordToPDF(inputPath, outputPath) {
  return new Promise((resolve, reject) => {
    const command = `soffice --headless --convert-to pdf:writer_pdf_Export --outdir "${path.dirname(outputPath)}" "${inputPath}"`;
    const env = { ...process.env, LANG: 'en_US.UTF-8', LC_ALL: 'en_US.UTF-8' };
    exec(command, { env }, (error, stdout, stderr) => {
      if (error) {
        console.error('Conversion error:', error);
        return reject(new Error(`Conversion failed: ${error.message}`));
      }
      const baseName = inputPath.replace(path.extname(inputPath), '');
      const possibleOutputs = [
        baseName + '.pdf',
        path.join(path.dirname(outputPath), path.basename(baseName) + '.pdf'),
        outputPath
      ];
      let pdfCreated = false;
      for (const possiblePath of possibleOutputs) {
        if (fs.existsSync(possiblePath)) {
          if (possiblePath !== outputPath) {
            try { fs.renameSync(possiblePath, outputPath); } catch (_) {}
          }
          pdfCreated = true; break;
        }
      }
      if (pdfCreated) resolve(outputPath);
      else reject(new Error('PDF file was not created. Check LibreOffice installation.'));
    });
  });
}

// User-provided preview generation via ImageMagick (optional)
function generatePreview(pdfPath, previewPath) {
  return new Promise((resolve) => {
    const command = `magick "${pdfPath}[0]" "${previewPath}"`;
    exec(command, (error) => {
      if (error) {
        console.log('Preview generation failed, continuing without preview...');
        return resolve(null);
      }
      resolve(previewPath);
    });
  });
}

// User-provided convert endpoint with preview and JSON response
app.post('/api/convert', uploadWord.single('wordFile'), async (req, res) => {
  let inputPath, outputPath, previewPath;
  try {
    if (!req.file) {
      return res.status(400).json({ success: false, message: 'No file uploaded. Please select a Word file.', diagnostics: { hasSoffice: hasSoffice(), chromeFound: !!findChromeCmd(), platform: process.platform } });
    }
    inputPath = req.file.path;
    const outputDir = 'converted/';
    const previewDir = 'previews/';
    const fileId = path.basename(req.file.filename, path.extname(req.file.filename));
    const outputFilename = `${fileId}.pdf`;
    const previewFilename = `${fileId}.jpg`;
    outputPath = path.join(outputDir, outputFilename);
    previewPath = path.join(previewDir, previewFilename);
    for (const dir of [outputDir, previewDir]) { if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true }); }

    // Consistent pipeline preferred: Word -> HTML (LibreOffice) -> inject unicode.css -> Chrome -> PDF
    let engineUsed = null;
    let consistentSucceeded = false;
    try {
      const chromeCmd = findChromeCmd();
      if (chromeCmd && hasSoffice()) {
        const htmlPath = await convertWordToHtmlWithLibreOffice(inputPath, outputDir);
        const injected = injectUnicodeCss(htmlPath, outputDir);
        await convertHtmlWithChrome(injected, outputPath);
        consistentSucceeded = fs.existsSync(outputPath);
        if (consistentSucceeded) engineUsed = 'chrome+libreoffice';
      }
    } catch (_) {
      consistentSucceeded = false;
    }

    if (!consistentSucceeded) {
      if (process.platform === 'win32') {
        try {
          await convertWithMsWord(inputPath, outputPath);
          engineUsed = 'msword';
        } catch (_) {
          if (hasSoffice()) {
            await convertWordToPDF(inputPath, outputPath);
            engineUsed = 'libreoffice';
          } else {
            throw new Error('No conversion engine available. Install Microsoft Word or LibreOffice.');
          }
        }
      } else if (hasSoffice()) {
        await convertWordToPDF(inputPath, outputPath);
        engineUsed = 'libreoffice';
      } else {
        throw new Error('LibreOffice not installed. Please install LibreOffice to enable conversion.');
      }
    }

  // Optimize and embed fonts using Ghostscript (ILovePDF-style quality step)
  try {
    const gsTest = findGhostscriptCmd();
    await execAsync(`"${gsTest}" -v`);
    const optimizedPath = outputPath.replace(/\.pdf$/i, '-opt.pdf');
    await forceEmbedFontsWithGhostscript(outputPath, optimizedPath);
    if (fs.existsSync(optimizedPath)) {
      try { fs.unlinkSync(outputPath); } catch (_) {}
      fs.renameSync(optimizedPath, outputPath);
    }
  } catch (_) {
    // Ghostscript not available; continue with existing PDF
  }

  let previewUrl = null;
  try { await generatePreview(outputPath, previewPath); previewUrl = `/previews/${previewFilename}`; } catch (_) {}

    res.json({
      success: true,
      message: 'File successfully converted to PDF!',
      downloadUrl: `/api/download/${outputFilename}`,
      previewUrl,
      filename: outputFilename,
      originalName: req.file.originalname.replace(path.extname(req.file.originalname), '.pdf'),
      unicodeSupported: true,
      fileInfo: { size: fs.statSync(outputPath).size, pages: 'Auto-detected' },
      engineUsed,
      diagnostics: {
        hasSoffice: hasSoffice(),
        chromeFound: !!findChromeCmd(),
        platform: process.platform
      }
    });

    setTimeout(() => {
      for (const p of [inputPath, outputPath, previewPath]) {
        if (p && fs.existsSync(p)) { try { fs.unlinkSync(p); } catch (e) {} }
      }
    }, 15 * 60 * 1000);
  } catch (error) {
    console.error('Conversion endpoint error:', error);
    for (const p of [inputPath, outputPath, previewPath]) {
      if (p && fs.existsSync(p)) { try { fs.unlinkSync(p); } catch (e) {} }
    }
    res.status(500).json({ success: false, message: `Conversion failed: ${error.message}`,
      tip: 'Install LibreOffice or Microsoft Word. If using Chrome pipeline, install Chrome/Edge.',
      diagnostics: { hasSoffice: hasSoffice(), chromeFound: !!findChromeCmd(), platform: process.platform }
    });
  }
});

// User-provided download endpoint
app.get('/api/download/:filename', (req, res) => {
  try {
    const filename = req.params.filename;
    const filePath = path.join('converted/', filename);
    if (!fs.existsSync(filePath)) return res.status(404).json({ success: false, message: 'File not found' });
    const disposition = (req.query.disposition || '').toLowerCase() === 'inline' ? 'inline' : 'attachment';
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', `${disposition}; filename="${filename}"`);
    res.setHeader('Cache-Control', 'no-cache');
    fs.createReadStream(filePath).pipe(res);
  } catch (error) {
    console.error('Download error:', error);
    res.status(500).json({ success: false, message: 'Download failed: ' + error.message });
  }
});

// User-provided error handler
app.use((error, req, res, next) => {
  console.error('Server error:', error);
  if (error instanceof multer.MulterError && error.code === 'LIMIT_FILE_SIZE') {
    return res.status(400).json({ success: false, message: 'File size too large. Maximum 100MB allowed.' });
  }
  res.status(500).json({ success: false, message: error.message || 'Internal server error' });
});

function findChromeCmd() {
  const candidates = process.platform === 'win32'
    ? [
        'chrome',
        'chrome.exe',
        'C:/Program Files/Google/Chrome/Application/chrome.exe',
        'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
        'msedge',
        'msedge.exe',
        'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
        'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
      ]
    : ['google-chrome', 'chromium', 'chrome', 'msedge'];
  return candidates.find(c => {
    try { return !!execSyncCheck(c); } catch (_) { return false; }
  });
}

function execSyncCheck(cmd) {
  try {
    execSync(`${cmd} --version`, { stdio: 'ignore' });
    return true;
  } catch (_) {
    return false;
  }
}

function hasSoffice() {
  const candidate = process.env.SOFFICE_PATH || 'soffice';
  try {
    execSync(`${candidate} --version`, { stdio: 'ignore' });
    return true;
  } catch (_) {
    return false;
  }
}

async function convertHtmlWithChrome(inputPath, outputPdf) {
  const chrome = findChromeCmd();
  if (!chrome) throw new Error('No Chrome/Edge found for HTML rendering');
  const fileUrl = 'file:///' + inputPath.replace(/\\/g, '/');
  const cmd = `"${chrome}" --headless --disable-gpu --no-first-run --no-default-browser-check --print-to-pdf="${outputPdf}" "${fileUrl}"`;
  await execAsync(cmd);
  if (!fs.existsSync(outputPdf)) throw new Error('Chrome did not produce a PDF');
  return outputPdf;
}

function injectUnicodeCss(htmlPath, workDir) {
  try {
    const raw = fs.readFileSync(htmlPath, 'utf8');
    const linkTag = `<link rel="stylesheet" href="http://localhost:${PORT}/assets/unicode.css">`;
    let out;
    if (/<head[\s>]/i.test(raw)) {
      out = raw.replace(/<head(\s*[^>]*)>/i, (m) => m + `\n  ${linkTag}`);
    } else if (/<html[\s>]/i.test(raw)) {
      out = raw.replace(/<html(\s*[^>]*)>/i, (m) => m + `\n<head>\n  <meta charset="utf-8">\n  ${linkTag}\n</head>`);
    } else {
      out = `<!doctype html>\n<html>\n<head>\n  <meta charset="utf-8">\n  ${linkTag}\n</head>\n<body>\n${raw}\n</body>\n</html>`;
    }
    const outPath = path.join(workDir, 'unicode_injected.html');
    fs.writeFileSync(outPath, out, 'utf8');
    return outPath;
  } catch (e) {
    return htmlPath; // fallback without injection
  }
}

app.post('/convert/word-to-pdf', upload.any(), async (req, res) => {
  const files = req.files || [];
  const file = files.find(f => f.fieldname === 'file') || files.find(f => f.fieldname === 'files') || files[0];
  if (!file) return res.status(400).json({ error: 'No file uploaded (expected field name "file" or "files")' });

  const workId = uuidv4();
  const workDir = path.join(os.tmpdir(), `easyjpgtopdf-${workId}`);
  fs.mkdirSync(workDir, { recursive: true });

  let producedPdf = null;
  let gsPdf = null;

  try {
    const ext = (path.extname(file.originalname || '').toLowerCase() || '').replace('.', '');
    const requestedEngine = (req.query.engine || '').toLowerCase();
    const isWordFamily = ['docx','doc','rtf','odt'].includes(ext);
    const isHtml = ['html','htm'].includes(ext);
    let engine = requestedEngine;
    if (!engine) {
      // Prefer Chrome for HTML rendering (better Unicode/webfont fidelity), else Word on Windows for Word docs
      if (isHtml && findChromeCmd()) engine = 'chrome';
      else if (process.platform === 'win32' && isWordFamily) engine = 'msword';
      else engine = 'libreoffice';
    }

    let pdfPath;
    if (engine === 'msword') {
      const out = path.join(workDir, path.parse(file.originalname || 'document').name + '.pdf');
      try {
        pdfPath = await convertWithMsWord(file.path, out);
      } catch (e) {
        // Fallback to LibreOffice if MS Word path fails
        pdfPath = await convertWithLibreOffice(file.path, workDir);
      }
    } else if (engine === 'chrome') {
      const out = path.join(workDir, path.parse(file.originalname || 'document').name + '.pdf');
      try {
        const inputForChrome = isHtml ? injectUnicodeCss(file.path, workDir) : file.path;
        pdfPath = await convertHtmlWithChrome(inputForChrome, out);
      } catch (e) {
        // Fallback to LibreOffice if Chrome path fails
        pdfPath = await convertWithLibreOffice(file.path, workDir);
      }
    } else {
      pdfPath = await convertWithLibreOffice(file.path, workDir);
    }
    producedPdf = pdfPath;

    // Try Ghostscript to force-embed fonts if available
    try {
      const testGs = findGhostscriptCmd();
      await execAsync(`"${testGs}" -v`);
      const gsOut = path.join(workDir, 'embedded.pdf');
      await forceEmbedFontsWithGhostscript(producedPdf, gsOut);
      gsPdf = gsOut;
    } catch (e) {
      // Ghostscript not installed or failed; continue with LO output
    }

    const finalPdf = gsPdf || producedPdf;
    const outName = path.parse(file.originalname || 'document').name + '.pdf';

    try {
      const stat = fs.statSync(finalPdf);
      const disposition = (req.query.disposition || '').toLowerCase() === 'inline' ? 'inline' : 'attachment';
      const headers = {
        'Content-Type': 'application/pdf',
        'Content-Length': stat.size,
        'Cache-Control': 'no-store',
      };

      if (disposition === 'attachment') {
        res.download(finalPdf, outName, (err) => {
          // cleanup async after response ends
          setTimeout(() => {
            cleanupFiles([file.path, producedPdf, gsPdf]);
            try { fs.rmSync(workDir, { recursive: true, force: true }); } catch (_) {}
          }, 1000);
          if (err) {
            try { return res.status(500).end('Failed to send PDF'); } catch (_) {}
          }
        });
      } else {
        res.set(headers);
        res.setHeader('Content-Disposition', `inline; filename="${outName}"`);
        res.sendFile(path.resolve(finalPdf), (err) => {
          setTimeout(() => {
            cleanupFiles([file.path, producedPdf, gsPdf]);
            try { fs.rmSync(workDir, { recursive: true, force: true }); } catch (_) {}
          }, 1000);
          if (err) {
            try { return res.status(500).end('Failed to send PDF'); } catch (_) {}
          }
        });
      }
    } catch (e) {
      return res.status(500).json({ error: 'Failed to prepare PDF response', details: String(e && e.message || e) });
    }
  } catch (err) {
    console.error('Conversion error:', err);
    cleanupFiles([file.path]);
    try { fs.rmSync(workDir, { recursive: true, force: true }); } catch (_) {}
    res.status(500).json({ error: 'Conversion failed', details: String(err && err.message || err) });
  }
});

// Explicit MS Word endpoint for clarity
app.post('/convert/word-to-pdf/msword', upload.any(), async (req, res) => {
  req.query.engine = 'msword';
  return app._router.handle(req, res, () => {});
});

app.listen(PORT, () => {
  console.log(`Word2PDF server listening on http://localhost:${PORT}`);
});



