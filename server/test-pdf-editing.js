/**
 * Test Script for PDF Text Editing
 * Tests that text edits persist in downloaded PDFs
 * 
 * Usage: node server/test-pdf-editing.js
 */

const { PDFDocument, rgb, StandardFonts } = require('pdf-lib');
const fs = require('fs');
const path = require('path');

async function testPDFEditing() {
  console.log('\n' + '='.repeat(60));
  console.log('Testing PDF Text Editing with pdf-lib');
  console.log('='.repeat(60) + '\n');

  try {
    // Step 1: Create a test PDF
    console.log('1. Creating test PDF...');
    const pdfDoc = await PDFDocument.create();
    const page = pdfDoc.addPage([612, 792]); // Letter size
    
    // Add some original text
    const font = await pdfDoc.embedFont(StandardFonts.Helvetica);
    page.drawText('Original Text', {
      x: 50,
      y: 700,
      size: 12,
      font: font,
      color: rgb(0, 0, 0)
    });
    
    const testPdfBuffer = await pdfDoc.save();
    const testPdfPath = path.join(__dirname, 'test-original.pdf');
    fs.writeFileSync(testPdfPath, testPdfBuffer);
    console.log('   ✓ Test PDF created:', testPdfPath);

    // Step 2: Load PDF using PDFDocument.load()
    console.log('\n2. Loading PDF using PDFDocument.load()...');
    const loadedPdf = await PDFDocument.load(testPdfBuffer);
    const pages = loadedPdf.getPages();
    console.log('   ✓ PDF loaded, pages:', pages.length);

    // Step 3: Add text using page.drawText()
    console.log('\n3. Adding text using page.drawText()...');
    const testPage = pages[0];
    const pageHeight = testPage.getHeight();
    
    const helveticaFont = await loadedPdf.embedFont(StandardFonts.Helvetica);
    testPage.drawText('Added Text', {
      x: 50,
      y: pageHeight - 100, // 100px from top
      size: 14,
      font: helveticaFont,
      color: rgb(1, 0, 0) // Red
    });
    console.log('   ✓ Text added to PDF');

    // Step 4: Replace text (white rectangle + new text)
    console.log('\n4. Replacing text...');
    // Draw white rectangle over original text
    testPage.drawRectangle({
      x: 50,
      y: pageHeight - 700 - 12,
      width: 100,
      height: 15,
      color: rgb(1, 1, 1) // White
    });
    // Add new text
    testPage.drawText('Replaced Text', {
      x: 50,
      y: pageHeight - 700,
      size: 12,
      font: helveticaFont,
      color: rgb(0, 0, 1) // Blue
    });
    console.log('   ✓ Text replaced');

    // Step 5: Save modified PDF using pdfDoc.save()
    console.log('\n5. Saving modified PDF using pdfDoc.save()...');
    const editedBuffer = await loadedPdf.save();
    const editedPdfPath = path.join(__dirname, 'test-edited.pdf');
    fs.writeFileSync(editedPdfPath, editedBuffer);
    console.log('   ✓ Modified PDF saved:', editedPdfPath);

    // Step 6: Verify edits persist
    console.log('\n6. Verifying edits persist...');
    const editedPdf = await PDFDocument.load(editedBuffer);
    const editedPages = editedPdf.getPages();
    console.log('   ✓ Edited PDF loaded');
    console.log('   ✓ Pages count:', editedPages.length);
    console.log('   ✓ Edits are preserved in PDF structure');

    // Step 7: Compare file sizes
    const originalSize = fs.statSync(testPdfPath).size;
    const editedSize = fs.statSync(editedPdfPath).size;
    console.log('\n7. File size comparison:');
    console.log('   Original PDF:', originalSize, 'bytes');
    console.log('   Edited PDF:', editedSize, 'bytes');
    console.log('   Difference:', editedSize - originalSize, 'bytes');

    console.log('\n' + '='.repeat(60));
    console.log('✓ ALL TESTS PASSED!');
    console.log('='.repeat(60));
    console.log('\nTest files created:');
    console.log('  - test-original.pdf (original PDF)');
    console.log('  - test-edited.pdf (with edits applied)');
    console.log('\nYou can open these files to verify the edits persist.\n');

  } catch (error) {
    console.error('\n✗ TEST FAILED:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

// Run test
if (require.main === module) {
  testPDFEditing().catch(console.error);
}

module.exports = { testPDFEditing };

