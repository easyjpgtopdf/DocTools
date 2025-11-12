/**
 * Application Configuration
 * Handles API endpoints and environment-specific settings
 */

// Detect environment and set API base URL
function getApiBaseUrl() {
  // Check if we're in development (localhost or 127.0.0.1)
  const hostname = window.location.hostname;
  const isDevelopment = hostname === 'localhost' || hostname === '127.0.0.1' || hostname.startsWith('192.168.');
  
  if (isDevelopment) {
    // For local development, always use localhost:3000
    return 'http://localhost:3000';
  }
  
  // For production (easyjpgtopdf.com, Vercel, etc.)
  // Use the same origin where the frontend is served
  const origin = window.location.origin;
  
  console.log(`🔧 API Base URL configured: ${origin}`);
  return origin;
}

export const API_BASE_URL = getApiBaseUrl();

console.log(`✅ API Base URL: ${API_BASE_URL}`);

/**
 * Make API request with proper base URL
 * @param {string} endpoint - API endpoint path (e.g., '/api/create-order')
 * @param {object} options - Fetch options
 * @returns {Promise<Response>}
 */
export async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`API Error ${response.status}: ${response.statusText}`);
    }

    return response;
  } catch (error) {
    console.error(`API request failed for ${url}:`, error);
    throw error;
  }
}

console.log(`API Base URL configured as: ${API_BASE_URL}`);
