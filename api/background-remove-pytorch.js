// DISABLED - Now using MODNet Browser Version
// This API endpoint is no longer used - background removal is done entirely in browser
// Kept for reference but returns error to prevent accidental usage

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  return res.status(410).json({
    success: false,
    error: 'This endpoint is disabled. Background removal now uses MODNet browser version - no backend needed.',
    message: 'Please use the browser-based MODNet implementation on the workspace page.'
  });
}
