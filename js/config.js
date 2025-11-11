/**
 * Application Configuration
 * Handles API endpoints and environment-specific settings
 */

// Detect environment and set API base URL
function getApiBaseUrl() {
  // Check if we're in development (localhost)
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return `http://localhost:3000`;
  }
  
  // For production, try to use the same origin first
  // If the server is served from a different domain, you can add a check here
  const origin = window.location.origin;
  
  // If on Vercel or production domain, try the same origin
  // The server should be served on the same origin (easyjpgtopdf.com)
  return origin;
}

export const API_BASE_URL = getApiBaseUrl();

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
