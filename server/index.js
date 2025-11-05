const express = require('express');
const cors = require('cors');
const multer = require('multer');
const fs = require('fs');
const path = require('path');
const { v4: uuidv4 } = require('uuid');
const PDFLib = require('pdf-lib');
const pdfjsLib = require('pdfjs-dist');
const { createCanvas } = require('canvas');

pdfjsLib.GlobalWorkerOptions.workerSrc = require('pdfjs-dist/build/pdf.worker.js');

const app = express();
app.use(cors());
app.use(express.json({ limit: '25mb' }));

const UPLOAD_DIR = path.join(__dirname, 'uploads');
const FONT_DIR = path.join(__dirname, 'fonts');
if (!fs.existsSync(UPLOAD_DIR)) fs.mkdirSync(UPLOAD_DIR, { recursive: true });

// Render a page server-side to PNG
app.get('/api/page-image', async (req, res) => {
  try{
    const { docId, page: pageStr } = req.query;
    const pageNum = parseInt(pageStr || '1', 10);
    const files = fs.readdirSync(UPLOAD_DIR).filter(f => f.startsWith(docId));
    if (!files.length) return res.status(404).json({ error: 'Doc not found' });
    const data = new Uint8Array(fs.readFileSync(path.join(UPLOAD_DIR, files[0])));
    const loadingTask = pdfjsLib.getDocument({ data });
    const doc = await loadingTask.promise;
    const page = await doc.getPage(pageNum);
    const viewport = page.getViewport({ scale: 1.0 });
    const canvas = createCanvas(Math.ceil(viewport.width), Math.ceil(viewport.height));
    const ctx = canvas.getContext('2d');
    await page.render({ canvasContext: ctx, viewport }).promise;
    const buf = canvas.toBuffer('image/png');
    res.setHeader('Content-Type', 'image/png');
    res.send(buf);
  }catch(e){
    console.error(e);
    res.status(500).json({ error: 'page-image failed' });
  }
});
if (!fs.existsSync(FONT_DIR)) fs.mkdirSync(FONT_DIR, { recursive: true });

const storage = multer.diskStorage({
  destination: (_, __, cb) => cb(null, UPLOAD_DIR),
  filename: (_, file, cb) => cb(null, uuidv4() + path.extname(file.originalname || '.pdf')),
});
const upload = multer({ storage });

// In-memory font store: key -> Uint8Array
const fontStore = Object.create(null);

app.post('/api/upload', upload.single('file'), async (req, res) => {
  try {
    if (!req.file) return res.status(400).json({ error: 'No file' });
    const filePath = path.join(UPLOAD_DIR, req.file.filename);
    const data = new Uint8Array(fs.readFileSync(filePath));
    const loadingTask = pdfjsLib.getDocument({ data });
    const doc = await loadingTask.promise;
    const pageCount = doc.numPages;
    const docId = path.parse(req.file.filename).name; // without ext
    res.json({ docId, pageCount });
  } catch (e) {
    console.error(e);
    res.status(500).json({ error: 'Upload failed' });
  }
});

app.get('/api/textlayer', async (req, res) => {
  try {
    const { docId, page: pageStr } = req.query;
    const pageNum = parseInt(pageStr || '1', 10);
    const files = fs.readdirSync(UPLOAD_DIR).filter(f => f.startsWith(docId));
    if (!files.length) return res.status(404).json({ error: 'Doc not found' });
    const data = new Uint8Array(fs.readFileSync(path.join(UPLOAD_DIR, files[0])));
    const loadingTask = pdfjsLib.getDocument({ data });
    const doc = await loadingTask.promise;
    const page = await doc.getPage(pageNum);
    const vp = page.getViewport({ scale: 1.0 });
    const textContent = await page.getTextContent();
    const items = textContent.items.map(it => ({
      str: it.str,
      transform: it.transform,
      width: it.width,
      dir: it.dir,
      height: it.height,
      fontName: it.fontName,
    }));
    res.json({ width: vp.width, height: vp.height, items });
  } catch (e) {
    console.error(e);
    res.status(500).json({ error: 'textlayer failed' });
  }
});

app.post('/api/add-font', upload.single('font'), async (req, res) => {
  try {
    if (!req.file) return res.status(400).json({ error: 'No font' });
    const key = path.parse(req.file.originalname || req.file.filename).name.toLowerCase();
    const buf = fs.readFileSync(req.file.path);
    fontStore[key] = new Uint8Array(buf);
    res.json({ key });
  } catch (e) {
    console.error(e);
    res.status(500).json({ error: 'add-font failed' });
  }
});

app.post('/api/save', async (req, res) => {
  try {
    const { docId, edits, metrics } = req.body || {};
    if (!docId || !Array.isArray(edits)) return res.status(400).json({ error: 'Bad payload' });
    const files = fs.readdirSync(UPLOAD_DIR).filter(f => f.startsWith(docId));
    if (!files.length) return res.status(404).json({ error: 'Doc not found' });
    const bytes = fs.readFileSync(path.join(UPLOAD_DIR, files[0]));
    const pdf = await PDFLib.PDFDocument.load(bytes);

    // font cache per doc
    const cache = {};
    async function getFont(family) {
      const key = (family || 'Helvetica').toLowerCase();
      if (cache[key]) return cache[key];
      if (fontStore[key]) {
        cache[key] = await pdf.embedFont(fontStore[key], { subset: true });
        return cache[key];
      }
      const std = PDFLib.StandardFonts;
      let pref = std.Helvetica;
      if (key.includes('times')) pref = std.TimesRoman; else if (key.includes('courier')) pref = std.Courier;
      cache[key] = await pdf.embedFont(pref);
      return cache[key];
    }

    edits.forEach(ed => {
      const page = pdf.getPage((ed.page || 1) - 1);
      if (!page) return;
      // client supplies x,y in PDF units already
      // ed: { page, x, y, text, size, color, family }
      // color as hex
      const rgb = hex01(ed.color || '#111827');
      // draw text line as-is; for multi-line, client sends multiple edits
      // ensure font is awaited synchronously (queue work then run after loop)
    });

    // draw sequentially to preserve await
    for (const ed of edits) {
      const page = pdf.getPage((ed.page || 1) - 1);
      if (!page) continue;
      const font = await getFont(ed.family);
      const size = ed.size || 12;
      const rgb = hex01(ed.color || '#111827');
      page.drawText(ed.text || '', {
        x: ed.x || 0, y: ed.y || 0, font, size,
        color: PDFLib.rgb(rgb.r, rgb.g, rgb.b),
      });
    }

    const out = await pdf.save();
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', 'attachment; filename="edited.pdf"');
    res.send(Buffer.from(out));
  } catch (e) {
    console.error(e);
    res.status(500).json({ error: 'save failed' });
  }
});

function hex01(hex) {
  const m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex || '#111827');
  return { r: parseInt(m[1], 16) / 255, g: parseInt(m[2], 16) / 255, b: parseInt(m[3], 16) / 255 };
}

const PORT = process.env.PORT || 5600;
app.listen(PORT, () => console.log('PDF server running on http://localhost:' + PORT));



