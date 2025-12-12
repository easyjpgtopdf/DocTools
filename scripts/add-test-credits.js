// Script to add credits to a user account
// Usage: node scripts/add-test-credits.js <email> [credits]
// Or: ADMIN_EMAIL=<email> ADMIN_CREDITS=<credits> node scripts/add-test-credits.js

const https = require('https');
const http = require('http');

// Email should be provided as command line argument or environment variable
// Usage: node scripts/add-test-credits.js <email> [credits]
// Or: ADMIN_EMAIL=<email> ADMIN_CREDITS=<credits> node scripts/add-test-credits.js
const email = process.argv[2] || process.env.ADMIN_EMAIL;
const credits = parseInt(process.argv[3] || process.env.ADMIN_CREDITS || '100');

// Get API URL
const isDevelopment = process.env.NODE_ENV === 'development' || process.argv.includes('--local');
const API_URL = isDevelopment 
  ? 'http://localhost:3000/api/admin/add-test-credits'
  : 'https://www.easyjpgtopdf.com/api/admin/add-test-credits';

const postData = JSON.stringify({
  email: email,
  credits: credits
});

const url = new URL(API_URL);
const options = {
  hostname: url.hostname,
  port: url.port || (url.protocol === 'https:' ? 443 : 80),
  path: url.pathname,
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Content-Length': Buffer.byteLength(postData)
  }
};

const client = url.protocol === 'https:' ? https : http;

if (!email) {
  console.error('❌ ERROR: Email is required');
  console.log('Usage: node scripts/add-test-credits.js <email> [credits]');
  console.log('   Or: ADMIN_EMAIL=<email> ADMIN_CREDITS=<credits> node scripts/add-test-credits.js');
  process.exit(1);
}

console.log(`Adding ${credits} credits to ${email}...`);
console.log(`API URL: ${API_URL}`);

const req = client.request(options, (res) => {
  let data = '';

  res.on('data', (chunk) => {
    data += chunk;
  });

  res.on('end', () => {
    try {
      const response = JSON.parse(data);
      
      if (response.success) {
        console.log('\n✅ SUCCESS!');
        console.log(`Credits added: ${response.credits.added}`);
        console.log(`Before: ${response.credits.before}`);
        console.log(`After: ${response.credits.after}`);
        console.log(`User: ${response.user.email} (${response.user.userId})`);
      } else {
        console.error('\n❌ ERROR:', response.error || response.message);
        process.exit(1);
      }
    } catch (error) {
      console.error('\n❌ Failed to parse response:', error);
      console.log('Response:', data);
      process.exit(1);
    }
  });
});

req.on('error', (error) => {
  console.error('\n❌ Request error:', error.message);
  process.exit(1);
});

req.write(postData);
req.end();

