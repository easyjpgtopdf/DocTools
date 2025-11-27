/**
 * File Cache Utility
 * Implements caching for PDF files and processed results
 */

const NodeCache = require('node-cache');

// Create cache instances
const fileCache = new NodeCache({
  stdTTL: 3600, // 1 hour default TTL
  checkperiod: 600, // Check for expired keys every 10 minutes
  maxKeys: 1000 // Maximum 1000 cached files
});

const resultCache = new NodeCache({
  stdTTL: 1800, // 30 minutes for processed results
  checkperiod: 300,
  maxKeys: 500
});

/**
 * Cache a file buffer
 */
function cacheFile(key, buffer, ttl = 3600) {
  try {
    fileCache.set(key, buffer, ttl);
    return true;
  } catch (error) {
    console.warn('Cache set failed:', error.message);
    return false;
  }
}

/**
 * Get cached file
 */
function getCachedFile(key) {
  return fileCache.get(key);
}

/**
 * Cache processed result
 */
function cacheResult(key, result, ttl = 1800) {
  try {
    resultCache.set(key, result, ttl);
    return true;
  } catch (error) {
    console.warn('Result cache set failed:', error.message);
    return false;
  }
}

/**
 * Get cached result
 */
function getCachedResult(key) {
  return resultCache.get(key);
}

/**
 * Invalidate cache entry
 */
function invalidateCache(key) {
  fileCache.del(key);
  resultCache.del(key);
}

/**
 * Clear all caches
 */
function clearCache() {
  fileCache.flushAll();
  resultCache.flushAll();
}

/**
 * Get cache statistics
 */
function getCacheStats() {
  return {
    files: {
      keys: fileCache.keys().length,
      hits: fileCache.getStats().hits,
      misses: fileCache.getStats().misses
    },
    results: {
      keys: resultCache.keys().length,
      hits: resultCache.getStats().hits,
      misses: resultCache.getStats().misses
    }
  };
}

module.exports = {
  cacheFile,
  getCachedFile,
  cacheResult,
  getCachedResult,
  invalidateCache,
  clearCache,
  getCacheStats
};

