/**
 * Streaming Utilities
 * Handles streaming for large PDF files
 */

const stream = require('stream');
const { pipeline } = require('stream/promises');

/**
 * Create a readable stream from buffer
 */
function bufferToStream(buffer) {
  const readable = new stream.Readable();
  readable.push(buffer);
  readable.push(null);
  return readable;
}

/**
 * Stream PDF response
 */
async function streamPDFResponse(res, pdfBuffer, filename) {
  // Set headers
  res.setHeader('Content-Type', 'application/pdf');
  res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
  res.setHeader('Content-Length', pdfBuffer.length);
  res.setHeader('Cache-Control', 'no-cache');
  
  // For large files, stream in chunks
  if (pdfBuffer.length > 10 * 1024 * 1024) { // > 10MB
    const chunkSize = 1024 * 1024; // 1MB chunks
    let offset = 0;
    
    const sendChunk = () => {
      if (offset >= pdfBuffer.length) {
        res.end();
        return;
      }
      
      const chunk = pdfBuffer.slice(offset, Math.min(offset + chunkSize, pdfBuffer.length));
      offset += chunkSize;
      
      if (res.write(chunk)) {
        setImmediate(sendChunk);
      } else {
        res.once('drain', sendChunk);
      }
    };
    
    sendChunk();
  } else {
    // Send entire buffer for smaller files
    res.send(pdfBuffer);
  }
}

/**
 * Process PDF in chunks
 */
async function processPDFInChunks(pdfBuffer, processor, chunkSize = 1024 * 1024) {
  const chunks = [];
  let offset = 0;
  
  while (offset < pdfBuffer.length) {
    const chunk = pdfBuffer.slice(offset, Math.min(offset + chunkSize, pdfBuffer.length));
    const processed = await processor(chunk, offset);
    chunks.push(processed);
    offset += chunkSize;
  }
  
  return Buffer.concat(chunks);
}

module.exports = {
  bufferToStream,
  streamPDFResponse,
  processPDFInChunks
};

