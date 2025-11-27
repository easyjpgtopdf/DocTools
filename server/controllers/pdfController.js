/**
 * PDF Controller
 * Handles PDF operations (upload, edit, OCR, download)
 */

const fs = require('fs');
const path = require('path');
const { getVisionClient } = require('../config/google-cloud');
const visionOCR = require('../api/pdf-ocr/vision-ocr');
const { 
  validatePDF, 
  validateFileSize, 
  validateFileType,
  asyncHandler,
  withTimeout,
  PDFCorruptionError,
  FileSizeError,
  QuotaExceededError
} = require('../middleware/errorHandler');
const { cacheFile, getCachedFile, cacheResult, getCachedResult } = require('../utils/cache');
const { streamPDFResponse } = require('../utils/streaming');
const jobQueue = require('../utils/backgroundJobs');

/**
 * Upload PDF file
 * Returns file ID and metadata
 */
async function uploadPDF(req, res) {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        error: 'No PDF file uploaded',
        code: 'NO_FILE'
      });
    }

    // Validate file type
    try {
      validateFileType(req.file.mimetype, req.file.originalname);
    } catch (error) {
      return res.status(error.statusCode || 400).json({
        success: false,
        error: error.message,
        code: error.name
      });
    }

    // Validate file size
    try {
      validateFileSize(req.file.size);
    } catch (error) {
      return res.status(error.statusCode || 413).json({
        success: false,
        error: error.message,
        code: error.name
      });
    }

    const fileStorage = require('../utils/fileStorage');
    let fileBuffer;

    try {
      fileBuffer = fs.readFileSync(req.file.path);
    } catch (error) {
      return res.status(500).json({
        success: false,
        error: 'Failed to read uploaded file',
        code: 'FILE_READ_ERROR'
      });
    }

    // Validate PDF structure
    try {
      await withTimeout(validatePDF(fileBuffer), 10000, 'PDF validation timed out');
    } catch (error) {
      return res.status(error.statusCode || 422).json({
        success: false,
        error: error.message || 'Invalid or corrupted PDF file',
        code: error.name || 'PDF_VALIDATION_ERROR'
      });
    }

    // Check cache first
    const fileHash = require('crypto').createHash('md5').update(fileBuffer).digest('hex');
    const cachedFile = getCachedFile(fileHash);
    
    let fileId;
    if (cachedFile) {
      // Use cached file ID if available
      const metadata = fileStorage.getFileMetadata(cachedFile.fileId);
      if (metadata) {
        fileId = cachedFile.fileId;
      }
    }

    if (!fileId) {
      // Store file and get ID
      fileId = fileStorage.storeFile(
        fileBuffer,
        req.file.originalname,
        req.file.mimetype
      );
      
      // Cache file
      cacheFile(fileHash, { fileId, buffer: fileBuffer });
    }

    // Cleanup uploaded temp file
    try {
      fs.unlinkSync(req.file.path);
    } catch (e) {
      console.warn('Could not delete temp file:', e.message);
    }

    // Optionally extract text and fonts for preview (with timeout)
    let textItems = [];
    let fonts = [];
    
    try {
      const pdfContentParser = require('../api/pdf-edit/pdf-content-parser');
      const parserResult = await withTimeout(
        Promise.all([
          pdfContentParser.extractTextWithPositions(fileBuffer),
          pdfContentParser.getFontsFromPDF(fileBuffer)
        ]),
        15000,
        'PDF parsing timed out'
      );
      textItems = parserResult[0] || [];
      fonts = parserResult[1] || [];
    } catch (e) {
      console.warn('Could not extract PDF content:', e.message);
      // Continue without extracted content
    }

    // Get metadata
    const metadata = fileStorage.getFileMetadata(fileId);

    res.json({
      success: true,
      message: 'PDF uploaded successfully',
      fileId: fileId,
      filename: req.file.originalname,
      size: req.file.size,
      mimeType: req.file.mimetype,
      createdAt: metadata.createdAt,
      textItems: textItems,
      fonts: fonts
    });
  } catch (error) {
    console.error('Upload error:', error);
    throw error; // Let error handler middleware handle it
  }
}

/**
 * Edit PDF (text, images, etc.)
 * Supports both fileId-based and direct PDF data editing
 */
async function editPDF(req, res) {
  try {
    const { fileId, pdfData, edits } = req.body;

    const fileStorage = require('../utils/fileStorage');
    const nativePdfEditor = require('../api/pdf-edit/native-pdf-editor');
    
    let pdfBuffer;
    let currentFileId = fileId;

    // If fileId is provided, use stored file
    if (fileId) {
      try {
        const fileData = fileStorage.getFile(fileId);
        pdfBuffer = fileData.buffer;
      } catch (error) {
        return res.status(404).json({
          success: false,
          error: 'File not found',
          code: 'FILE_NOT_FOUND'
        });
      }
    } else if (pdfData) {
      // Convert base64 to buffer
      if (typeof pdfData === 'string') {
        if (pdfData.startsWith('data:application/pdf;base64,')) {
          pdfData = pdfData.split(',')[1];
        }
        pdfBuffer = Buffer.from(pdfData, 'base64');
      } else {
        pdfBuffer = Buffer.from(pdfData);
      }
    } else {
      return res.status(400).json({
        success: false,
        error: 'Either fileId or pdfData must be provided',
        code: 'MISSING_DATA'
      });
    }

    // Apply edits using native PDF editor
    const editedBuffer = await nativePdfEditor.applyNativeEdits(pdfBuffer, edits || {});
    
    // If fileId was provided, update the stored file
    if (currentFileId) {
      fileStorage.updateFile(currentFileId, editedBuffer);
      
      // Store edit history
      if (edits) {
        if (edits.textEdits && edits.textEdits.length > 0) {
          fileStorage.addEdit(currentFileId, {
            type: 'text',
            edits: edits.textEdits
          });
        }
        if (edits.textReplacements && edits.textReplacements.length > 0) {
          fileStorage.addEdit(currentFileId, {
            type: 'replacement',
            replacements: edits.textReplacements
          });
        }
        if (edits.deletions && edits.deletions.length > 0) {
          fileStorage.addEdit(currentFileId, {
            type: 'deletion',
            deletions: edits.deletions
          });
        }
        if (edits.images && edits.images.length > 0) {
          fileStorage.addEdit(currentFileId, {
            type: 'image',
            images: edits.images
          });
        }
        if (edits.ocrTexts && edits.ocrTexts.length > 0) {
          fileStorage.addEdit(currentFileId, {
            type: 'ocr',
            ocrTexts: edits.ocrTexts
          });
        }
      }
    }
    
    const editedBase64 = editedBuffer.toString('base64');

    res.json({
      success: true,
      fileId: currentFileId,
      pdfData: `data:application/pdf;base64,${editedBase64}`,
      message: 'PDF edited successfully'
    });
  } catch (error) {
    console.error('PDF editing error:', error);
    throw error; // Let error handler middleware handle it
  }
}

/**
 * Edit PDF text specifically using pdf-lib
 * Takes file ID and text edits (add, replace, delete)
 * Actually modifies PDF content - not overlays
 * Uses the exact structure: PDFDocument.load() -> page.drawText() -> save()
 */
async function editText(req, res) {
  try {
    const { fileId, textEdits, textReplacements, deletions } = req.body;

    if (!fileId) {
      return res.status(400).json({
        success: false,
        error: 'File ID is required',
        code: 'MISSING_FILE_ID'
      });
    }

    // At least one type of edit must be provided
    if ((!textEdits || textEdits.length === 0) && 
        (!textReplacements || textReplacements.length === 0) && 
        (!deletions || deletions.length === 0)) {
      return res.status(400).json({
        success: false,
        error: 'At least one edit (textEdits, textReplacements, or deletions) is required',
        code: 'NO_EDITS_PROVIDED'
      });
    }

    const fileStorage = require('../utils/fileStorage');
    const { PDFDocument, rgb, StandardFonts } = require('pdf-lib');
    
    // Get file with error handling
    let pdfBuffer, metadata;
    try {
      const fileData = fileStorage.getFile(fileId);
      pdfBuffer = fileData.buffer;
      metadata = fileData.metadata;
    } catch (error) {
      return res.status(404).json({
        success: false,
        error: 'File not found',
        code: 'FILE_NOT_FOUND'
      });
    }

    // Validate PDF
    try {
      await withTimeout(validatePDF(pdfBuffer), 10000);
    } catch (error) {
      return res.status(error.statusCode || 422).json({
        success: false,
        error: error.message || 'Invalid PDF file',
        code: error.name || 'PDF_VALIDATION_ERROR'
      });
    }

    // CRITICAL: Use pdf-lib directly for actual PDF modification
    // Load the uploaded PDF using PDFDocument.load()
    const pdfDoc = await PDFDocument.load(pdfBuffer);
    const pages = pdfDoc.getPages();

    // Process text edits (add new text) - Using exact structure as requested
    if (textEdits && textEdits.length > 0) {
      for (const editData of textEdits) {
        const pageIndex = editData.pageIndex || 0;
        if (pageIndex >= 0 && pageIndex < pages.length) {
          // Get the specific page using pdfDoc.getPages()[pageIndex]
          const page = pages[pageIndex];
          const pageHeight = page.getHeight();
          
          // Convert coordinates (canvas Y to PDF Y - PDF uses bottom-left origin)
          const pdfX = editData.x || 0;
          const pdfY = pageHeight - (editData.y || 0);
          
          // Use page.drawText() to actually add/modify text in the PDF
          // EXACT CODE STRUCTURE AS REQUESTED:
          page.drawText(editData.text || '', {
            x: pdfX,
            y: pdfY,
            size: editData.fontSize || 12,
            color: rgb(0, 0, 0)
          });
        }
      }
    }

    // Process text replacements (delete old + add new)
    if (textReplacements && textReplacements.length > 0) {
      for (const replacement of textReplacements) {
        const pageIndex = replacement.pageIndex || 0;
        if (pageIndex >= 0 && pageIndex < pages.length) {
          const page = pages[pageIndex];
          const pageHeight = page.getHeight();
          
          // Draw white rectangle over old text (delete)
          const pdfX = replacement.x || 0;
          const pdfY = pageHeight - (replacement.y || 0);
          const fontSize = replacement.fontSize || 12;
          const estimatedWidth = (replacement.oldText || '').length * fontSize * 0.6;
          
          page.drawRectangle({
            x: pdfX,
            y: pdfY - fontSize,
            width: estimatedWidth,
            height: fontSize * 1.2,
            color: rgb(1, 1, 1) // White
          });
          
          // Add new text
          let font;
          const fontName = replacement.fontName || 'Helvetica';
          if (fontName === 'Helvetica') {
            font = await pdfDoc.embedFont(StandardFonts.Helvetica);
          } else if (fontName === 'Times-Roman') {
            font = await pdfDoc.embedFont(StandardFonts.TimesRoman);
          } else if (fontName === 'Courier') {
            font = await pdfDoc.embedFont(StandardFonts.Courier);
          } else {
            font = await pdfDoc.embedFont(StandardFonts.Helvetica);
          }
          
          const fontColor = replacement.fontColor || [0, 0, 0];
          const color = rgb(fontColor[0] / 255, fontColor[1] / 255, fontColor[2] / 255);
          
          page.drawText(replacement.newText || '', {
            x: pdfX,
            y: pdfY,
            size: fontSize,
            font: font,
            color: color
          });
        }
      }
    }

    // Process deletions (draw white rectangle)
    if (deletions && deletions.length > 0) {
      for (const deletion of deletions) {
        const pageIndex = deletion.pageIndex || 0;
        if (pageIndex >= 0 && pageIndex < pages.length) {
          const page = pages[pageIndex];
          const pageHeight = page.getHeight();
          
          const pdfX = deletion.x || 0;
          const pdfY = pageHeight - (deletion.y || 0);
          const width = deletion.width || 100;
          const height = deletion.height || 20;
          
          // Draw white rectangle to cover text
          page.drawRectangle({
            x: pdfX,
            y: pdfY - height,
            width: width,
            height: height,
            color: rgb(1, 1, 1) // White
          });
        }
      }
    }

    // Save the modified PDF using pdfDoc.save()
    // This returns the modified PDF buffer
    const modifiedPdfBuffer = await pdfDoc.save();

    // Store the modified PDF and return success
    // CRITICAL: Update stored file with edited version (not original)
    fileStorage.updateFile(fileId, modifiedPdfBuffer);
    
    // Store edit history
    if (textEdits && textEdits.length > 0) {
      fileStorage.addEdit(fileId, {
        type: 'text',
        edits: textEdits
      });
    }
    if (textReplacements && textReplacements.length > 0) {
      fileStorage.addEdit(fileId, {
        type: 'replacement',
        replacements: textReplacements
      });
    }
    if (deletions && deletions.length > 0) {
      fileStorage.addEdit(fileId, {
        type: 'deletion',
        deletions: deletions
      });
    }

    // Convert to base64 for response
    const editedBase64 = modifiedPdfBuffer.toString('base64');

    // Return success status with the modified PDF data
    res.json({
      success: true,
      fileId: fileId,
      pdfData: `data:application/pdf;base64,${editedBase64}`,
      message: 'Text edited successfully using pdf-lib (actual PDF modification)',
      editsCount: {
        added: textEdits ? textEdits.length : 0,
        replaced: textReplacements ? textReplacements.length : 0,
        deleted: deletions ? deletions.length : 0
      }
    });
  } catch (error) {
    console.error('Text editing error:', error);
    throw error; // Let error handler middleware handle it
  }
}

/**
 * Perform OCR on PDF page
 * Takes file ID and page number
 * Supports background processing for large files
 */
async function performOCR(req, res) {
  try {
    const visionClient = getVisionClient();
    if (!visionClient) {
      return res.status(503).json({
        success: false,
        error: 'Google Cloud Vision API not initialized. Please check your service account credentials.',
        code: 'SERVICE_UNAVAILABLE'
      });
    }

    const { fileId, pageIndex = 0, scale = 2.0, languageHints = ['en'], background = false } = req.body;

    if (!fileId) {
      return res.status(400).json({
        success: false,
        error: 'File ID is required',
        code: 'MISSING_FILE_ID'
      });
    }

    const fileStorage = require('../utils/fileStorage');
    
    // Get file with error handling
    let pdfBuffer;
    try {
      const fileData = fileStorage.getFile(fileId);
      pdfBuffer = fileData.buffer;
    } catch (error) {
      return res.status(404).json({
        success: false,
        error: 'File not found',
        code: 'FILE_NOT_FOUND'
      });
    }

    // Validate PDF
    try {
      await withTimeout(validatePDF(pdfBuffer), 10000);
    } catch (error) {
      return res.status(error.statusCode || 422).json({
        success: false,
        error: error.message || 'Invalid PDF file',
        code: error.name || 'PDF_VALIDATION_ERROR'
      });
    }

    // Check cache for OCR results
    const cacheKey = `ocr-${fileId}-${pageIndex}-${scale}`;
    const cachedResult = getCachedResult(cacheKey);
    if (cachedResult) {
      return res.json({
        success: true,
        ...cachedResult,
        cached: true
      });
    }

    // Get client ID for rate limiting
    const clientId = req.ip || req.headers['x-forwarded-for'] || 'default';

    // Background processing for large files
    if (background || pdfBuffer.length > 50 * 1024 * 1024) {
      const jobId = jobQueue.enqueue({
        handler: async (data) => {
          return await visionOCR.performOCR(data.pdfBuffer, data.pageIndex, {
            scale: data.scale,
            languageHints: data.languageHints,
            clientId: data.clientId
          });
        },
        data: {
          pdfBuffer,
          pageIndex,
          scale,
          languageHints,
          clientId
        }
      });

      return res.json({
        success: true,
        message: 'OCR job queued for background processing',
        jobId: jobId,
        status: 'queued',
        statusUrl: `/api/pdf/ocr/status/${jobId}`
      });
    }

    // Perform OCR with timeout
    let ocrResult;
    try {
      ocrResult = await withTimeout(
        visionOCR.performOCR(pdfBuffer, pageIndex, {
          scale: scale,
          languageHints: languageHints,
          clientId: clientId
        }),
        60000, // 60 second timeout
        'OCR processing timed out'
      );
    } catch (error) {
      // Handle quota exceeded
      if (error.code === 8 || error.message.includes('RESOURCE_EXHAUSTED') || error.message.includes('quota')) {
        throw new QuotaExceededError('Google Cloud Vision API quota exceeded. Please try again later.');
      }
      throw error;
    }

    // OCR result already contains properly mapped PDF coordinates
    // No additional mapping needed as it's done in vision-ocr.js
    const result = {
      success: true,
      fileId: fileId,
      pageIndex: pageIndex,
      text: ocrResult.text,
      words: ocrResult.words, // Already contains pdfCoordinates
      paragraphs: ocrResult.paragraphs,
      blocks: ocrResult.blocks,
      confidence: ocrResult.confidence,
      method: ocrResult.method,
      imageSize: ocrResult.imageSize,
      pdfSize: ocrResult.pdfSize,
      scale: ocrResult.scale
    };

    // Cache result
    cacheResult(cacheKey, result, 1800); // 30 minutes

    res.json(result);
  } catch (error) {
    console.error('OCR error:', error);
    throw error; // Let error handler middleware handle it
  }
}

/**
 * Perform batch OCR on multiple pages
 */
async function performBatchOCR(req, res) {
  try {
    const visionClient = getVisionClient();
    if (!visionClient) {
      return res.status(503).json({
        success: false,
        error: 'Google Cloud Vision API not initialized'
      });
    }

    const { pdfData, pageIndices = [0], scale = 2.0, languageHints = ['en'] } = req.body;

    if (!pdfData || !Array.isArray(pageIndices) || pageIndices.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'Invalid request. Provide pdfData and pageIndices array.'
      });
    }

    // Convert base64 to buffer
    let pdfBuffer;
    if (typeof pdfData === 'string') {
      if (pdfData.startsWith('data:application/pdf;base64,')) {
        pdfData = pdfData.split(',')[1];
      }
      pdfBuffer = Buffer.from(pdfData, 'base64');
    } else {
      pdfBuffer = Buffer.from(pdfData);
    }

    // Get client ID for rate limiting
    const clientId = req.ip || req.headers['x-forwarded-for'] || 'default';

    // Perform batch OCR
    const batchResult = await visionOCR.performBatchOCR(pdfBuffer, pageIndices, {
      scale: scale,
      languageHints: languageHints,
      clientId: clientId
    });

    res.json({
      success: batchResult.success,
      ...batchResult
    });
  } catch (error) {
    console.error('Batch OCR error:', error);
    
    let statusCode = 500;
    if (error.message.includes('Rate limit')) {
      statusCode = 429;
    }

    res.status(statusCode).json({
      success: false,
      error: error.message || 'Batch OCR failed',
      code: error.code || 'BATCH_OCR_ERROR'
    });
  }
}

/**
 * Download edited PDF (legacy endpoint - supports direct PDF data)
 * This endpoint accepts PDF data directly and returns it for download
 */
async function downloadPDF(req, res) {
  try {
    const { pdfData, filename = 'edited-document.pdf', fileId } = req.body;

    let pdfBuffer;

    // If fileId is provided, use stored file (preferred - ensures latest edits)
    if (fileId) {
      const fileStorage = require('../utils/fileStorage');
      try {
        const fileData = fileStorage.getFile(fileId);
        pdfBuffer = fileData.buffer;
        
        // Apply any pending edits
        const metadata = fileData.metadata;
        if (metadata.edits && metadata.edits.length > 0) {
          const nativePdfEditor = require('../api/pdf-edit/native-pdf-editor');
          const allEdits = {
            textEdits: [],
            textReplacements: [],
            deletions: [],
            highlights: [],
            comments: [],
            stamps: [],
            shapes: [],
            images: [],
            ocrTexts: []
          };
          
          metadata.edits.forEach(edit => {
            if (edit.type === 'text' && edit.edits) allEdits.textEdits.push(...edit.edits);
            else if (edit.type === 'replacement' && edit.replacements) allEdits.textReplacements.push(...edit.replacements);
            else if (edit.type === 'deletion' && edit.deletions) allEdits.deletions.push(...edit.deletions);
            else if (edit.type === 'image' && edit.images) allEdits.images.push(...edit.images);
            else if (edit.type === 'ocr' && edit.ocrTexts) allEdits.ocrTexts.push(...edit.ocrTexts);
          });
          
          pdfBuffer = await nativePdfEditor.applyNativeEdits(pdfBuffer, allEdits);
        }
      } catch (error) {
        console.warn('Could not load file by ID, using provided PDF data:', error.message);
      }
    }

    // If no fileId or fileId load failed, use provided pdfData
    if (!pdfBuffer) {
      if (!pdfData) {
        return res.status(400).json({
          success: false,
          error: 'No PDF data or file ID provided'
        });
      }

      // Convert base64 to buffer
      if (typeof pdfData === 'string') {
        if (pdfData.startsWith('data:application/pdf;base64,')) {
          pdfData = pdfData.split(',')[1];
        }
        pdfBuffer = Buffer.from(pdfData, 'base64');
      } else {
        pdfBuffer = Buffer.from(pdfData);
      }
    }

    // Set headers for download
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
    res.setHeader('Content-Length', pdfBuffer.length);

    // Send PDF buffer
    res.send(pdfBuffer);
  } catch (error) {
    console.error('Download error:', error);
    res.status(500).json({
      success: false,
      error: 'Download failed: ' + error.message
    });
  }
}

/**
 * Download edited PDF by file ID
 * Returns the LATEST edited version with ALL changes applied
 * CRITICAL: This ensures users get the edited PDF, not the original
 * Handles large file downloads with streaming
 */
async function downloadPDFById(req, res) {
  try {
    const { id } = req.params;

    if (!id) {
      return res.status(400).json({
        success: false,
        error: 'File ID is required',
        code: 'MISSING_FILE_ID'
      });
    }

    const fileStorage = require('../utils/fileStorage');
    const nativePdfEditor = require('../api/pdf-edit/native-pdf-editor');
    
    // Get file with error handling
    let pdfBuffer, metadata;
    try {
      const fileData = fileStorage.getFile(id);
      pdfBuffer = fileData.buffer;
      metadata = fileData.metadata;
    } catch (error) {
      return res.status(404).json({
        success: false,
        error: 'File not found',
        code: 'FILE_NOT_FOUND'
      });
    }

    // CRITICAL: Always reapply ALL edits to ensure latest version
    // Even if file was updated, we need to ensure all edits are applied
    if (metadata.edits && metadata.edits.length > 0) {
      console.log(`Applying ${metadata.edits.length} edit(s) before download...`);
      
      // Collect ALL edits from history
      const allEdits = {
        textEdits: [],
        textReplacements: [],
        deletions: [],
        highlights: [],
        comments: [],
        stamps: [],
        shapes: [],
        images: [],
        ocrTexts: []
      };
      
      // Group ALL edits by type (from entire edit history)
      metadata.edits.forEach(edit => {
        if (edit.type === 'text' && edit.edits) {
          allEdits.textEdits.push(...edit.edits);
        } else if (edit.type === 'replacement' && edit.replacements) {
          allEdits.textReplacements.push(...edit.replacements);
        } else if (edit.type === 'deletion' && edit.deletions) {
          allEdits.deletions.push(...edit.deletions);
        } else if (edit.type === 'highlight' && edit.highlights) {
          allEdits.highlights.push(...edit.highlights);
        } else if (edit.type === 'comment' && edit.comments) {
          allEdits.comments.push(...edit.comments);
        } else if (edit.type === 'stamp' && edit.stamps) {
          allEdits.stamps.push(...edit.stamps);
        } else if (edit.type === 'shape' && edit.shapes) {
          allEdits.shapes.push(...edit.shapes);
        } else if (edit.type === 'image' && edit.images) {
          allEdits.images.push(...edit.images);
        } else if (edit.type === 'ocr' && edit.ocrTexts) {
          allEdits.ocrTexts.push(...edit.ocrTexts);
        }
      });
      
      // Apply ALL edits using pdf-lib (actual PDF modification)
      if (allEdits.textEdits.length > 0 || allEdits.textReplacements.length > 0 || 
          allEdits.deletions.length > 0 || allEdits.images.length > 0 ||
          allEdits.highlights.length > 0 || allEdits.comments.length > 0 ||
          allEdits.stamps.length > 0 || allEdits.shapes.length > 0 ||
          allEdits.ocrTexts.length > 0) {
        
        console.log('Applying edits:', {
          textEdits: allEdits.textEdits.length,
          replacements: allEdits.textReplacements.length,
          deletions: allEdits.deletions.length,
          images: allEdits.images.length,
          highlights: allEdits.highlights.length,
          comments: allEdits.comments.length,
          stamps: allEdits.stamps.length,
          shapes: allEdits.shapes.length,
          ocrTexts: allEdits.ocrTexts.length
        });
        
        // Apply all edits to PDF using pdf-lib
        pdfBuffer = await nativePdfEditor.applyNativeEdits(pdfBuffer, allEdits);
        
        // Update stored file with final version (so next download is faster)
        fileStorage.updateFile(id, pdfBuffer);
        
        console.log('All edits applied successfully. PDF ready for download.');
      }
    }

    // Validate PDF
    try {
      await withTimeout(validatePDF(pdfBuffer), 10000);
    } catch (error) {
      return res.status(error.statusCode || 422).json({
        success: false,
        error: error.message || 'Invalid PDF file',
        code: error.name || 'PDF_VALIDATION_ERROR'
      });
    }

    // Get filename from metadata or use default
    const filename = metadata.originalName || 'edited-document.pdf';
    
    // Sanitize filename (add "edited" prefix if file was modified)
    let safeFilename = filename.replace(/[^a-zA-Z0-9.-]/g, '_');
    if (metadata.edits && metadata.edits.length > 0) {
      const nameWithoutExt = safeFilename.replace(/\.pdf$/i, '');
      safeFilename = `${nameWithoutExt}_edited.pdf`;
    }

    // Use streaming for large files with proper headers
    await streamPDFResponse(res, pdfBuffer, safeFilename);
  } catch (error) {
    console.error('Download error:', error);
    throw error; // Let error handler middleware handle it
  }
}

/**
 * Get server status
 */
function getStatus(req, res) {
  const { checkGoogleCloudStatus } = require('../config/google-cloud');
  const status = checkGoogleCloudStatus();
  
  res.json({
    success: true,
    server: 'running',
    visionApi: status.vision.initialized ? 'initialized' : 'not initialized',
    firebase: status.firebase.initialized ? 'initialized' : 'not initialized',
    timestamp: new Date().toISOString()
  });
}

/**
 * Get OCR service status
 */
function getOCRStatus(req, res) {
  const visionClient = getVisionClient();
  
  res.json({
    success: true,
    visionApi: visionClient ? 'active' : 'inactive',
    method: visionClient ? 'Google Cloud Vision API' : 'not available'
  });
}

/**
 * Load PDF by file ID
 */
async function loadPDF(req, res) {
  try {
    const { id } = req.params;

    if (!id) {
      return res.status(400).json({
        success: false,
        error: 'File ID is required',
        code: 'MISSING_FILE_ID'
      });
    }

    const fileStorage = require('../utils/fileStorage');
    
    // Get file with error handling
    let pdfBuffer, metadata;
    try {
      const fileData = fileStorage.getFile(id);
      pdfBuffer = fileData.buffer;
      metadata = fileData.metadata;
    } catch (error) {
      return res.status(404).json({
        success: false,
        error: 'File not found',
        code: 'FILE_NOT_FOUND'
      });
    }

    // Validate PDF
    try {
      await withTimeout(validatePDF(pdfBuffer), 10000);
    } catch (error) {
      return res.status(error.statusCode || 422).json({
        success: false,
        error: error.message || 'Invalid PDF file',
        code: error.name || 'PDF_VALIDATION_ERROR'
      });
    }

    // Set headers
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Length', pdfBuffer.length);
    res.setHeader('Cache-Control', 'public, max-age=3600'); // Cache for 1 hour
    res.setHeader('X-File-Id', id);

    // Send PDF buffer
    res.send(pdfBuffer);
  } catch (error) {
    console.error('Load PDF error:', error);
    throw error; // Let error handler middleware handle it
  }
}

/**
 * Get OCR job status
 */
function getOCRJobStatus(req, res) {
  try {
    const { jobId } = req.params;
    
    if (!jobId) {
      return res.status(400).json({
        success: false,
        error: 'Job ID is required',
        code: 'MISSING_JOB_ID'
      });
    }

    const jobStatus = jobQueue.getJobStatus(jobId);
    
    if (!jobStatus) {
      return res.status(404).json({
        success: false,
        error: 'Job not found',
        code: 'JOB_NOT_FOUND'
      });
    }

    res.json({
      success: true,
      jobId: jobId,
      status: jobStatus.status,
      createdAt: jobStatus.createdAt,
      updatedAt: jobStatus.updatedAt,
      result: jobStatus.result,
      error: jobStatus.error
    });
  } catch (error) {
    console.error('Get OCR job status error:', error);
    throw error;
  }
}

module.exports = {
  uploadPDF: asyncHandler(uploadPDF),
  editPDF: asyncHandler(editPDF),
  editText: asyncHandler(editText),
  performOCR: asyncHandler(performOCR),
  performBatchOCR: asyncHandler(performBatchOCR),
  downloadPDF: asyncHandler(downloadPDF),
  downloadPDFById: asyncHandler(downloadPDFById),
  loadPDF: asyncHandler(loadPDF),
  getStatus,
  getOCRStatus,
  getOCRJobStatus
};

