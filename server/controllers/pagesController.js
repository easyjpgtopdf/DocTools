/**
 * Pages Controller
 * Handles PDF page management operations
 */

const pageManagement = require('../api/pdf-edit/page-management');

/**
 * Rotate pages
 */
async function rotatePages(req, res) {
  try {
    const { pdfData, rotations } = req.body;
    
    if (!pdfData || !rotations) {
      return res.status(400).json({
        success: false,
        error: 'Missing required data: pdfData and rotations'
      });
    }
    
    let pdfBuffer = Buffer.from(pdfData.split(',')[1] || pdfData, 'base64');
    const editedBuffer = await pageManagement.rotatePages(pdfBuffer, rotations);
    
    res.json({
      success: true,
      pdfData: `data:application/pdf;base64,${editedBuffer.toString('base64')}`
    });
  } catch (error) {
    console.error('Rotate pages error:', error);
    res.status(500).json({
      success: false,
      error: error.message || 'Page rotation failed'
    });
  }
}

/**
 * Delete pages
 */
async function deletePages(req, res) {
  try {
    const { pdfData, pageIndices } = req.body;
    
    if (!pdfData || !pageIndices || !Array.isArray(pageIndices)) {
      return res.status(400).json({
        success: false,
        error: 'Missing required data: pdfData and pageIndices array'
      });
    }
    
    let pdfBuffer = Buffer.from(pdfData.split(',')[1] || pdfData, 'base64');
    const editedBuffer = await pageManagement.deletePages(pdfBuffer, pageIndices);
    
    res.json({
      success: true,
      pdfData: `data:application/pdf;base64,${editedBuffer.toString('base64')}`
    });
  } catch (error) {
    console.error('Delete pages error:', error);
    res.status(500).json({
      success: false,
      error: error.message || 'Page deletion failed'
    });
  }
}

/**
 * Reorder pages
 */
async function reorderPages(req, res) {
  try {
    const { pdfData, newOrder } = req.body;
    
    if (!pdfData || !newOrder || !Array.isArray(newOrder)) {
      return res.status(400).json({
        success: false,
        error: 'Missing required data: pdfData and newOrder array'
      });
    }
    
    let pdfBuffer = Buffer.from(pdfData.split(',')[1] || pdfData, 'base64');
    const editedBuffer = await pageManagement.reorderPages(pdfBuffer, newOrder);
    
    res.json({
      success: true,
      pdfData: `data:application/pdf;base64,${editedBuffer.toString('base64')}`
    });
  } catch (error) {
    console.error('Reorder pages error:', error);
    res.status(500).json({
      success: false,
      error: error.message || 'Page reordering failed'
    });
  }
}

/**
 * Extract pages
 */
async function extractPages(req, res) {
  try {
    const { pdfData, pageIndices } = req.body;
    
    if (!pdfData || !pageIndices || !Array.isArray(pageIndices)) {
      return res.status(400).json({
        success: false,
        error: 'Missing required data: pdfData and pageIndices array'
      });
    }
    
    let pdfBuffer = Buffer.from(pdfData.split(',')[1] || pdfData, 'base64');
    const extractedBuffer = await pageManagement.extractPages(pdfBuffer, pageIndices);
    
    res.json({
      success: true,
      pdfData: `data:application/pdf;base64,${extractedBuffer.toString('base64')}`
    });
  } catch (error) {
    console.error('Extract pages error:', error);
    res.status(500).json({
      success: false,
      error: error.message || 'Page extraction failed'
    });
  }
}

/**
 * Add page
 */
async function addPage(req, res) {
  try {
    const { pdfData, pageIndex = -1, insertAfter = true } = req.body;
    
    if (!pdfData) {
      return res.status(400).json({
        success: false,
        error: 'Missing required data: pdfData'
      });
    }
    
    let pdfBuffer = Buffer.from(pdfData.split(',')[1] || pdfData, 'base64');
    const editedBuffer = await pageManagement.addPage(pdfBuffer, pageIndex, insertAfter);
    
    res.json({
      success: true,
      pdfData: `data:application/pdf;base64,${editedBuffer.toString('base64')}`
    });
  } catch (error) {
    console.error('Add page error:', error);
    res.status(500).json({
      success: false,
      error: error.message || 'Page addition failed'
    });
  }
}

module.exports = {
  rotatePages,
  deletePages,
  reorderPages,
  extractPages,
  addPage
};

