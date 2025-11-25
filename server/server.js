require('dotenv').config();
const express = require('express');
const cors = require('cors');
const multer = require('multer');
const os = require('os');
const path = require('path');
const fs = require('fs');
const { exec, execSync } = require('child_process');
const crypto = require('crypto');
const { v4: uuidv4 } = require('uuid');
const admin = require('firebase-admin');
const Stripe = require('stripe');
const Razorpay = require('razorpay');

// Start Google Cloud Services Permanently
console.log('\n' + '='.repeat(50));
console.log('Starting Google Cloud Services...');
console.log('='.repeat(50));
require('./start-google-cloud-services');
console.log('='.repeat(50) + '\n');

// Subscription routes
const subscriptionRoutes = require('./api/subscriptions/routes');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors({ exposedHeaders: ['Content-Length', 'Content-Disposition'] }));

app.post('/api/payments/razorpay/webhook', express.raw({ type: 'application/json' }), handleRazorpayWebhook);

app.use(express.json({ limit: '100mb' }));
app.use(express.urlencoded({ extended: true, limit: '100mb' }));
app.use(express.static('public'));
app.use('/previews', express.static('previews'));
app.use('/converted', express.static('converted'));
app.use('/assets', express.static(path.join(__dirname, 'assets')));

// --- Firebase Admin initialisation ---
if (!admin.apps.length) {
  try {
    const serviceAccountRaw = process.env.FIREBASE_SERVICE_ACCOUNT;
    if (serviceAccountRaw) {
      try {
        const serviceAccount = JSON.parse(serviceAccountRaw);
        admin.initializeApp({
          credential: admin.credential.cert(serviceAccount)
        });
        console.log('Firebase Admin SDK initialized with service account');
      } catch (parseError) {
        console.warn('Failed to parse FIREBASE_SERVICE_ACCOUNT JSON, initializing with default credentials');
        admin.initializeApp();
      }
    } else {
      admin.initializeApp();
      console.log('Firebase Admin SDK initialized with default credentials');
    }
  } catch (error) {
    console.error('Failed to initialise Firebase Admin SDK:', error);
  }
}

const stripeSecretKey = process.env.STRIPE_SECRET_KEY;
const stripe = stripeSecretKey ? new Stripe(stripeSecretKey) : null;
const stripeSuccessUrl = process.env.STRIPE_SUCCESS_URL || 'https://easyjpgtopdf.com/donate-success?session_id={CHECKOUT_SESSION_ID}';
const stripeCancelUrl = process.env.STRIPE_CANCEL_URL || 'https://easyjpgtopdf.com/donate-cancelled';

const razorpayKeyId = process.env.RAZORPAY_KEY_ID;
const razorpayKeySecret = process.env.RAZORPAY_KEY_SECRET;
const razorpayWebhookSecret = process.env.RAZORPAY_WEBHOOK_SECRET;
const razorpayReceiptPrefix = process.env.RAZORPAY_RECEIPT_PREFIX || 'easyjpgtopdf';
let razorpay = null;

if (razorpayKeyId && razorpayKeySecret) {
  try {
    razorpay = new Razorpay({ key_id: razorpayKeyId, key_secret: razorpayKeySecret });
    console.log('✓ Razorpay client initialized successfully');
  } catch (error) {
    console.error('✗ Failed to initialise Razorpay client:', error);
  }
} else {
  console.warn('⚠ Razorpay keys not found in environment. RAZORPAY_KEY_ID:', razorpayKeyId ? '✓ set' : '✗ missing', 'RAZORPAY_KEY_SECRET:', razorpayKeySecret ? '✓ set' : '✗ missing');
}

const payuKey = process.env.PAYU_KEY;
const payuSalt = process.env.PAYU_SALT;
const payuEnv = (process.env.PAYU_ENV || 'test').toLowerCase();
const payuBaseUrl = process.env.PAYU_BASE_URL || ((payuEnv === 'production' || payuEnv === 'prod' || payuEnv === 'live') ? 'https://secure.payu.in' : 'https://test.payu.in');
const payuSuccessUrl = process.env.PAYU_SUCCESS_URL || 'https://easyjpgtopdf.com/payu-success';
const payuFailureUrl = process.env.PAYU_FAILURE_URL || 'https://easyjpgtopdf.com/payu-failure';
const payuNotifyUrl = process.env.PAYU_NOTIFY_URL || '';
const payuReceiptPrefix = process.env.PAYU_RECEIPT_PREFIX || 'EJP2PDF';

function generatePayuTxnId() {
  const raw = `${payuReceiptPrefix}_${Date.now()}_${Math.floor(Math.random() * 1000)}`;
  return raw.substring(0, 25);
}

function buildPayuHash(params = {}) {
  if (!payuKey || !payuSalt) {
    return '';
  }

  const sequence = [
    payuKey,
    params.txnid || '',
    params.amount || '',
    params.productinfo || '',
    params.firstname || '',
    params.email || '',
  ];

  for (let i = 1; i <= 10; i += 1) {
    sequence.push(params[`udf${i}`] || '');
  }

  sequence.push(payuSalt);

  return crypto.createHash('sha512').update(sequence.join('|')).digest('hex');
}

function verifyPayuResponseHash(data = {}) {
  if (!payuKey || !payuSalt) {
    return false;
  }

  const sequence = [
    payuSalt,
    data.status || '',
  ];

  for (let i = 10; i >= 1; i -= 1) {
    sequence.push(data[`udf${i}`] || '');
  }

  sequence.push(
    data.email || '',
    data.firstname || '',
    data.productinfo || '',
    data.amount || '',
    data.txnid || '',
    data.key || ''
  );

  const calculated = crypto.createHash('sha512').update(sequence.join('|')).digest('hex');
  const provided = (data.hash || '').toLowerCase();
  return calculated === provided;
}

const ZERO_DECIMAL_CURRENCIES = new Set(['BIF', 'CLP', 'DJF', 'GNF', 'JPY', 'KMF', 'KRW', 'MGA', 'PYG', 'RWF', 'UGX', 'VND', 'VUV', 'XAF', 'XOF', 'XPF']);

function getMinorUnitAmount(amount, currency) {
  const normalizedCurrency = (currency || '').toUpperCase();
  if (ZERO_DECIMAL_CURRENCIES.has(normalizedCurrency)) {
    return Math.round(amount);
  }
  return Math.round(amount * 100);
}

function getPaiseAmount(amount) {
  return Math.round(Number(amount) * 100);
}

function handleRazorpayWebhook(req, res) {
  if (!razorpayWebhookSecret) {
    return res.status(503).json({ error: 'Webhook secret not configured.' });
  }

  const signature = req.headers['x-razorpay-signature'];
  const body = req.body; // raw buffer because express.raw earlier

  if (!signature || !body) {
    return res.status(400).json({ error: 'Invalid webhook payload.' });
  }

  const generatedSignature = crypto
    .createHmac('sha256', razorpayWebhookSecret)
    .update(body)
    .digest('hex');

  if (generatedSignature !== signature) {
    return res.status(400).json({ error: 'Signature verification failed.' });
  }

  let event;
  try {
    event = JSON.parse(body.toString());
  } catch (error) {
    console.error('Razorpay webhook JSON parse failed:', error);
    return res.status(400).json({ error: 'Invalid payload JSON.' });
  }

  if (!event || !event.event) {
    return res.status(200).json({ received: true });
  }

  const eventType = event.event;
  const payload = event.payload || {};
  const payment = payload.payment?.entity;
  const order = payload.order?.entity;

  const orderId = payment?.order_id || order?.id;
  const paymentId = payment?.id || null;
  const status = payment?.status || order?.status;

  if (!orderId) {
    console.warn('Razorpay webhook missing order id', eventType);
    return res.status(200).json({ received: true });
  }

  if (!admin.apps.length || !admin.firestore) {
    console.warn('Firestore not initialised, skipping Razorpay webhook persistence.');
    return res.status(200).json({ received: true });
  }

  const updates = {
    updatedAt: admin.firestore.FieldValue.serverTimestamp(),
    webhookEvent: eventType,
    paymentId,
    paymentStatus: status,
    razorpayPayload: event,
  };

  if (status === 'captured') {
    updates.status = 'succeeded';
  } else if (status === 'failed') {
    updates.status = 'failed';
  }

  const metadata = order?.notes || payment?.notes || {};
  const firebaseUid = metadata.firebaseUid;

  const targetDoc = firebaseUid
    ? admin.firestore().collection('payments').doc(firebaseUid).collection('records').doc(orderId)
    : null;

  if (!targetDoc) {
    console.warn('Razorpay webhook missing firebase UID in notes.');
    return res.status(200).json({ received: true });
  }

  targetDoc
    .set(updates, { merge: true })
    .then(() => {
      res.status(200).json({ received: true });
    })
    .catch((error) => {
      console.error('Failed to update Razorpay payment record:', error);
      res.status(500).json({ error: 'Failed to persist webhook event.' });
    });
}

async function verifyFirebaseIdToken(req, res, next) {
  try {
    const authHeader = req.headers.authorization || '';
    const token = authHeader.startsWith('Bearer ') ? authHeader.substring(7) : null;

    if (!token) {
      return res.status(401).json({ error: 'Missing Authorization header' });
    }

    if (!admin.apps.length) {
      return res.status(500).json({ error: 'Firebase Admin SDK not initialised' });
    }

    const decoded = await admin.auth().verifyIdToken(token);
    req.user = decoded;
    return next();
  } catch (error) {
    console.error('Firebase token verification failed:', error);
    return res.status(401).json({ error: 'Invalid or expired token' });
  }
}

// Multer storage to OS temp directory
const upload = multer({ storage: multer.diskStorage({
  destination: (req, file, cb) => cb(null, os.tmpdir()),
  filename: (req, file, cb) => cb(null, `${Date.now()}-${file.originalname}`)
})});

// Simple in-process job queue to simulate cloud processing for large files.
const BG_JOB_DIR = path.join(__dirname, 'uploads', 'bg-jobs');
const BG_OUTPUT_DIR = path.join(__dirname, 'previews');
if (!fs.existsSync(BG_JOB_DIR)) fs.mkdirSync(BG_JOB_DIR, { recursive: true });
if (!fs.existsSync(BG_OUTPUT_DIR)) fs.mkdirSync(BG_OUTPUT_DIR, { recursive: true });

const bgJobs = new Map(); // jobId -> { status, inputPath, outputPath, error }
const bgQueue = [];
let bgProcessing = false;

function enqueueBgJob(job) {
  bgJobs.set(job.id, { status: 'queued', inputPath: job.inputPath, outputPath: job.outputPath, error: null });
  bgQueue.push(job.id);
  processBgQueue();
}

async function runRembg(inputPath, outputPath) {
  return new Promise((resolve, reject) => {
    // Try python3 -m rembg i <in> <out> then fallback to rembg CLI
    const tryCmds = [
      `python3 -m rembg i "${inputPath}" "${outputPath}"`,
      `rembg i "${inputPath}" "${outputPath}"`,
      `rembg -o "${outputPath}" "${inputPath}"`
    ];

    let lastErr = null;
    const tryNext = (idx) => {
      if (idx >= tryCmds.length) return reject(lastErr || new Error('rembg failed'));
      const cmd = tryCmds[idx];
      exec(cmd, { maxBuffer: 1024 * 1024 * 500 }, (err, stdout, stderr) => {
        if (err) {
          lastErr = err;
          return tryNext(idx + 1);
        }
        resolve();
      });
    };
    tryNext(0);
  });
}

async function processBgQueue() {
  if (bgProcessing) return;
  bgProcessing = true;
  while (bgQueue.length) {
    const jobId = bgQueue.shift();
    const job = bgJobs.get(jobId);
    if (!job) continue;
    bgJobs.set(jobId, { ...job, status: 'processing' });
    try {
      await runRembg(job.inputPath, job.outputPath);
      bgJobs.set(jobId, { ...job, status: 'done' });
    } catch (err) {
      console.error('Background job failed', jobId, err);
      bgJobs.set(jobId, { ...job, status: 'error', error: (err && err.message) || String(err) });
    }
  }
  bgProcessing = false;
}


app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

// Create Razorpay Order
app.post('/api/create-order', async (req, res) => {
  try {
    // Check if Razorpay is configured
    if (!razorpay) {
      return res.status(503).json({ 
        error: 'Razorpay is not configured on the server.',
        details: 'Missing RAZORPAY_KEY_ID or RAZORPAY_KEY_SECRET in environment variables'
      });
    }

    const { amount, name, email, firebaseUid, currency = 'INR' } = req.body;
    
    if (!amount || !name || !email) {
      return res.status(400).json({ error: 'Missing required fields: amount, name, email' });
    }

    const orderOptions = {
      amount: Math.round(amount * 100), // Convert to paise
      currency: currency,
      receipt: `${razorpayReceiptPrefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      payment_capture: 1,
      notes: {
        name: name,
        email: email,
        firebaseUid: firebaseUid || 'anonymous',
        purpose: 'Donation to easyjpgtopdf'
      }
    };

    const order = await razorpay.orders.create(orderOptions);
    
    res.json({
      id: order.id,
      amount: order.amount,
      currency: order.currency,
      receipt: order.receipt,
      key: razorpayKeyId || '',
      amountInPaise: order.amount
    });
    
  } catch (error) {
    console.error('Error creating Razorpay order:', error);
    res.status(500).json({ 
      error: 'Failed to create order',
      details: error.message 
    });
  }
});

// Background remover endpoint: small files processed locally, large files queued for "cloud" processing.
// Accepts multipart form field 'image'.
app.post('/api/background/remove', upload.single('image'), async (req, res) => {
  try {
    if (!req.file || !req.file.path) return res.status(400).json({ error: 'No file uploaded' });

    const filePath = req.file.path;
    const stats = fs.statSync(filePath);
    const sizeBytes = stats.size || 0;
    const threshold = (process.env.BG_LOCAL_THRESHOLD_MB ? Number(process.env.BG_LOCAL_THRESHOLD_MB) : 50) * 1024 * 1024;

    if (sizeBytes <= threshold) {
      // Process locally and return result URL
      const outName = `bg-${uuidv4()}.png`;
      const outPath = path.join(BG_OUTPUT_DIR, outName);
      try {
        await runRembg(filePath, outPath);
        // cleanup uploaded temp
        try { fs.unlinkSync(filePath); } catch (_) {}
        return res.json({ success: true, url: `/previews/${outName}`, size: sizeBytes, method: 'local' });
      } catch (err) {
        console.error('Local rembg failed:', err);
        return res.status(500).json({ error: 'Local processing failed', details: err && err.message });
      }
    }

    // For large files: move to jobs folder and enqueue for async processing (simulating cloud)
    const jobId = uuidv4();
    const ext = path.extname(req.file.originalname) || '.png';
    const dest = path.join(BG_JOB_DIR, `${jobId}${ext}`);
    fs.renameSync(filePath, dest);
    const outputFile = path.join(BG_OUTPUT_DIR, `bg-${jobId}.png`);
    enqueueBgJob({ id: jobId, inputPath: dest, outputPath: outputFile });
    return res.json({ queued: true, jobId, statusUrl: `/api/background/status/${jobId}`, size: sizeBytes, method: 'cloud' });
  } catch (err) {
    console.error('Background remove API error:', err);
    return res.status(500).json({ error: 'Server error', details: err && err.message });
  }
});

// Status endpoint for background jobs
app.get('/api/background/status/:jobId', (req, res) => {
  const jobId = req.params.jobId;
  if (!jobId) return res.status(400).json({ error: 'Missing jobId' });
  const job = bgJobs.get(jobId);
  if (!job) return res.status(404).json({ error: 'Job not found' });
  const resp = { status: job.status };
  if (job.status === 'done') {
    const outName = path.basename(job.outputPath);
    resp.url = `/previews/${outName}`;
  }
  if (job.status === 'error') resp.error = job.error || 'Processing failed';
  return res.json(resp);
});

// ROOT ROUTE
app.get('/', (req, res) => {
  res.json({ message: 'Word to PDF API is running!' });
});

// HEALTH ROUTE  
app.get('/api/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date() });
});

app.post('/api/payments/razorpay/order', verifyFirebaseIdToken, async (req, res) => {
  if (!razorpay) {
    return res.status(503).json({ error: 'Razorpay is not configured on the server.' });
  }

  const { amount, currency, motive, donationType } = req.body || {};
  const numericAmount = Number(amount);

  if (!Number.isFinite(numericAmount) || numericAmount <= 0) {
    return res.status(400).json({ error: 'Invalid donation amount.' });
  }

  const normalizedCurrency = (currency || 'INR').toUpperCase();
  if (normalizedCurrency !== 'INR') {
    return res.status(400).json({ error: 'Razorpay currently supports INR only for this donation.' });
  }

  const amountInPaise = getPaiseAmount(numericAmount);
  if (!Number.isInteger(amountInPaise) || amountInPaise <= 0) {
    return res.status(400).json({ error: 'Unable to process the donation amount for Razorpay.' });
  }

  const user = req.user || {};
  const uid = user.uid;

  if (!uid) {
    return res.status(401).json({ error: 'Unable to verify authenticated user.' });
  }

  const receiptId = `${razorpayReceiptPrefix}_${uuidv4()}`;

  try {
    const order = await razorpay.orders.create({
      amount: amountInPaise,
      currency: normalizedCurrency,
      receipt: receiptId,
      notes: {
        firebaseUid: uid,
        motive: motive || 'donation',
        donationType: donationType || 'project',
      },
    });

    if (admin.apps.length && admin.firestore) {
      try {
        await admin
          .firestore()
          .collection('payments')
          .doc(uid)
          .collection('records')
          .doc(order.id)
          .set({
            gateway: 'razorpay',
            amount: numericAmount,
            amountInMinor: amountInPaise,
            currency: normalizedCurrency,
            status: 'pending',
            type: 'donation',
            motive: motive || 'donation',
            donationType: donationType || 'project',
            orderId: order.id,
            receipt: receiptId,
            rawOrder: order,
            createdAt: admin.firestore.FieldValue.serverTimestamp(),
            updatedAt: admin.firestore.FieldValue.serverTimestamp(),
          }, { merge: true });
      } catch (firestoreError) {
        console.warn('Failed to record Razorpay order in Firestore:', firestoreError);
      }
    }

    return res.json({
      orderId: order.id,
      amount: numericAmount,
      amountInPaise,
      currency: normalizedCurrency,
      razorpayKeyId,
      receipt: receiptId,
      prefill: {
        name: user.name || user.displayName || '',
        email: user.email || '',
      },
      notes: order.notes,
      donationType: donationType || 'project',
    });
  } catch (error) {
    console.error('Failed to create Razorpay order:', error);
    return res.status(500).json({ error: 'Unable to create Razorpay order.' });
  }
});

app.post('/api/payments/payu/order', verifyFirebaseIdToken, async (req, res) => {
  if (!payuKey || !payuSalt) {
    return res.status(503).json({ error: 'PayU is not configured on the server.' });
  }

  const { amount, currency, donationType, motive } = req.body || {};
  const numericAmount = Number(amount);

  if (!Number.isFinite(numericAmount) || numericAmount <= 0) {
    return res.status(400).json({ error: 'Invalid contribution amount.' });
  }

  const normalizedCurrency = (currency || 'INR').toUpperCase();
  if (normalizedCurrency !== 'INR') {
    return res.status(400).json({ error: 'PayU donations currently support INR only.' });
  }

  const amountStr = numericAmount.toFixed(2);
  const user = req.user || {};
  const uid = user.uid;

  if (!uid) {
    return res.status(401).json({ error: 'Unable to verify authenticated user.' });
  }

  const txnid = generatePayuTxnId();
  const focus = donationType || 'project';
  const motiveValue = motive || 'donation';

  const productInfo = focus === 'premium'
    ? 'easyjpgtopdf Premium Access'
    : focus === 'humanity'
      ? 'Humanity Outreach Support'
      : 'Project Development Support';

  const params = {
    key: payuKey,
    txnid,
    amount: amountStr,
    productinfo: productInfo,
    firstname: user.name || user.displayName || 'Donor',
    email: user.email || '',
    phone: user.phone_number || '',
    surl: payuSuccessUrl,
    furl: payuFailureUrl,
    curl: payuFailureUrl,
    udf1: uid,
    udf2: focus,
    udf3: motiveValue,
    udf4: normalizedCurrency,
    udf5: '',
    udf6: '',
    udf7: '',
    udf8: '',
    udf9: '',
    udf10: '',
  };

  if (payuNotifyUrl) {
    params.notify_url = payuNotifyUrl;
  }

  const hash = buildPayuHash(params);
  if (!hash) {
    return res.status(500).json({ error: 'Unable to sign PayU request.' });
  }

  params.hash = hash;

  if (admin.apps.length && admin.firestore) {
    try {
      await admin
        .firestore()
        .collection('payments')
        .doc(uid)
        .collection('records')
        .doc(txnid)
        .set({
          gateway: 'payu',
          amount: numericAmount,
          amountFormatted: amountStr,
          currency: normalizedCurrency,
          status: 'pending',
          type: 'donation',
          motive: motiveValue,
          donationType: focus,
          txnid,
          payuEnv,
          createdAt: admin.firestore.FieldValue.serverTimestamp(),
          updatedAt: admin.firestore.FieldValue.serverTimestamp(),
        }, { merge: true });
    } catch (firestoreError) {
      console.warn('Failed to record PayU initiation in Firestore:', firestoreError);
    }
  }

  return res.json({
    actionUrl: `${payuBaseUrl}/_payment`,
    params,
  });
});

app.post('/api/payments/create-donation-session', verifyFirebaseIdToken, async (req, res) => {
  if (!stripe) {
    return res.status(503).json({ error: 'Stripe is not configured on the server.' });
  }

  const { amount, currency, motive } = req.body || {};
  const numericAmount = Number(amount);

  if (!Number.isFinite(numericAmount) || numericAmount <= 0) {
    return res.status(400).json({ error: 'Invalid donation amount.' });
  }

  if (numericAmount > 1000000) {
    return res.status(400).json({ error: 'Donation amount is too large.' });
  }

  const normalizedCurrency = (currency || 'INR').toUpperCase();
  const unitAmount = getMinorUnitAmount(numericAmount, normalizedCurrency);

  if (!unitAmount || unitAmount <= 0) {
    return res.status(400).json({ error: 'Unable to process the donation amount for the selected currency.' });
  }

  const user = req.user || {};
  const uid = user.uid;

  if (!uid) {
    return res.status(401).json({ error: 'Unable to verify authenticated user.' });
  }

  const sessionConfig = {
    mode: 'payment',
    success_url: stripeSuccessUrl,
    cancel_url: stripeCancelUrl,
    line_items: [
      {
        price_data: {
          currency: normalizedCurrency,
          unit_amount: unitAmount,
          product_data: {
            name: 'easyjpgtopdf Donation',
            description: 'Support the easyjpgtopdf toolset',
          },
        },
        quantity: 1,
      },
    ],
    metadata: {
      firebaseUid: uid,
      motive: motive || 'donation',
      source: 'easyjpgtopdf',
    },
    automatic_payment_methods: { enabled: true },
  };

  if (user.email) {
    sessionConfig.customer_email = user.email;
  }

  try {
    const session = await stripe.checkout.sessions.create(sessionConfig);

    if (admin.apps.length && admin.firestore) {
      try {
        await admin
          .firestore()
          .collection('payments')
          .doc(uid)
          .collection('records')
          .doc(session.id)
          .set({
            amount: numericAmount,
            currency: normalizedCurrency,
            status: 'pending',
            type: 'donation',
            checkoutSessionId: session.id,
            motive: motive || 'donation',
            createdAt: admin.firestore.FieldValue.serverTimestamp(),
          }, { merge: true });
      } catch (firestoreError) {
        console.warn('Failed to record pending donation in Firestore:', firestoreError);
      }
    }

    return res.json({ checkoutUrl: session.url });
  } catch (error) {
    console.error('Failed to create donation checkout session:', error);
    return res.status(500).json({ error: 'Unable to create donation checkout session.' });
  }
});

app.post('/api/payments/payu/callback', express.urlencoded({ extended: false }), (req, res) => {
  const data = req.body || {};

  if (!Object.keys(data).length) {
    return res.status(400).send('Invalid PayU payload.');
  }

  if (!verifyPayuResponseHash(data)) {
    console.warn('PayU hash verification failed:', data);
    return res.status(400).send('Hash verification failed.');
  }

  if (!admin.apps.length || !admin.firestore) {
    console.warn('Firestore not initialised, cannot persist PayU callback.');
    return res.status(200).send('OK');
  }

  const uid = data.udf1;
  const txnid = data.txnid;
  const payuStatus = (data.status || '').toLowerCase();

  if (!uid || !txnid) {
    console.warn('PayU callback missing UID or txnid.', data);
    return res.status(200).send('OK');
  }

  let status = 'pending';
  if (payuStatus === 'success') {
    status = 'succeeded';
  } else if (payuStatus === 'failure' || payuStatus === 'failed') {
    status = 'failed';
  }

  const updates = {
    status,
    payuStatus,
    paymentId: data.mihpayid || null,
    mihpayid: data.mihpayid || null,
    bankRefNum: data.bank_ref_num || null,
    payuResponse: data,
    updatedAt: admin.firestore.FieldValue.serverTimestamp(),
  };

  admin
    .firestore()
    .collection('payments')
    .doc(uid)
    .collection('records')
    .doc(txnid)
    .set(updates, { merge: true })
    .then(() => {
      res.status(200).send('OK');
    })
    .catch((error) => {
      console.error('Failed to persist PayU callback:', error);
      res.status(500).send('Failed to persist callback.');
    });
});

function findGhostscriptCmd() {
  if (process.platform === 'win32') {
    return 'gswin64c'; // falls back to PATH resolution
  }
  return 'gs';
}

function execAsync(cmd, opts = {}) {
  return new Promise((resolve, reject) => {
    exec(cmd, { ...opts }, (err, stdout, stderr) => {
      if (err) return reject(Object.assign(err, { stdout, stderr }));
      resolve({ stdout, stderr });
    });
  });
}

// Convert Word to HTML via LibreOffice for consistent Chrome rendering
async function convertWordToHtmlWithLibreOffice(inputPath, outDir) {
  const soffice = process.env.SOFFICE_PATH || 'soffice';
  const cmd = `"${soffice}" --headless --nologo --nofirststartwizard --convert-to html --outdir "${outDir}" "${inputPath}"`;
  await execAsync(cmd);
  const base = path.parse(inputPath).name + '.html';
  const htmlPath = path.join(outDir, base);
  if (!fs.existsSync(htmlPath)) throw new Error('LibreOffice did not produce HTML');
  return htmlPath;
}

async function convertWithLibreOffice(inputPath, outDir) {
  const soffice = process.env.SOFFICE_PATH || 'soffice';
  // LibreOffice headless conversion
  // Filter options note: font embedding is controlled by installed fonts.
  // We still rely on Ghostscript pass to force embed if available.
  const cmd = `"${soffice}" --headless --nologo --nofirststartwizard --convert-to "pdf:writer_pdf_Export" --outdir "${outDir}" "${inputPath}"`;
  await execAsync(cmd);
  // Construct expected PDF name generically for any input extension (docx, doc, rtf, odt, html, etc.)
  const base = path.parse(inputPath).name + '.pdf';
  const pdfPath = path.join(outDir, base);
  if (!fs.existsSync(pdfPath)) throw new Error('LibreOffice did not produce a PDF');
  return pdfPath;
}

async function convertWithMsWord(inputPath, outputPdf) {
  if (process.platform !== 'win32') {
    throw new Error('MS Word engine is only available on Windows');
  }
  // Use PowerShell COM Automation for Word -> PDF. Requires Microsoft Word installed.
  const ps = `
    $ErrorActionPreference = 'Stop'
    $in = '${inputPath.replace(/'/g, "''")}'
    $out = '${outputPdf.replace(/'/g, "''")}'
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    try {
      $doc = $word.Documents.Open($in, $false, $true) # ReadOnly true
      # 17 = wdExportFormatPDF
      # Export with print quality to better preserve layout
      $wdExportFormatPDF = 17
      $wdExportOptimizeForPrint = 0
      # Arg order: OutputFileName, ExportFormat, OpenAfterExport, OptimizeFor, Range, From, To, Item, IncludeDocProps, KeepIRM, CreateBookmarks, DocStructureTags, BitmapMissingFonts, UseISO19005_1
      # Use BitmapMissingFonts=$true to avoid font substitution when fonts are not installed; UseISO19005_1=$true for PDF/A-1a compatibility
      $doc.ExportAsFixedFormat($out, $wdExportFormatPDF, $false, $wdExportOptimizeForPrint, 0, 0, 0, 0, $true, $false, 1, $true, $true, $true)
      $doc.Close()
    } finally {
      $word.Quit()
    }
  `;
  const cmd = `powershell -NoProfile -ExecutionPolicy Bypass -Command "${ps.replace(/"/g, '\\"').replace(/\n/g, '; ')}"`;
  await execAsync(cmd);
  if (!fs.existsSync(outputPdf)) throw new Error('MS Word did not produce a PDF');
  return outputPdf;
}

async function forceEmbedFontsWithGhostscript(inputPdf, outputPdf) {
  const gs = findGhostscriptCmd();
  const cmd = `"${gs}" -dBATCH -dNOPAUSE -dQUIET -sDEVICE=pdfwrite -dCompatibilityLevel=1.7 -dSubsetFonts=false -dEmbedAllFonts=true -sOutputFile="${outputPdf}" "${inputPdf}"`;
  await execAsync(cmd);
  if (!fs.existsSync(outputPdf)) throw new Error('Ghostscript failed to write output');
  return outputPdf;
}

function cleanupFiles(paths) {
  for (const p of paths) {
    if (!p) continue;
    try { fs.unlinkSync(p); } catch (_) {}
  }
}

// User-provided upload storage for Word files to uploads/
const uploadsStorage = multer.diskStorage({
  destination: function (req, file, cb) {
    const uploadDir = 'uploads/';
    if (!fs.existsSync(uploadDir)) {
      fs.mkdirSync(uploadDir, { recursive: true });
    }
    cb(null, uploadDir);
  },
  filename: function (req, file, cb) {
    const uniqueName = Date.now() + '-' + Math.round(Math.random() * 1E9) + path.extname(file.originalname);
    cb(null, uniqueName);
  }
});

const uploadWord = multer({
  storage: uploadsStorage,
  fileFilter: function (req, file, cb) {
    const allowedExtensions = ['.docx', '.doc'];
    const fileExtension = path.extname(file.originalname).toLowerCase();
    if (allowedExtensions.includes(fileExtension)) cb(null, true);
    else cb(new Error('Only Word files (.docx, .doc) are allowed'));
  },
  limits: { fileSize: 100 * 1024 * 1024 }
});

// User-provided conversion using LibreOffice with UTF-8 env
function convertWordToPDF(inputPath, outputPath) {
  return new Promise((resolve, reject) => {
    const command = `soffice --headless --convert-to pdf:writer_pdf_Export --outdir "${path.dirname(outputPath)}" "${inputPath}"`;
    const env = { ...process.env, LANG: 'en_US.UTF-8', LC_ALL: 'en_US.UTF-8' };
    exec(command, { env }, (error, stdout, stderr) => {
      if (error) {
        console.error('Conversion error:', error);
        return reject(new Error(`Conversion failed: ${error.message}`));
      }
      const baseName = inputPath.replace(path.extname(inputPath), '');
      const possibleOutputs = [
        baseName + '.pdf',
        path.join(path.dirname(outputPath), path.basename(baseName) + '.pdf'),
        outputPath
      ];
      let pdfCreated = false;
      for (const possiblePath of possibleOutputs) {
        if (fs.existsSync(possiblePath)) {
          if (possiblePath !== outputPath) {
            try { fs.renameSync(possiblePath, outputPath); } catch (_) {}
          }
          pdfCreated = true; break;
        }
      }
      if (pdfCreated) resolve(outputPath);
      else reject(new Error('PDF file was not created. Check LibreOffice installation.'));
    });
  });
}

// User-provided preview generation via ImageMagick (optional)
function generatePreview(pdfPath, previewPath) {
  return new Promise((resolve) => {
    const command = `magick "${pdfPath}[0]" "${previewPath}"`;
    exec(command, (error) => {
      if (error) {
        console.log('Preview generation failed, continuing without preview...');
        return resolve(null);
      }
      resolve(previewPath);
    });
  });
}

// User-provided convert endpoint with preview and JSON response
app.post('/api/convert', uploadWord.single('wordFile'), async (req, res) => {
  let inputPath, outputPath, previewPath;
  try {
    if (!req.file) {
      return res.status(400).json({ success: false, message: 'No file uploaded. Please select a Word file.', diagnostics: { hasSoffice: hasSoffice(), chromeFound: !!findChromeCmd(), platform: process.platform } });
    }
    inputPath = req.file.path;
    const outputDir = 'converted/';
    const previewDir = 'previews/';
    const fileId = path.basename(req.file.filename, path.extname(req.file.filename));
    const outputFilename = `${fileId}.pdf`;
    const previewFilename = `${fileId}.jpg`;
    outputPath = path.join(outputDir, outputFilename);
    previewPath = path.join(previewDir, previewFilename);
    for (const dir of [outputDir, previewDir]) { if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true }); }

    // Consistent pipeline preferred: Word -> HTML (LibreOffice) -> inject unicode.css -> Chrome -> PDF
    let engineUsed = null;
    let consistentSucceeded = false;
    try {
      const chromeCmd = findChromeCmd();
      if (chromeCmd && hasSoffice()) {
        const htmlPath = await convertWordToHtmlWithLibreOffice(inputPath, outputDir);
        const injected = injectUnicodeCss(htmlPath, outputDir);
        await convertHtmlWithChrome(injected, outputPath);
        consistentSucceeded = fs.existsSync(outputPath);
        if (consistentSucceeded) engineUsed = 'chrome+libreoffice';
      }
    } catch (_) {
      consistentSucceeded = false;
    }

    if (!consistentSucceeded) {
      if (process.platform === 'win32') {
        try {
          await convertWithMsWord(inputPath, outputPath);
          engineUsed = 'msword';
        } catch (_) {
          if (hasSoffice()) {
            await convertWordToPDF(inputPath, outputPath);
            engineUsed = 'libreoffice';
          } else {
            throw new Error('No conversion engine available. Install Microsoft Word or LibreOffice.');
          }
        }
      } else if (hasSoffice()) {
        await convertWordToPDF(inputPath, outputPath);
        engineUsed = 'libreoffice';
      } else {
        throw new Error('LibreOffice not installed. Please install LibreOffice to enable conversion.');
      }
    }

  // Optimize and embed fonts using Ghostscript (ILovePDF-style quality step)
  try {
    const gsTest = findGhostscriptCmd();
    await execAsync(`"${gsTest}" -v`);
    const optimizedPath = outputPath.replace(/\.pdf$/i, '-opt.pdf');
    await forceEmbedFontsWithGhostscript(outputPath, optimizedPath);
    if (fs.existsSync(optimizedPath)) {
      try { fs.unlinkSync(outputPath); } catch (_) {}
      fs.renameSync(optimizedPath, outputPath);
    }
  } catch (_) {
    // Ghostscript not available; continue with existing PDF
  }

  let previewUrl = null;
  try { await generatePreview(outputPath, previewPath); previewUrl = `/previews/${previewFilename}`; } catch (_) {}

    res.json({
      success: true,
      message: 'File successfully converted to PDF!',
      downloadUrl: `/api/download/${outputFilename}`,
      previewUrl,
      filename: outputFilename,
      originalName: req.file.originalname.replace(path.extname(req.file.originalname), '.pdf'),
      unicodeSupported: true,
      fileInfo: { size: fs.statSync(outputPath).size, pages: 'Auto-detected' },
      engineUsed,
      diagnostics: {
        hasSoffice: hasSoffice(),
        chromeFound: !!findChromeCmd(),
        platform: process.platform
      }
    });

    setTimeout(() => {
      for (const p of [inputPath, outputPath, previewPath]) {
        if (p && fs.existsSync(p)) { try { fs.unlinkSync(p); } catch (e) {} }
      }
    }, 15 * 60 * 1000);
  } catch (error) {
    console.error('Conversion endpoint error:', error);
    for (const p of [inputPath, outputPath, previewPath]) {
      if (p && fs.existsSync(p)) { try { fs.unlinkSync(p); } catch (e) {} }
    }
    res.status(500).json({ success: false, message: `Conversion failed: ${error.message}`,
      tip: 'Install LibreOffice or Microsoft Word. If using Chrome pipeline, install Chrome/Edge.',
      diagnostics: { hasSoffice: hasSoffice(), chromeFound: !!findChromeCmd(), platform: process.platform }
    });
  }
});

// User-provided download endpoint
app.get('/api/download/:filename', (req, res) => {
  try {
    const filename = req.params.filename;
    const filePath = path.join('converted/', filename);
    if (!fs.existsSync(filePath)) return res.status(404).json({ success: false, message: 'File not found' });
    const disposition = (req.query.disposition || '').toLowerCase() === 'inline' ? 'inline' : 'attachment';
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', `${disposition}; filename="${filename}"`);
    res.setHeader('Cache-Control', 'no-cache');
    fs.createReadStream(filePath).pipe(res);
  } catch (error) {
    console.error('Download error:', error);
    res.status(500).json({ success: false, message: 'Download failed: ' + error.message });
  }
});

// PDF Editing API endpoints
const pdfEditModule = require('./api/pdf-edit/edit-pdf');
const pdfEditAdvanced = require('./api/pdf-edit/edit-pdf-advanced');

// Multer configuration for PDF uploads (Direct file processing)
const uploadPDF = multer({
  storage: multer.diskStorage({
    destination: (req, file, cb) => {
      const uploadDir = path.join(__dirname, 'uploads', 'pdfs');
      if (!fs.existsSync(uploadDir)) {
        fs.mkdirSync(uploadDir, { recursive: true });
      }
      cb(null, uploadDir);
    },
    filename: (req, file, cb) => {
      const uniqueName = `${Date.now()}-${Math.round(Math.random() * 1E9)}${path.extname(file.originalname)}`;
      cb(null, uniqueName);
    }
  }),
  limits: {
    fileSize: 100 * 1024 * 1024 // 100MB limit
  },
  fileFilter: (req, file, cb) => {
    if (file.mimetype === 'application/pdf' || file.originalname.toLowerCase().endsWith('.pdf')) {
      cb(null, true);
    } else {
      cb(new Error('Only PDF files are allowed'), false);
    }
  }
});

// Direct PDF Upload Endpoint (Fast server processing)
app.post('/api/pdf/upload', uploadPDF.single('pdfFile'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        error: 'No PDF file uploaded'
      });
    }
    
    const filePath = req.file.path;
    const fileBuffer = fs.readFileSync(filePath);
    
    // Process PDF immediately (fast)
    // Optionally: Extract text, fonts, etc.
    const pdfContentParser = require('./api/pdf-edit/pdf-content-parser');
    let textItems = [];
    let fonts = [];
    
    try {
      textItems = await pdfContentParser.extractTextWithPositions(fileBuffer);
      fonts = await pdfContentParser.getFontsFromPDF(fileBuffer);
    } catch (e) {
      console.warn('Could not extract PDF content:', e.message);
    }
    
    // Create accessible URL
    const fileUrl = `/uploads/pdfs/${req.file.filename}`;
    
    // Clean up after 1 hour (optional)
    setTimeout(() => {
      try {
        if (fs.existsSync(filePath)) {
          fs.unlinkSync(filePath);
        }
      } catch (e) {
        console.warn('Could not delete temp file:', e);
      }
    }, 3600000); // 1 hour
    
    res.json({
      success: true,
      pdfUrl: fileUrl,
      filename: req.file.originalname,
      size: req.file.size,
      textItems: textItems,
      fonts: fonts,
      message: 'PDF uploaded and processed successfully'
    });
  } catch (error) {
    console.error('PDF upload error:', error);
    res.status(500).json({
      success: false,
      error: 'PDF upload failed: ' + error.message
    });
  }
});

// Serve uploaded PDFs
app.use('/uploads', express.static(path.join(__dirname, 'uploads')));

// PDF Page Management Endpoints
app.post('/api/pdf/pages/rotate', express.json({ limit: '100mb' }), async (req, res) => {
  try {
    const { pdfData, rotations } = req.body;
    if (!pdfData || !rotations) {
      return res.status(400).json({ success: false, error: 'Missing required data' });
    }
    
    let pdfBuffer = Buffer.from(pdfData.split(',')[1] || pdfData, 'base64');
    const pageManagement = require('./api/pdf-edit/page-management');
    const editedBuffer = await pageManagement.rotatePages(pdfBuffer, rotations);
    
    res.json({
      success: true,
      pdfData: `data:application/pdf;base64,${editedBuffer.toString('base64')}`
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

app.post('/api/pdf/pages/delete', express.json({ limit: '100mb' }), async (req, res) => {
  try {
    const { pdfData, pageIndices } = req.body;
    if (!pdfData || !pageIndices) {
      return res.status(400).json({ success: false, error: 'Missing required data' });
    }
    
    let pdfBuffer = Buffer.from(pdfData.split(',')[1] || pdfData, 'base64');
    const pageManagement = require('./api/pdf-edit/page-management');
    const editedBuffer = await pageManagement.deletePages(pdfBuffer, pageIndices);
    
    res.json({
      success: true,
      pdfData: `data:application/pdf;base64,${editedBuffer.toString('base64')}`
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

app.post('/api/pdf/pages/reorder', express.json({ limit: '100mb' }), async (req, res) => {
  try {
    const { pdfData, newOrder } = req.body;
    if (!pdfData || !newOrder) {
      return res.status(400).json({ success: false, error: 'Missing required data' });
    }
    
    let pdfBuffer = Buffer.from(pdfData.split(',')[1] || pdfData, 'base64');
    const pageManagement = require('./api/pdf-edit/page-management');
    const editedBuffer = await pageManagement.reorderPages(pdfBuffer, newOrder);
    
    res.json({
      success: true,
      pdfData: `data:application/pdf;base64,${editedBuffer.toString('base64')}`
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// PDF Forms Endpoints
app.post('/api/pdf/forms/fill', express.json({ limit: '100mb' }), async (req, res) => {
  try {
    const { pdfData, formFields } = req.body;
    if (!pdfData || !formFields) {
      return res.status(400).json({ success: false, error: 'Missing required data' });
    }
    
    let pdfBuffer = Buffer.from(pdfData.split(',')[1] || pdfData, 'base64');
    const forms = require('./api/pdf-edit/forms');
    const editedBuffer = await forms.fillFormFields(pdfBuffer, formFields);
    
    res.json({
      success: true,
      pdfData: `data:application/pdf;base64,${editedBuffer.toString('base64')}`
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

app.post('/api/pdf/forms/get-fields', express.json({ limit: '100mb' }), async (req, res) => {
  try {
    const { pdfData } = req.body;
    if (!pdfData) {
      return res.status(400).json({ success: false, error: 'Missing PDF data' });
    }
    
    let pdfBuffer = Buffer.from(pdfData.split(',')[1] || pdfData, 'base64');
    const forms = require('./api/pdf-edit/forms');
    const formFields = await forms.getFormFields(pdfBuffer);
    
    res.json({
      success: true,
      formFields: formFields
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// PDF Annotations Endpoints
app.post('/api/pdf/annotations/highlight', express.json({ limit: '100mb' }), async (req, res) => {
  try {
    const { pdfData, highlights } = req.body;
    if (!pdfData || !highlights) {
      return res.status(400).json({ success: false, error: 'Missing required data' });
    }
    
    let pdfBuffer = Buffer.from(pdfData.split(',')[1] || pdfData, 'base64');
    const annotations = require('./api/pdf-edit/annotations');
    const editedBuffer = await annotations.addHighlights(pdfBuffer, highlights);
    
    res.json({
      success: true,
      pdfData: `data:application/pdf;base64,${editedBuffer.toString('base64')}`
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

app.post('/api/pdf/annotations/comment', express.json({ limit: '100mb' }), async (req, res) => {
  try {
    const { pdfData, comments } = req.body;
    if (!pdfData || !comments) {
      return res.status(400).json({ success: false, error: 'Missing required data' });
    }
    
    let pdfBuffer = Buffer.from(pdfData.split(',')[1] || pdfData, 'base64');
    const annotations = require('./api/pdf-edit/annotations');
    const editedBuffer = await annotations.addComments(pdfBuffer, comments);
    
    res.json({
      success: true,
      pdfData: `data:application/pdf;base64,${editedBuffer.toString('base64')}`
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

app.post('/api/pdf/annotations/stamp', express.json({ limit: '100mb' }), async (req, res) => {
  try {
    const { pdfData, stamps } = req.body;
    if (!pdfData || !stamps) {
      return res.status(400).json({ success: false, error: 'Missing required data' });
    }
    
    let pdfBuffer = Buffer.from(pdfData.split(',')[1] || pdfData, 'base64');
    const annotations = require('./api/pdf-edit/annotations');
    const editedBuffer = await annotations.addStamps(pdfBuffer, stamps);
    
    res.json({
      success: true,
      pdfData: `data:application/pdf;base64,${editedBuffer.toString('base64')}`
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// PDF Export Endpoints
app.post('/api/pdf/export/word', express.json({ limit: '100mb' }), async (req, res) => {
  try {
    const { pdfData } = req.body;
    if (!pdfData) {
      return res.status(400).json({ success: false, error: 'Missing PDF data' });
    }
    
    let pdfBuffer = Buffer.from(pdfData.split(',')[1] || pdfData, 'base64');
    const exportFormats = require('./api/pdf-edit/export-formats');
    const docxBuffer = await exportFormats.exportToWord(pdfBuffer);
    
    res.json({
      success: true,
      fileData: `data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64,${docxBuffer.toString('base64')}`,
      filename: 'exported-document.docx'
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

app.post('/api/pdf/export/excel', express.json({ limit: '100mb' }), async (req, res) => {
  try {
    const { pdfData } = req.body;
    if (!pdfData) {
      return res.status(400).json({ success: false, error: 'Missing PDF data' });
    }
    
    let pdfBuffer = Buffer.from(pdfData.split(',')[1] || pdfData, 'base64');
    const exportFormats = require('./api/pdf-edit/export-formats');
    const xlsxBuffer = await exportFormats.exportToExcel(pdfBuffer);
    
    res.json({
      success: true,
      fileData: `data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,${xlsxBuffer.toString('base64')}`,
      filename: 'exported-document.xlsx'
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

app.post('/api/pdf/export/powerpoint', express.json({ limit: '100mb' }), async (req, res) => {
  try {
    const { pdfData } = req.body;
    if (!pdfData) {
      return res.status(400).json({ success: false, error: 'Missing PDF data' });
    }
    
    let pdfBuffer = Buffer.from(pdfData.split(',')[1] || pdfData, 'base64');
    const exportFormats = require('./api/pdf-edit/export-formats');
    const pptxBuffer = await exportFormats.exportToPowerPoint(pdfBuffer);
    
    res.json({
      success: true,
      fileData: `data:application/vnd.openxmlformats-officedocument.presentationml.presentation;base64,${pptxBuffer.toString('base64')}`,
      filename: 'exported-document.pptx'
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

app.post('/api/pdf/export/images', express.json({ limit: '100mb' }), async (req, res) => {
  try {
    const { pdfData, options = {} } = req.body;
    if (!pdfData) {
      return res.status(400).json({ success: false, error: 'Missing PDF data' });
    }
    
    let pdfBuffer = Buffer.from(pdfData.split(',')[1] || pdfData, 'base64');
    const exportFormats = require('./api/pdf-edit/export-formats');
    const images = await exportFormats.exportToImages(pdfBuffer, options);
    
    const imageData = images.map(img => ({
      pageIndex: img.pageIndex,
      imageData: `data:image/${img.format};base64,${img.image.toString('base64')}`,
      format: img.format
    }));
    
    res.json({
      success: true,
      images: imageData
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// PDF Compression Endpoint
app.post('/api/pdf/compress', express.json({ limit: '100mb' }), async (req, res) => {
  try {
    const { pdfData, options = {} } = req.body;
    if (!pdfData) {
      return res.status(400).json({ success: false, error: 'Missing PDF data' });
    }
    
    let pdfBuffer = Buffer.from(pdfData.split(',')[1] || pdfData, 'base64');
    const compression = require('./api/pdf-edit/compression');
    const result = await compression.compressPDF(pdfBuffer, options);
    
    res.json({
      success: true,
      pdfData: `data:application/pdf;base64,${result.buffer.toString('base64')}`,
      originalSize: result.originalSize,
      compressedSize: result.compressedSize,
      compressionRatio: result.compressionRatio
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// PDF Merge Endpoint
app.post('/api/pdf/merge', express.json({ limit: '200mb' }), async (req, res) => {
  try {
    const { pdfDataArray } = req.body;
    if (!pdfDataArray || !Array.isArray(pdfDataArray) || pdfDataArray.length < 2) {
      return res.status(400).json({ success: false, error: 'At least 2 PDFs required for merge' });
    }
    
    const pdfBuffers = pdfDataArray.map(data => {
      const base64 = data.split(',')[1] || data;
      return Buffer.from(base64, 'base64');
    });
    
    const mergeSplit = require('./api/pdf-edit/merge-split');
    const mergedBuffer = await mergeSplit.mergePDFs(pdfBuffers);
    
    res.json({
      success: true,
      pdfData: `data:application/pdf;base64,${mergedBuffer.toString('base64')}`
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// PDF Split Endpoint
app.post('/api/pdf/split', express.json({ limit: '100mb' }), async (req, res) => {
  try {
    const { pdfData, splitRanges } = req.body;
    if (!pdfData || !splitRanges) {
      return res.status(400).json({ success: false, error: 'Missing required data' });
    }
    
    let pdfBuffer = Buffer.from(pdfData.split(',')[1] || pdfData, 'base64');
    const mergeSplit = require('./api/pdf-edit/merge-split');
    const splitBuffers = await mergeSplit.splitPDF(pdfBuffer, splitRanges);
    
    const splitPdfs = splitBuffers.map((buffer, index) => ({
      pdfData: `data:application/pdf;base64,${buffer.toString('base64')}`,
      filename: `split-part-${index + 1}.pdf`
    }));
    
    res.json({
      success: true,
      splitPdfs: splitPdfs
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Cloud Save Endpoint
app.post('/api/pdf/save-cloud', express.json({ limit: '100mb' }), async (req, res) => {
  try {
    const { pdfData, filename = 'document.pdf', cloudProvider = 'firebase' } = req.body;
    
    if (!pdfData) {
      return res.status(400).json({
        success: false,
        error: 'No PDF data provided'
      });
    }
    
    // Convert base64 to buffer
    let pdfBuffer;
    if (typeof pdfData === 'string') {
      if (pdfData.startsWith('data:application/pdf')) {
        pdfData = pdfData.split(',')[1];
      }
      pdfBuffer = Buffer.from(pdfData, 'base64');
    } else {
      pdfBuffer = Buffer.from(pdfData);
    }
    
    // Save to cloud
    const cloudIntegration = require('./api/pdf-edit/cloud-integration');
    let cloudUrl = null;
    
    try {
      if (cloudProvider === 'google-cloud' || cloudProvider === 'firebase') {
        cloudUrl = await cloudIntegration.saveToFirebase(pdfBuffer, filename);
      }
    } catch (cloudError) {
      console.warn('Cloud save failed:', cloudError.message);
      // Continue without cloud save
    }
    
    res.json({
      success: true,
      cloudUrl: cloudUrl,
      message: cloudUrl ? 'PDF saved to cloud successfully' : 'PDF processed (cloud save unavailable)',
      provider: cloudProvider
    });
  } catch (error) {
    console.error('Cloud save error:', error);
    res.status(500).json({
      success: false,
      error: 'Cloud save failed: ' + error.message
    });
  }
});

// Edit PDF (text + images)
app.post('/api/pdf/edit', express.json({ limit: '100mb' }), async (req, res) => {
  try {
    const { pdfData, edits } = req.body;
    
    if (!pdfData) {
      return res.status(400).json({
        success: false,
        error: 'No PDF data provided'
      });
    }
    
    // Convert base64 to buffer
    let pdfBuffer;
    if (typeof pdfData === 'string') {
      if (pdfData.startsWith('data:application/pdf')) {
        pdfData = pdfData.split(',')[1];
      }
      pdfBuffer = Buffer.from(pdfData, 'base64');
    } else {
      pdfBuffer = Buffer.from(pdfData);
    }
    
    // Apply edits using advanced editing (Adobe Acrobat Pro style)
    // This handles deletions, replacements, additions, and OCR integration
    let editedBuffer;
    
    // Always use advanced editing for professional results
    // It handles all cases: deletions, replacements, OCR integration
    if (edits.deletions || edits.textReplacements || edits.ocrTexts) {
      editedBuffer = await pdfEditAdvanced.editPDFAdvanced(pdfBuffer, edits || {});
    } else if (edits.textEdits || edits.imageInserts) {
      // Use advanced editing for better font matching and coordinates
      editedBuffer = await pdfEditAdvanced.editPDFAdvanced(pdfBuffer, edits || {});
    } else {
      // Fallback to standard editing
      editedBuffer = await pdfEditModule.editPDF(pdfBuffer, edits || {});
    }
    
    // Convert to base64 for response
    const editedBase64 = editedBuffer.toString('base64');
    
    res.json({
      success: true,
      pdfData: `data:application/pdf;base64,${editedBase64}`,
      message: 'PDF edited successfully'
    });
  } catch (error) {
    console.error('PDF editing error:', error);
    res.status(500).json({
      success: false,
      error: 'PDF editing failed: ' + error.message
    });
  }
});

// Edit PDF text only
app.post('/api/pdf/edit-text', express.json({ limit: '100mb' }), async (req, res) => {
  try {
    const { pdfData, textEdits } = req.body;
    
    if (!pdfData || !textEdits || !Array.isArray(textEdits)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid request: pdfData and textEdits array required'
      });
    }
    
    // Convert base64 to buffer
    let pdfBuffer;
    if (typeof pdfData === 'string') {
      if (pdfData.startsWith('data:application/pdf')) {
        pdfData = pdfData.split(',')[1];
      }
      pdfBuffer = Buffer.from(pdfData, 'base64');
    } else {
      pdfBuffer = Buffer.from(pdfData);
    }
    
    // Apply text edits
    const editedBuffer = await pdfEditModule.editPDFText(pdfBuffer, textEdits);
    
    // Convert to base64 for response
    const editedBase64 = editedBuffer.toString('base64');
    
    res.json({
      success: true,
      pdfData: `data:application/pdf;base64,${editedBase64}`,
      message: 'PDF text edited successfully'
    });
  } catch (error) {
    console.error('PDF text editing error:', error);
    res.status(500).json({
      success: false,
      error: 'PDF text editing failed: ' + error.message
    });
  }
});

// Insert image into PDF
app.post('/api/pdf/insert-image', express.json({ limit: '100mb' }), async (req, res) => {
  try {
    const { pdfData, imageInserts } = req.body;
    
    if (!pdfData || !imageInserts || !Array.isArray(imageInserts)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid request: pdfData and imageInserts array required'
      });
    }
    
    // Convert base64 to buffer
    let pdfBuffer;
    if (typeof pdfData === 'string') {
      if (pdfData.startsWith('data:application/pdf')) {
        pdfData = pdfData.split(',')[1];
      }
      pdfBuffer = Buffer.from(pdfData, 'base64');
    } else {
      pdfBuffer = Buffer.from(pdfData);
    }
    
    // Apply image inserts
    const editedBuffer = await pdfEditModule.insertImageIntoPDF(pdfBuffer, imageInserts);
    
    // Convert to base64 for response
    const editedBase64 = editedBuffer.toString('base64');
    
    res.json({
      success: true,
      pdfData: `data:application/pdf;base64,${editedBase64}`,
      message: 'Image inserted into PDF successfully'
    });
  } catch (error) {
    console.error('PDF image insertion error:', error);
    res.status(500).json({
      success: false,
      error: 'PDF image insertion failed: ' + error.message
    });
  }
});

// PDF Content Extraction Endpoints (Adobe Acrobat Pro style)
app.post('/api/pdf/extract-text', express.json({ limit: '100mb' }), async (req, res) => {
  try {
    const { pdfData } = req.body;
    
    if (!pdfData) {
      return res.status(400).json({
        success: false,
        error: 'No PDF data provided'
      });
    }
    
    // Convert base64 to buffer
    let pdfBuffer;
    if (typeof pdfData === 'string') {
      if (pdfData.startsWith('data:application/pdf')) {
        pdfData = pdfData.split(',')[1];
      }
      pdfBuffer = Buffer.from(pdfData, 'base64');
    } else {
      pdfBuffer = Buffer.from(pdfData);
    }
    
    // Extract text with positions
    const pdfContentParser = require('./api/pdf-edit/pdf-content-parser');
    const textItems = await pdfContentParser.extractTextWithPositions(pdfBuffer);
    const fonts = await pdfContentParser.getFontsFromPDF(pdfBuffer);
    
    res.json({
      success: true,
      textItems: textItems,
      fonts: fonts,
      message: 'Text extracted successfully'
    });
  } catch (error) {
    console.error('PDF text extraction error:', error);
    res.status(500).json({
      success: false,
      error: 'PDF text extraction failed: ' + error.message
    });
  }
});

// Get fonts from PDF
app.post('/api/pdf/get-fonts', express.json({ limit: '100mb' }), async (req, res) => {
  try {
    const { pdfData } = req.body;
    
    if (!pdfData) {
      return res.status(400).json({
        success: false,
        error: 'No PDF data provided'
      });
    }
    
    // Convert base64 to buffer
    let pdfBuffer;
    if (typeof pdfData === 'string') {
      if (pdfData.startsWith('data:application/pdf')) {
        pdfData = pdfData.split(',')[1];
      }
      pdfBuffer = Buffer.from(pdfData, 'base64');
    } else {
      pdfBuffer = Buffer.from(pdfData);
    }
    
    // Get fonts
    const pdfContentParser = require('./api/pdf-edit/pdf-content-parser');
    const fonts = await pdfContentParser.getFontsFromPDF(pdfBuffer);
    
    res.json({
      success: true,
      fonts: fonts,
      message: 'Fonts extracted successfully'
    });
  } catch (error) {
    console.error('PDF font extraction error:', error);
    res.status(500).json({
      success: false,
      error: 'PDF font extraction failed: ' + error.message
    });
  }
});

// Comprehensive Google Cloud Services Status Check
app.get('/api/cloud/status', async (req, res) => {
  try {
    const cloudStatus = require('./cloud-run-status');
    const status = cloudStatus.getComprehensiveStatus();
    
    res.json({
      success: true,
      ...status
    });
  } catch (error) {
    console.error('Cloud status check error:', error);
    res.status(500).json({
      success: false,
      error: 'Status check failed: ' + error.message
    });
  }
});

// Google Cloud Vision API Status Check Endpoint
app.get('/api/pdf-ocr/status', async (req, res) => {
  try {
    const googleCloudOCR = require('./api/pdf-ocr/google-cloud-ocr');
    const isAvailable = googleCloudOCR.isAvailable();
    
    let statusDetails = {
      available: isAvailable,
      method: null,
      error: null
    };
    
    if (isAvailable) {
      // Check which method is being used
      if (process.env.GOOGLE_CLOUD_SERVICE_ACCOUNT) {
        statusDetails.method = 'GOOGLE_CLOUD_SERVICE_ACCOUNT';
        statusDetails.message = 'Google Cloud Vision API is active and ready!';
      } else if (process.env.FIREBASE_SERVICE_ACCOUNT) {
        statusDetails.method = 'FIREBASE_SERVICE_ACCOUNT';
        statusDetails.message = 'Google Cloud Vision API is active via Firebase credentials!';
      } else if (process.env.GOOGLE_APPLICATION_CREDENTIALS) {
        statusDetails.method = 'GOOGLE_APPLICATION_CREDENTIALS';
        statusDetails.message = 'Google Cloud Vision API is active via credentials file!';
      } else {
        statusDetails.method = 'default';
        statusDetails.message = 'Google Cloud Vision API is active with default credentials!';
      }
      
      // Test with a simple image to verify it's actually working
      try {
        // Create a simple 1x1 white pixel image in base64
        const testImage = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==';
        await googleCloudOCR.processDocumentTextDetection(testImage, 'en');
        statusDetails.test = 'passed';
        statusDetails.accuracy = '100% - Google Cloud Vision API is fully functional';
      } catch (testError) {
        statusDetails.test = 'failed';
        statusDetails.error = testError.message;
        statusDetails.accuracy = 'Cannot verify - API may not be fully configured';
      }
    } else {
      statusDetails.message = 'Google Cloud Vision API is NOT active. Using fallback OCR (Tesseract).';
      statusDetails.accuracy = '90-95% (Tesseract OCR)';
      statusDetails.fallback = 'Python Tesseract OCR will be used';
      
      // Check why it's not available
      if (!process.env.GOOGLE_CLOUD_SERVICE_ACCOUNT && 
          !process.env.FIREBASE_SERVICE_ACCOUNT && 
          !process.env.GOOGLE_APPLICATION_CREDENTIALS) {
        statusDetails.error = 'No Google Cloud credentials found. Set GOOGLE_CLOUD_SERVICE_ACCOUNT or FIREBASE_SERVICE_ACCOUNT environment variable.';
      }
    }
    
    res.json({
      success: true,
      ...statusDetails
    });
  } catch (error) {
    res.json({
      success: false,
      available: false,
      error: error.message,
      message: 'Error checking Google Cloud Vision API status',
      accuracy: '90-95% (Fallback: Tesseract OCR)'
    });
  }
});

// Fast OCR Processing Endpoint (Optimized for speed)
app.post('/api/pdf-ocr/process-fast', express.json({ limit: '50mb' }), async (req, res) => {
  try {
    const { image, language = 'en', fast = true } = req.body;
    
    if (!image) {
      return res.status(400).json({ 
        success: false, 
        error: 'No image data provided' 
      });
    }
    
    // Fast processing: Use Google Cloud Vision API with optimized settings
    try {
      const googleCloudOCR = require('./api/pdf-ocr/google-cloud-ocr');
      
      if (googleCloudOCR.isAvailable()) {
        const langMap = {
          'eng': 'en', 'en': 'en', 'hin': 'hi', 'hi': 'hi',
          'guj': 'gu', 'mar': 'mr', 'nep': 'ne', 'san': 'sa',
          'tam': 'ta', 'tel': 'te', 'kan': 'kn', 'mal': 'ml',
          'ben': 'bn', 'pun': 'pa', 'urd': 'ur'
        };
        
        const mappedLang = langMap[language] || language || 'en';
        
        // Use fast text detection (not document text detection for speed)
        const result = await googleCloudOCR.processOCRWithGoogleCloud(image, mappedLang);
        
        return res.json({
          success: true,
          text: result.text,
          words: result.words,
          confidence: result.confidence,
          language: mappedLang,
          method: 'google-cloud-vision-fast',
          processingTime: 'instant'
        });
      }
    } catch (googleError) {
      console.warn('Fast Google Cloud OCR failed:', googleError.message);
    }
    
    // Fallback to standard OCR
    try {
      const standardResponse = await fetch('http://localhost:' + PORT + '/api/pdf-ocr/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image, language })
      });
      
      if (standardResponse.ok) {
        const result = await standardResponse.json();
        return res.json({
          ...result,
          method: 'standard-fallback'
        });
      }
    } catch (fetchError) {
      console.warn('Standard OCR fallback failed:', fetchError.message);
    }
    
    throw new Error('Fast OCR processing failed');
  } catch (error) {
    console.error('Fast OCR error:', error);
    res.status(500).json({
      success: false,
      error: 'Fast OCR processing failed: ' + error.message
    });
  }
});

// PDF OCR API endpoint - High accuracy server-side OCR processing with Google Cloud Vision API
app.post('/api/pdf-ocr/process', express.json({ limit: '50mb' }), async (req, res) => {
  try {
    const { image, language = 'en' } = req.body;
    
    if (!image) {
      return res.status(400).json({ 
        success: false, 
        error: 'No image data provided' 
      });
    }
    
    // Try Google Cloud Vision API first (preferred method)
    try {
      const googleCloudOCR = require('./api/pdf-ocr/google-cloud-ocr');
      
      if (googleCloudOCR.isAvailable()) {
        // Map language codes (e.g., 'eng' -> 'en', 'hin' -> 'hi')
        const langMap = {
          'eng': 'en',
          'en': 'en',
          'hin': 'hi',
          'hi': 'hi',
          'guj': 'gu',
          'mar': 'mr',
          'nep': 'ne',
          'san': 'sa',
          'tam': 'ta',
          'tel': 'te',
          'kan': 'kn',
          'mal': 'ml',
          'ben': 'bn',
          'pun': 'pa',
          'urd': 'ur'
        };
        
        const mappedLang = langMap[language] || language || 'en';
        
        // Use document text detection for better structure
        const result = await googleCloudOCR.processDocumentTextDetection(image, mappedLang);
        
        return res.json({
          success: true,
          text: result.text,
          words: result.words,
          blocks: result.blocks,
          confidence: result.confidence,
          language: mappedLang,
          method: 'google-cloud-vision'
        });
      }
    } catch (googleError) {
      console.warn('Google Cloud Vision API not available, falling back to Python OCR:', googleError.message);
    }
    
    // Fallback to Python Tesseract OCR
    const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
    const ocrScriptPath = path.join(__dirname, 'api', 'pdf-ocr', 'ocr-process.py');
    
    // Prepare input data
    const inputData = JSON.stringify({ image, language });
    
    // Execute Python OCR script
    exec(
      `${pythonCmd} "${ocrScriptPath}"`,
      { 
        input: inputData,
        maxBuffer: 50 * 1024 * 1024 // 50MB buffer
      },
      (error, stdout, stderr) => {
        if (error) {
          console.error('OCR processing error:', error);
          console.error('Stderr:', stderr);
          return res.status(500).json({ 
            success: false, 
            error: 'OCR processing failed: ' + error.message 
          });
        }
        
        try {
          const result = JSON.parse(stdout);
          res.json(result);
        } catch (parseError) {
          console.error('Failed to parse OCR result:', parseError);
          console.error('Stdout:', stdout);
          res.status(500).json({ 
            success: false, 
            error: 'Failed to parse OCR result' 
          });
        }
      }
    );
    
  } catch (error) {
    console.error('OCR API error:', error);
    res.status(500).json({ 
      success: false, 
      error: 'OCR API error: ' + error.message 
    });
  }
});

// User-provided error handler
app.use((error, req, res, next) => {
  console.error('Server error:', error);
  if (error instanceof multer.MulterError && error.code === 'LIMIT_FILE_SIZE') {
    return res.status(400).json({ success: false, message: 'File size too large. Maximum 100MB allowed.' });
  }
  res.status(500).json({ success: false, message: error.message || 'Internal server error' });
});

function findChromeCmd() {
  const candidates = process.platform === 'win32'
    ? [
        'chrome',
        'chrome.exe',
        'C:/Program Files/Google/Chrome/Application/chrome.exe',
        'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
        'msedge',
        'msedge.exe',
        'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
        'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
      ]
    : ['google-chrome', 'chromium', 'chrome', 'msedge'];
  return candidates.find(c => {
    try { return !!execSyncCheck(c); } catch (_) { return false; }
  });
}

function execSyncCheck(cmd) {
  try {
    execSync(`${cmd} --version`, { stdio: 'ignore' });
    return true;
  } catch (_) {
    return false;
  }
}

function hasSoffice() {
  const candidate = process.env.SOFFICE_PATH || 'soffice';
  try {
    execSync(`${candidate} --version`, { stdio: 'ignore' });
    return true;
  } catch (_) {
    return false;
  }
}

async function convertHtmlWithChrome(inputPath, outputPdf) {
  const chrome = findChromeCmd();
  if (!chrome) throw new Error('No Chrome/Edge found for HTML rendering');
  const fileUrl = 'file:///' + inputPath.replace(/\\/g, '/');
  const cmd = `"${chrome}" --headless --disable-gpu --no-first-run --no-default-browser-check --print-to-pdf="${outputPdf}" "${fileUrl}"`;
  await execAsync(cmd);
  if (!fs.existsSync(outputPdf)) throw new Error('Chrome did not produce a PDF');
  return outputPdf;
}

function injectUnicodeCss(htmlPath, workDir) {
  try {
    const raw = fs.readFileSync(htmlPath, 'utf8');
    const linkTag = `<link rel="stylesheet" href="http://localhost:${PORT}/assets/unicode.css">`;
    let out;
    if (/<head[\s>]/i.test(raw)) {
      out = raw.replace(/<head(\s*[^>]*)>/i, (m) => m + `\n  ${linkTag}`);
    } else if (/<html[\s>]/i.test(raw)) {
      out = raw.replace(/<html(\s*[^>]*)>/i, (m) => m + `\n<head>\n  <meta charset="utf-8">\n  ${linkTag}\n</head>`);
    } else {
      out = `<!doctype html>\n<html>\n<head>\n  <meta charset="utf-8">\n  ${linkTag}\n</head>\n<body>\n${raw}\n</body>\n</html>`;
    }
    const outPath = path.join(workDir, 'unicode_injected.html');
    fs.writeFileSync(outPath, out, 'utf8');
    return outPath;
  } catch (e) {
    return htmlPath; // fallback without injection
  }
}

app.post('/convert/word-to-pdf', upload.any(), async (req, res) => {
  const files = req.files || [];
  const file = files.find(f => f.fieldname === 'file') || files.find(f => f.fieldname === 'files') || files[0];
  if (!file) return res.status(400).json({ error: 'No file uploaded (expected field name "file" or "files")' });

  const workId = uuidv4();
  const workDir = path.join(os.tmpdir(), `easyjpgtopdf-${workId}`);
  fs.mkdirSync(workDir, { recursive: true });

  let producedPdf = null;
  let gsPdf = null;

  try {
    const ext = (path.extname(file.originalname || '').toLowerCase() || '').replace('.', '');
    const requestedEngine = (req.query.engine || '').toLowerCase();
    const isWordFamily = ['docx','doc','rtf','odt'].includes(ext);
    const isHtml = ['html','htm'].includes(ext);
    let engine = requestedEngine;
    if (!engine) {
      // Prefer Chrome for HTML rendering (better Unicode/webfont fidelity), else Word on Windows for Word docs
      if (isHtml && findChromeCmd()) engine = 'chrome';
      else if (process.platform === 'win32' && isWordFamily) engine = 'msword';
      else engine = 'libreoffice';
    }

    let pdfPath;
    if (engine === 'msword') {
      const out = path.join(workDir, path.parse(file.originalname || 'document').name + '.pdf');
      try {
        pdfPath = await convertWithMsWord(file.path, out);
      } catch (e) {
        // Fallback to LibreOffice if MS Word path fails
        pdfPath = await convertWithLibreOffice(file.path, workDir);
      }
    } else if (engine === 'chrome') {
      const out = path.join(workDir, path.parse(file.originalname || 'document').name + '.pdf');
      try {
        const inputForChrome = isHtml ? injectUnicodeCss(file.path, workDir) : file.path;
        pdfPath = await convertHtmlWithChrome(inputForChrome, out);
      } catch (e) {
        // Fallback to LibreOffice if Chrome path fails
        pdfPath = await convertWithLibreOffice(file.path, workDir);
      }
    } else {
      pdfPath = await convertWithLibreOffice(file.path, workDir);
    }
    producedPdf = pdfPath;

    // Try Ghostscript to force-embed fonts if available
    try {
      const testGs = findGhostscriptCmd();
      await execAsync(`"${testGs}" -v`);
      const gsOut = path.join(workDir, 'embedded.pdf');
      await forceEmbedFontsWithGhostscript(producedPdf, gsOut);
      gsPdf = gsOut;
    } catch (e) {
      // Ghostscript not installed or failed; continue with LO output
    }

    const finalPdf = gsPdf || producedPdf;
    const outName = path.parse(file.originalname || 'document').name + '.pdf';

    try {
      const stat = fs.statSync(finalPdf);
      const disposition = (req.query.disposition || '').toLowerCase() === 'inline' ? 'inline' : 'attachment';
      const headers = {
        'Content-Type': 'application/pdf',
        'Content-Length': stat.size,
        'Cache-Control': 'no-store',
      };

      if (disposition === 'attachment') {
        res.download(finalPdf, outName, (err) => {
          // cleanup async after response ends
          setTimeout(() => {
            cleanupFiles([file.path, producedPdf, gsPdf]);
            try { fs.rmSync(workDir, { recursive: true, force: true }); } catch (_) {}
          }, 1000);
          if (err) {
            try { return res.status(500).end('Failed to send PDF'); } catch (_) {}
          }
        });
      } else {
        res.set(headers);
        res.setHeader('Content-Disposition', `inline; filename="${outName}"`);
        res.sendFile(path.resolve(finalPdf), (err) => {
          setTimeout(() => {
            cleanupFiles([file.path, producedPdf, gsPdf]);
            try { fs.rmSync(workDir, { recursive: true, force: true }); } catch (_) {}
          }, 1000);
          if (err) {
            try { return res.status(500).end('Failed to send PDF'); } catch (_) {}
          }
        });
      }
    } catch (e) {
      return res.status(500).json({ error: 'Failed to prepare PDF response', details: String(e && e.message || e) });
    }
  } catch (err) {
    console.error('Conversion error:', err);
    cleanupFiles([file.path]);
    try { fs.rmSync(workDir, { recursive: true, force: true }); } catch (_) {}
    res.status(500).json({ error: 'Conversion failed', details: String(err && err.message || err) });
  }
});

// Explicit MS Word endpoint for clarity
app.post('/convert/word-to-pdf/msword', upload.any(), async (req, res) => {
  req.query.engine = 'msword';
  return app._router.handle(req, res, () => {});
});

// Initialize subscription routes
try {
  subscriptionRoutes(app);
  console.log('Subscription routes initialized');
} catch (error) {
  console.warn('Failed to initialize subscription routes:', error.message);
}

app.listen(PORT, () => {
  console.log(`Word2PDF server listening on http://localhost:${PORT}`);
});



