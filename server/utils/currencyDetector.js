/**
 * Currency Detection Utility
 * Detects user's preferred currency based on various signals
 */

const { CURRENCY_RATES, RAZORPAY_SUPPORTED_CURRENCIES } = require('../config/pricingConfig');

/**
 * Get user's currency from request
 * Priority: 1. Query param, 2. Header, 3. IP-based detection, 4. Default
 */
function detectUserCurrency(req) {
  // Priority 1: Explicit currency in query params or body
  if (req.query.currency) {
    const currency = req.query.currency.toUpperCase();
    if (isRazorpaySupported(currency)) {
      return currency;
    }
  }

  if (req.body && req.body.currency) {
    const currency = req.body.currency.toUpperCase();
    if (isRazorpaySupported(currency)) {
      return currency;
    }
  }

  // Priority 2: Accept-Language header
  const acceptLanguage = req.headers['accept-language'] || '';
  const currencyFromLang = detectCurrencyFromLanguage(acceptLanguage);
  if (currencyFromLang) {
    return currencyFromLang;
  }

  // Priority 3: IP-based detection (if available)
  const ip = getClientIP(req);
  if (ip && ip !== 'unknown') {
    const currencyFromIP = detectCurrencyFromIP(ip);
    if (currencyFromIP) {
      return currencyFromIP;
    }
  }

  // Priority 4: CF-IPCountry header (Cloudflare)
  if (req.headers['cf-ipcountry']) {
    const country = req.headers['cf-ipcountry'];
    const currencyFromCountry = getCurrencyFromCountryCode(country);
    if (currencyFromCountry) {
      return currencyFromCountry;
    }
  }

  // Default: USD
  return 'USD';
}

/**
 * Detect currency from Accept-Language header
 */
function detectCurrencyFromLanguage(acceptLanguage) {
  if (!acceptLanguage) return null;

  const lang = acceptLanguage.toLowerCase();

  // Indian languages
  if (lang.includes('en-in') || lang.includes('hi') || lang.includes('ta') || lang.includes('te') || lang.includes('kn') || lang.includes('ml') || lang.includes('gu') || lang.includes('pa') || lang.includes('bn') || lang.includes('or') || lang.includes('as')) {
    return 'INR';
  }

  // US English
  if (lang.includes('en-us') || (lang.includes('en') && !lang.includes('en-in') && !lang.includes('en-gb'))) {
    return 'USD';
  }

  // UK English
  if (lang.includes('en-gb')) {
    return 'GBP';
  }

  // Japanese
  if (lang.includes('ja')) {
    return 'JPY';
  }

  // Russian
  if (lang.includes('ru')) {
    return 'RUB';
  }

  // European languages (default to EUR)
  if (lang.includes('de') || lang.includes('fr') || lang.includes('es') || lang.includes('it') || lang.includes('nl') || lang.includes('pt') || lang.includes('pl') || lang.includes('cs') || lang.includes('sk') || lang.includes('hu') || lang.includes('ro') || lang.includes('bg') || lang.includes('hr') || lang.includes('sr') || lang.includes('sl') || lang.includes('et') || lang.includes('lv') || lang.includes('lt') || lang.includes('fi') || lang.includes('sv') || lang.includes('da') || lang.includes('no') || lang.includes('is') || lang.includes('ga') || lang.includes('mt') || lang.includes('el') || lang.includes('cy')) {
    return 'EUR';
  }

  // Australian English
  if (lang.includes('en-au')) {
    return 'AUD';
  }

  // Canadian English/French
  if (lang.includes('en-ca') || lang.includes('fr-ca')) {
    return 'CAD';
  }

  // Singapore
  if (lang.includes('en-sg') || lang.includes('zh-sg') || lang.includes('ms-sg') || lang.includes('ta-sg')) {
    return 'SGD';
  }

  // UAE
  if (lang.includes('ar-ae')) {
    return 'AED';
  }

  // Saudi Arabia
  if (lang.includes('ar-sa')) {
    return 'SAR';
  }

  return null;
}

/**
 * Detect currency from IP address (simplified - based on common patterns)
 * Note: For production, use a proper IP geolocation service
 */
function detectCurrencyFromIP(ip) {
  // This is a simplified version
  // For production, use services like:
  // - ipapi.co
  // - ip-api.com
  // - maxmind GeoIP2
  // - Cloudflare CF-IPCountry header (already handled above)
  
  // For now, return null and let other methods handle it
  return null;
}

/**
 * Get currency from country code
 */
function getCurrencyFromCountryCode(countryCode) {
  if (!countryCode) return null;

  const countryCurrencyMap = {
    'IN': 'INR',
    'US': 'USD',
    'GB': 'GBP',
    'JP': 'JPY',
    'AU': 'AUD',
    'CA': 'CAD',
    'SG': 'SGD',
    'AE': 'AED',
    'SA': 'SAR',
    'RU': 'RUB',
    // European countries (EUR)
    'DE': 'EUR', 'FR': 'EUR', 'ES': 'EUR', 'IT': 'EUR', 'NL': 'EUR',
    'PT': 'EUR', 'BE': 'EUR', 'AT': 'EUR', 'GR': 'EUR', 'FI': 'EUR',
    'IE': 'EUR', 'LU': 'EUR', 'MT': 'EUR', 'CY': 'EUR', 'SK': 'EUR',
    'SI': 'EUR', 'EE': 'EUR', 'LV': 'EUR', 'LT': 'EUR'
  };

  return countryCurrencyMap[countryCode.toUpperCase()] || null;
}

/**
 * Get client IP from request
 */
function getClientIP(req) {
  return req.headers['x-forwarded-for']?.split(',')[0]?.trim() ||
         req.headers['x-real-ip'] ||
         req.connection?.remoteAddress ||
         req.socket?.remoteAddress ||
         'unknown';
}

/**
 * Check if currency is supported by Razorpay
 */
function isRazorpaySupported(currency) {
  return RAZORPAY_SUPPORTED_CURRENCIES.includes(currency.toUpperCase());
}

/**
 * Get currency symbol
 */
function getCurrencySymbol(currency) {
  const symbols = {
    USD: '$',
    INR: '₹',
    EUR: '€',
    GBP: '£',
    JPY: '¥',
    AUD: 'A$',
    CAD: 'C$',
    SGD: 'S$',
    AED: 'د.إ',
    SAR: '﷼',
    RUB: '₽'
  };
  return symbols[currency.toUpperCase()] || currency;
}

module.exports = {
  detectUserCurrency,
  detectCurrencyFromLanguage,
  detectCurrencyFromIP,
  getCurrencyFromCountryCode,
  getClientIP,
  isRazorpaySupported,
  getCurrencySymbol
};

