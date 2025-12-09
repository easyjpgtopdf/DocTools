# PDF Editor Pro - Desktop Application

Enterprise-ready desktop PDF editor built with Electron, designed for reliable text editing and future Acrobat-like features.

## Architecture

- **Main Process**: Electron main process handling file I/O and backend communication
- **Renderer Process**: React/HTML UI (currently HTML, will migrate to React)
- **Backend Integration**: Reuses existing Cloud Run service (`pdf-editor-service`)
- **Local Processing**: Simple edits processed locally when possible
- **Cloud OCR**: Uses backend `/ocr/apply` for OCR functionality

## Current Capabilities

- ✅ Open PDF files locally
- ✅ Save edited PDFs
- ✅ Basic text editing (via backend `/text/edit`)
- ✅ OCR support (via backend `/ocr/apply`)
- ✅ Search functionality
- ✅ User credits display
- ✅ Zoom controls

## Future Enhancements (Desktop Pro)

- Advanced text editing with live preview
- Watermark, Protect, Rotate, Reorder pages
- Digital signatures
- Form filling
- Annotations and comments
- Multi-page management
- Batch operations

## Setup

```bash
npm install
npm start
```

## Build

```bash
# Windows
npm run build:win

# macOS
npm run build:mac

# Linux
npm run build:linux
```

## Backend Integration

The desktop app uses the same Cloud Run backend as the web editor:
- `/session/start` - Start editing session
- `/page/render` - Render PDF page
- `/text/edit` - Edit text
- `/text/add` - Add text
- `/ocr/apply` - Apply OCR
- `/user/credits` - Check user credits

## Notes

- Currently uses HTML/JS for UI (will migrate to React/TypeScript)
- PDF processing uses backend for now (will add local PDF.js integration)
- User authentication via device fingerprint (same as web app)

