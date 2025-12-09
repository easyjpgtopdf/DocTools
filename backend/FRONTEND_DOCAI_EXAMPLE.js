/**
 * Frontend Fetch Code for Google Document AI Endpoint
 * Add this to pdf-to-excel-convert.html
 * 
 * Replace API_BASE_URL with your Cloud Run URL
 */

// Backend API URL - Update with your Cloud Run URL
const API_BASE_URL = 'https://pdf-to-excel-backend-iwumaktavq-uc.a.run.app';

/**
 * Convert PDF to Excel using Google Document AI
 * @param {File} file - PDF file from file input
 */
async function convertPdfToExcelDocAI(file) {
  try {
    // Validate file
    if (!file || file.type !== 'application/pdf') {
      alert('Please select a valid PDF file');
      return;
    }
    
    if (file.size > 100 * 1024 * 1024) {
      alert('File size exceeds 100MB limit');
      return;
    }
    
    // Show loading state
    console.log('Converting PDF to Excel with Document AI...');
    
    // Create FormData
    const fd = new FormData();
    fd.append('file', file);
    
    // Call backend API
    const response = await fetch(`${API_BASE_URL}/api/pdf-to-excel-docai`, {
      method: 'POST',
      body: fd
    });
    
    const json = await response.json();
    
    // Check for insufficient credits
    if (json.insufficient_credits) {
      alert(`Not enough credits. You need ${json.required} credits but only have ${json.available}. Please buy more credits.`);
      return;
    }
    
    // Check for errors
    if (!response.ok) {
      const errorMsg = json.error || json.detail || json.message || 'Conversion failed';
      alert(`Error: ${errorMsg}`);
      return;
    }
    
    // Success - redirect to download URL
    if (json.downloadUrl) {
      console.log(`Success! Processed ${json.pagesProcessed} pages. Credits left: ${json.creditsLeft}`);
      window.location.href = json.downloadUrl;
    } else {
      alert('Conversion completed but no download URL received');
    }
    
  } catch (error) {
    console.error('Conversion error:', error);
    alert('Failed to convert PDF to Excel: ' + error.message);
  }
}

/**
 * Example: Add button to existing UI
 * 
 * In pdf-to-excel-convert.html, add a new button:
 * 
 * <button class="btn" id="downloadExcelDocAI">
 *   <i class="fas fa-file-excel"></i> Download Excel (DocAI)
 * </button>
 * 
 * Then add event listener:
 * 
 * document.getElementById('downloadExcelDocAI').addEventListener('click', async function() {
 *   const rec = await getPdf(); // Get PDF from storage
 *   if (!rec || !rec.blob) {
 *     alert('PDF file not found. Please upload again.');
 *     return;
 *   }
 *   
 *   const pdfFile = new File([rec.blob], rec.name || 'document.pdf', { type: 'application/pdf' });
 *   await convertPdfToExcelDocAI(pdfFile);
 * });
 */

/**
 * Complete integration example for pdf-to-excel-convert.html
 * 
 * Replace the existing exportExcel function or add alongside it:
 */
async function exportExcelDocAI() {
  // Get PDF file from storage (existing code)
  const rec = await getPdf();
  if (!rec || !rec.blob) {
    showToast('PDF file not found. Please upload again.', true);
    location.href = 'pdf-to-excel.html';
    return;
  }
  
  // Show loading state
  downloadBtn.disabled = true;
  showToast('Converting PDF to Excel with Document AI...', false);
  
  try {
    // Create FormData with PDF file
    const fd = new FormData();
    const pdfFile = new File([rec.blob], rec.name || 'document.pdf', { type: 'application/pdf' });
    fd.append('file', pdfFile);
    
    // Call backend API
    const response = await fetch(`${API_BASE_URL}/api/pdf-to-excel-docai`, {
      method: 'POST',
      body: fd
    });
    
    const result = await response.json();
    
    // Check for insufficient credits
    if (result.insufficient_credits) {
      alert(`Not enough credits. You need ${result.required} credits but only have ${result.available}. Please buy more credits.`);
      downloadBtn.disabled = false;
      return;
    }
    
    // Check for errors
    if (!response.ok || result.status !== 'success') {
      const errorMsg = result.error || result.detail || result.message || 'Conversion failed';
      throw new Error(errorMsg);
    }
    
    // Success - redirect to download URL
    showToast(`Success! Processed ${result.pagesProcessed} pages. Credits left: ${result.creditsLeft}`, false);
    window.location.href = result.downloadUrl;
    
  } catch (err) {
    console.error('Conversion error:', err);
    showToast('Failed to convert PDF to Excel: ' + err.message, true);
    downloadBtn.disabled = false;
  }
}

