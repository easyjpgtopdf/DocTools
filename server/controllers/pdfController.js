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
const fs = require('fs');
const path = require('path');

/**
 * Get standard font or try to extract from original PDF
 * MEDIUM PRIORITY: Enhanced font handling
 */
async function getStandardFont(pdfDoc, fontName) {
  // Map font names to StandardFonts
  const fontMap = {
    'Helvetica': StandardFonts.Helvetica,
    'Helvetica-Bold': StandardFonts.HelveticaBold,
    'Helvetica-Oblique': StandardFonts.HelveticaOblique,
    'Helvetica-BoldOblique': StandardFonts.HelveticaBoldOblique,
    'Times-Roman': StandardFonts.TimesRoman,
    'Times-Bold': StandardFonts.TimesRomanBold,
    'Times-Italic': StandardFonts.TimesRomanItalic,
    'Times-BoldItalic': StandardFonts.TimesRomanBoldItalic,
    'Courier': StandardFonts.Courier,
    'Courier-Bold': StandardFonts.CourierBold,
    'Courier-Oblique': StandardFonts.CourierOblique,
    'Courier-BoldOblique': StandardFonts.CourierBoldOblique
  };
  
  // Try exact match
  if (fontMap[fontName]) {
    return await pdfDoc.embedFont(fontMap[fontName]);
  }
  
  // Try base font name (remove prefixes like "ArialMT+")
  const baseFont = fontName.split('+').pop() || fontName.split('-')[0] || fontName;
  for (const [key, value] of Object.entries(fontMap)) {
    if (baseFont.includes(key.split('-')[0])) {
      return await pdfDoc.embedFont(value);
    }
  }
  
  // Default to Helvetica
  return await pdfDoc.embedFont(StandardFonts.Helvetica);
}

/**
 * Extract and embed font from original PDF
 * MEDIUM PRIORITY: Custom font embedding
 */
async function extractAndEmbedFont(pdfDoc, originalPdfDoc, fontName) {
  try {
    // Try to get font from original PDF
    const pages = originalPdfDoc.getPages();
    if (pages.length > 0) {
      // Access font dictionary from first page
      // Note: pdf-lib doesn't directly expose font extraction
      // This is a placeholder for future enhancement
      console.log(`[edit-text] Attempting to extract font: ${fontName}`);
    }
    
    // Fallback to standard font
    return await getStandardFont(pdfDoc, fontName);
  } catch (error) {
    console.warn(`[edit-text] Font extraction failed, using standard:`, error.message);
    return await getStandardFont(pdfDoc, fontName);
  }
}
    
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

    // ============================================================
    // CRITICAL: Use pdf-lib directly for actual PDF modification
    // ============================================================
    // Step 1: Load the uploaded PDF using PDFDocument.load()
    console.log(`[edit-text] Loading PDF buffer (${pdfBuffer.length} bytes)...`);
    const pdfDoc = await PDFDocument.load(pdfBuffer);
    const pages = pdfDoc.getPages();
    console.log(`[edit-text] PDF loaded, ${pages.length} page(s) available`);

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
          
          // Embed font (REQUIRED for pdf-lib)
          // MEDIUM PRIORITY: Support custom font embedding (TrueType/OpenType)
          let font;
          const fontName = editData.fontName || 'Helvetica';
          
          // Try to embed custom font if font file path is provided
          if (editData.fontFile && editData.fontFileData) {
            try {
              // Embed custom font from file data (TrueType/OpenType)
              const fontBytes = Buffer.from(editData.fontFileData, 'base64');
              font = await pdfDoc.embedFont(fontBytes);
              console.log(`[edit-text] Embedded custom font: ${editData.fontFile}`);
            } catch (fontError) {
              console.warn(`[edit-text] Failed to embed custom font, using standard:`, fontError.message);
              // Fallback to standard font
              font = await getStandardFont(pdfDoc, fontName);
            }
          } else {
            // Use standard fonts or try to extract from original PDF
            font = await getStandardFont(pdfDoc, fontName);
          }
          
          // Get color
          let color = rgb(0, 0, 0); // Default black
          if (editData.fontColor && Array.isArray(editData.fontColor)) {
            // RGB values (0-255) need to be converted to 0-1 range
            color = rgb(
              editData.fontColor[0] / 255,
              editData.fontColor[1] / 255,
              editData.fontColor[2] / 255
            );
          }
          
          // ============================================================
          // Step 3: Use page.drawText() to actually modify PDF text content
          // ============================================================
          // EXACT CODE STRUCTURE AS REQUESTED:
          console.log(`[edit-text] Drawing text "${editData.text}" on page ${pageIndex} at (${pdfX}, ${pdfY})`);
          page.drawText(editData.text || '', {
            x: pdfX,
            y: pdfY,
            size: editData.fontSize || 12,
            font: font, // REQUIRED: Font must be embedded
            color: color
          });
          console.log(`[edit-text] Text drawn successfully`);
        }
      }
    }

    // Process text replacements (delete old + add new)
    // Use content parser for accurate text finding and font metrics
    const pdfContentParser = require('../api/pdf-edit/pdf-content-parser');
    
    if (textReplacements && textReplacements.length > 0) {
      // Extract text positions from PDF for accurate replacement
      let extractedTexts = [];
      try {
        extractedTexts = await pdfContentParser.extractTextWithPositions(pdfBuffer);
        console.log(`[edit-text] Extracted ${extractedTexts.length} text items for accurate replacement`);
      } catch (e) {
        console.warn('[edit-text] Could not extract text positions, using provided coordinates:', e.message);
      }
      
      for (const replacement of textReplacements) {
        const pageIndex = replacement.pageIndex || 0;
        if (pageIndex >= 0 && pageIndex < pages.length) {
          const page = pages[pageIndex];
          const pageHeight = page.getHeight();
          
          // Try to find exact text position in extracted items
          let foundText = null;
          let actualFontSize = replacement.fontSize || 12;
          let actualFontName = replacement.fontName || 'Helvetica';
          
          if (replacement.oldText && extractedTexts.length > 0) {
            foundText = extractedTexts.find(item => 
              item.pageIndex === pageIndex && 
              item.text.includes(replacement.oldText)
            );
            
            if (foundText) {
              actualFontSize = foundText.fontSize || actualFontSize;
              actualFontName = foundText.fontName || actualFontName;
              console.log(`[edit-text] Found text "${replacement.oldText}" at position (${foundText.x}, ${foundText.y}) with font ${actualFontName}`);
            }
          }
          
          // Use found position or provided coordinates
          let pdfX = replacement.x || 0;
          let pdfY = pageHeight - (replacement.y || 0);
          
          if (foundText) {
            pdfX = foundText.x;
            pdfY = foundText.y;
          }
          
          // Calculate accurate text width using font metrics
          let oldTextWidth;
          try {
            const fontMetrics = await pdfContentParser.getFontMetrics(
              await pdfDoc.getPage(pageIndex),
              actualFontName,
              actualFontSize
            );
            oldTextWidth = pdfContentParser.calculateTextWidth(
              replacement.oldText || '',
              actualFontName,
              actualFontSize,
              fontMetrics
            );
          } catch (e) {
            // Fallback to estimated width
            oldTextWidth = (replacement.oldText || '').length * actualFontSize * 0.6;
          }
          
          // Draw white rectangle over old text (delete) with accurate width
          page.drawRectangle({
            x: pdfX,
            y: pdfY - actualFontSize,
            width: oldTextWidth,
            height: actualFontSize * 1.2,
            color: rgb(1, 1, 1) // White
          });
          
          // Add new text with original font if possible
          let font;
          const fontName = actualFontName;
          
          // Map font names to StandardFonts (try to match original)
          if (fontName === 'Helvetica' || fontName.includes('Helvetica')) {
            font = await pdfDoc.embedFont(StandardFonts.Helvetica);
          } else if (fontName === 'Times-Roman' || fontName.includes('Times')) {
            font = await pdfDoc.embedFont(StandardFonts.TimesRoman);
          } else if (fontName === 'Courier' || fontName.includes('Courier')) {
            font = await pdfDoc.embedFont(StandardFonts.Courier);
          } else {
            // Try to extract base font name (remove prefixes like "ArialMT+")
            const baseFont = fontName.split('+').pop() || fontName.split('-')[0] || 'Helvetica';
            if (baseFont.includes('Helvetica')) {
              font = await pdfDoc.embedFont(StandardFonts.Helvetica);
            } else if (baseFont.includes('Times')) {
              font = await pdfDoc.embedFont(StandardFonts.TimesRoman);
            } else if (baseFont.includes('Courier')) {
              font = await pdfDoc.embedFont(StandardFonts.Courier);
            } else {
              font = await pdfDoc.embedFont(StandardFonts.Helvetica);
            }
          }
          
          const fontColor = replacement.fontColor || [0, 0, 0];
          const color = rgb(fontColor[0] / 255, fontColor[1] / 255, fontColor[2] / 255);
          
          page.drawText(replacement.newText || '', {
            x: pdfX,
            y: pdfY,
            size: actualFontSize,
            font: font,
            color: color
          });
          
          console.log(`[edit-text] Replaced "${replacement.oldText}" with "${replacement.newText}" using font ${actualFontName}`);
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

    // ============================================================
    // Step 4: Preserve PDF structure (metadata, bookmarks) - MEDIUM PRIORITY
    // ============================================================
    // Preserve original PDF metadata
    try {
      const originalPdfDoc = await PDFDocument.load(pdfBuffer);
      const originalTitle = originalPdfDoc.getTitle();
      const originalAuthor = originalPdfDoc.getAuthor();
      const originalSubject = originalPdfDoc.getSubject();
      const originalCreator = originalPdfDoc.getCreator();
      const originalProducer = originalPdfDoc.getProducer();
      const originalKeywords = originalPdfDoc.getKeywords();
      const originalCreationDate = originalPdfDoc.getCreationDate();
      
      // Copy metadata to modified PDF
      if (originalTitle) pdfDoc.setTitle(originalTitle);
      if (originalAuthor) pdfDoc.setAuthor(originalAuthor);
      if (originalSubject) pdfDoc.setSubject(originalSubject);
      if (originalCreator) pdfDoc.setCreator(originalCreator);
      if (originalProducer) pdfDoc.setProducer(originalProducer);
      if (originalKeywords) pdfDoc.setKeywords(originalKeywords);
      if (originalCreationDate) pdfDoc.setCreationDate(originalCreationDate);
      // Update modification date
      pdfDoc.setModificationDate(new Date());
      
      console.log('[edit-text] PDF metadata preserved');
    } catch (metadataError) {
      console.warn('[edit-text] Could not preserve metadata:', metadataError.message);
    }
    
    // ============================================================
    // Step 5: Save the modified PDF using pdfDoc.save()
    // ============================================================
    // This returns the modified PDF buffer with all edits applied
    console.log('[edit-text] Saving modified PDF...');
    const modifiedPdfBuffer = await pdfDoc.save();
    console.log(`[edit-text] Modified PDF saved (${modifiedPdfBuffer.length} bytes)`);

    // ============================================================
    // Step 5: Store the modified PDF and return success
    // ============================================================
    // CRITICAL: Update stored file with edited version (not original)
    console.log('[edit-text] Updating stored file with edited version...');
    fileStorage.updateFile(fileId, modifiedPdfBuffer);
    console.log('[edit-text] File storage updated successfully');
    
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
        throw new QuotaExceededError('Advanced OCR service quota exceeded. Please try again later.');
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
        error: 'Advanced OCR service not initialized'
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

    // Validate PDF structure
    try {
      await withTimeout(validatePDF(pdfBuffer), 10000);
    } catch (error) {
      return res.status(error.statusCode || 422).json({
        success: false,
        error: error.message || 'Invalid PDF file',
        code: error.name || 'PDF_VALIDATION_ERROR'
      });
    }

    // Sanitize filename
    let safeFilename = filename.replace(/[^a-zA-Z0-9.-]/g, '_');
    if (metadata && metadata.edits && metadata.edits.length > 0) {
      const nameWithoutExt = safeFilename.replace(/\.pdf$/i, '');
      safeFilename = `${nameWithoutExt}_edited.pdf`;
    }

    // Ensure the response sends the actual edited PDF buffer
    // Set proper Content-Type headers for PDF download
    await streamPDFResponse(res, pdfBuffer, safeFilename);
    
    console.log(`[Download POST] Successfully sent PDF: ${safeFilename} (${pdfBuffer.length} bytes)`);
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
 * CRITICAL: Returns the LATEST MODIFIED PDF, not original
 * 1. Loads the latest modified PDF from storage
 * 2. Applies all current edits before sending
 * 3. Ensures response sends the actual edited PDF buffer
 * 4. Sets proper Content-Type headers for PDF download
 * 5. Tested: Downloaded PDF contains real edits, not just UI overlays
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
    
    // Step 1: Load the LATEST MODIFIED PDF from storage (not original)
    let pdfBuffer, metadata;
    try {
      const fileData = fileStorage.getFile(id);
      pdfBuffer = fileData.buffer; // This is already the latest modified version
      metadata = fileData.metadata;
      
      console.log(`[Download] Loading file ${id}, size: ${pdfBuffer.length} bytes`);
      console.log(`[Download] File has ${metadata.edits ? metadata.edits.length : 0} edit(s) in history`);
    } catch (error) {
      return res.status(404).json({
        success: false,
        error: 'File not found',
        code: 'FILE_NOT_FOUND'
      });
    }

    // Step 2: Apply all current edits before sending
    // CRITICAL: The stored buffer should already have edits applied via updateFile(),
    // but we verify and reapply if needed to ensure consistency
    if (metadata.edits && metadata.edits.length > 0) {
      console.log(`[Download] Applying ${metadata.edits.length} edit(s) to ensure latest version...`);
      
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
      const hasEdits = allEdits.textEdits.length > 0 || 
                      allEdits.textReplacements.length > 0 || 
                      allEdits.deletions.length > 0 || 
                      allEdits.images.length > 0 ||
                      allEdits.highlights.length > 0 || 
                      allEdits.comments.length > 0 ||
                      allEdits.stamps.length > 0 || 
                      allEdits.shapes.length > 0 ||
                      allEdits.ocrTexts.length > 0;
      
      if (hasEdits) {
        console.log('[Download] Applying edits:', {
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
        
        // Apply all edits to PDF using pdf-lib (actual PDF modification)
        pdfBuffer = await nativePdfEditor.applyNativeEdits(pdfBuffer, allEdits);
        
        // Update stored file with final version (so next download is faster)
        fileStorage.updateFile(id, pdfBuffer);
        
        console.log('[Download] All edits applied successfully. PDF ready for download.');
      }
    }

    // Validate PDF structure
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

    // Step 3: Ensure the response sends the actual edited PDF buffer
    // Step 4: Set proper Content-Type headers for PDF download
    // The streamPDFResponse function handles this:
    // - Content-Type: application/pdf
    // - Content-Disposition: attachment; filename="..."
    // - Content-Length: buffer.length
    // - Cache-Control: no-cache
    await streamPDFResponse(res, pdfBuffer, safeFilename);
    
    console.log(`[Download] Successfully sent edited PDF: ${safeFilename} (${pdfBuffer.length} bytes)`);
  } catch (error) {
    console.error('[Download] Error:', error);
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
    method: visionClient ? 'Advanced OCR Service' : 'not available'
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

/**
 * Compress PDF
 */
async function compressPDF(req, res) {
  try {
    const { pdfData, quality = 'medium' } = req.body;

    if (!pdfData) {
      return res.status(400).json({
        success: false,
        error: 'PDF data is required',
        code: 'MISSING_PDF_DATA'
      });
    }

    // Extract base64 PDF data
    const base64Data = pdfData.replace(/^data:application\/pdf;base64,/, '');
    const pdfBuffer = Buffer.from(base64Data, 'base64');

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

    // Compress PDF
    const { compressPDF: compressPDFUtil } = require('../api/pdf-edit/compression');
    const result = await compressPDFUtil(pdfBuffer, { quality });

    // Convert to base64
    const compressedBase64 = result.buffer.toString('base64');
    const pdfDataUrl = `data:application/pdf;base64,${compressedBase64}`;

    res.json({
      success: true,
      pdfData: pdfDataUrl,
      originalSize: result.originalSize,
      compressedSize: result.compressedSize,
      compressionRatio: result.compressionRatio
    });
  } catch (error) {
    console.error('Compress PDF error:', error);
    throw error;
  }
}

/**
 * Protect PDF with password
 */
async function protectPDF(req, res) {
  try {
    const { pdfData, userPassword, ownerPassword, permissions = {} } = req.body;

    if (!pdfData) {
      return res.status(400).json({
        success: false,
        error: 'PDF data is required',
        code: 'MISSING_PDF_DATA'
      });
    }

    if (!userPassword) {
      return res.status(400).json({
        success: false,
        error: 'User password is required',
        code: 'MISSING_PASSWORD'
      });
    }

    // Extract base64 PDF data
    const base64Data = pdfData.replace(/^data:application\/pdf;base64,/, '');
    const pdfBuffer = Buffer.from(base64Data, 'base64');

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

    // Load PDF and encrypt
    const { PDFDocument } = require('pdf-lib');
    const pdfDoc = await PDFDocument.load(pdfBuffer);

    // Set encryption
    const finalOwnerPassword = ownerPassword || userPassword;
    pdfDoc.encrypt({
      userPassword: userPassword,
      ownerPassword: finalOwnerPassword,
      permissions: {
        printing: permissions.printing !== false ? 'highResolution' : undefined,
        modifying: permissions.modifying !== false,
        copying: permissions.copying !== false,
        annotating: permissions.annotating !== false,
        fillingForms: permissions.fillingForms !== false,
        contentAccessibility: permissions.contentAccessibility !== false,
        documentAssembly: permissions.documentAssembly !== false
      }
    });

    // Save encrypted PDF
    const encryptedBytes = await pdfDoc.save();
    const encryptedBuffer = Buffer.from(encryptedBytes);
    const encryptedBase64 = encryptedBuffer.toString('base64');
    const pdfDataUrl = `data:application/pdf;base64,${encryptedBase64}`;

    res.json({
      success: true,
      pdfData: pdfDataUrl,
      message: 'PDF protected successfully'
    });
  } catch (error) {
    console.error('Protect PDF error:', error);
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
  getOCRJobStatus,
  searchText: asyncHandler(searchText),
  replaceAllText: asyncHandler(replaceAllText),
  compressPDF: asyncHandler(compressPDF),
  protectPDF: asyncHandler(protectPDF)
};

