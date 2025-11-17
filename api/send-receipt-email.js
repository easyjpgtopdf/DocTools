// Send payment receipt email using Resend
const RESEND_API_KEY = process.env.RESEND_API_KEY;

module.exports = async function handler(req, res) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Content-Type', 'application/json');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ 
      success: false,
      error: 'Method not allowed'
    });
  }

  try {
    // Check if Resend is configured
    if (!RESEND_API_KEY) {
      console.error('Resend API key not configured');
      return res.status(503).json({ 
        success: false,
        error: 'Email service not configured'
      });
    }

    const { email, name, amount, currency, transactionId, orderId, paymentMethod, date } = req.body;

    // Validate required fields
    if (!email || !amount || !transactionId) {
      return res.status(400).json({
        success: false,
        error: 'Missing required fields',
        required: ['email', 'amount', 'transactionId']
      });
    }

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid email address'
      });
    }

    // Create email HTML content
    const emailHTML = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Payment Receipt - easyjpgtopdf</title>
  <style>
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      line-height: 1.6;
      color: #333;
      background-color: #f5f7ff;
      margin: 0;
      padding: 0;
    }
    .container {
      max-width: 600px;
      margin: 20px auto;
      background: white;
      border-radius: 10px;
      overflow: hidden;
      box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 30px;
      text-align: center;
    }
    .header h1 {
      margin: 0;
      font-size: 28px;
    }
    .success-icon {
      font-size: 60px;
      margin-bottom: 10px;
    }
    .content {
      padding: 40px 30px;
    }
    .receipt-details {
      background: #f8f9fa;
      border-radius: 8px;
      padding: 20px;
      margin: 20px 0;
    }
    .receipt-row {
      display: flex;
      justify-content: space-between;
      padding: 12px 0;
      border-bottom: 1px solid #e0e0e0;
    }
    .receipt-row:last-child {
      border-bottom: none;
      font-weight: bold;
      font-size: 18px;
      color: #4361ee;
      margin-top: 10px;
      padding-top: 15px;
      border-top: 2px solid #4361ee;
    }
    .label {
      color: #666;
      font-weight: 500;
    }
    .value {
      color: #333;
      font-weight: 600;
      text-align: right;
    }
    .footer {
      background: #f8f9fa;
      padding: 20px 30px;
      text-align: center;
      color: #666;
      font-size: 14px;
    }
    .button {
      display: inline-block;
      padding: 12px 30px;
      background: #4361ee;
      color: white;
      text-decoration: none;
      border-radius: 5px;
      margin: 20px 0;
      font-weight: 600;
    }
    .note {
      background: #fff3cd;
      border-left: 4px solid #ffc107;
      padding: 15px;
      margin: 20px 0;
      border-radius: 4px;
      font-size: 14px;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="success-icon">✓</div>
      <h1>Payment Successful!</h1>
      <p style="margin: 10px 0 0 0; opacity: 0.9;">Thank you for your donation</p>
    </div>
    
    <div class="content">
      <p>Dear ${name || 'Valued Customer'},</p>
      <p>Thank you for your generous donation to <strong>easyjpgtopdf</strong>. Your payment has been processed successfully.</p>
      
      <div class="receipt-details">
        <h3 style="margin-top: 0; color: #4361ee;">Payment Receipt</h3>
        
        <div class="receipt-row">
          <span class="label">Transaction ID:</span>
          <span class="value">${transactionId}</span>
        </div>
        
        ${orderId ? `
        <div class="receipt-row">
          <span class="label">Order ID:</span>
          <span class="value">${orderId}</span>
        </div>
        ` : ''}
        
        <div class="receipt-row">
          <span class="label">Date & Time:</span>
          <span class="value">${date || new Date().toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })}</span>
        </div>
        
        <div class="receipt-row">
          <span class="label">Payment Method:</span>
          <span class="value">${paymentMethod || 'Razorpay'}</span>
        </div>
        
        <div class="receipt-row">
          <span class="label">Amount Paid:</span>
          <span class="value">${currency || 'INR'} ${parseFloat(amount).toFixed(2)}</span>
        </div>
      </div>
      
      <div class="note">
        <strong>📌 Important:</strong> Please save this email for your records. You can also view and print your receipt anytime from your account dashboard.
      </div>
      
      <div style="text-align: center;">
        <a href="https://easyjpgtopdf.com/payment-receipt.html?txn_id=${transactionId}&order_id=${orderId || ''}&amount=${amount}&currency=${currency || 'INR'}&method=${paymentMethod || 'razorpay'}" class="button">
          View Full Receipt
        </a>
      </div>
      
      <p style="margin-top: 30px;">Your contribution helps us keep easyjpgtopdf free and accessible to everyone. We truly appreciate your support!</p>
      
      <p style="margin-top: 20px;">
        Best regards,<br>
        <strong>Team easyjpgtopdf</strong>
      </p>
    </div>
    
    <div class="footer">
      <p style="margin: 0 0 10px 0;">© ${new Date().getFullYear()} easyjpgtopdf. All rights reserved.</p>
      <p style="margin: 0;">
        <a href="https://easyjpgtopdf.com" style="color: #4361ee; text-decoration: none;">Visit Website</a> | 
        <a href="https://easyjpgtopdf.com/privacy-policy.html" style="color: #4361ee; text-decoration: none;">Privacy Policy</a> | 
        <a href="https://easyjpgtopdf.com/terms-of-service.html" style="color: #4361ee; text-decoration: none;">Terms of Service</a>
      </p>
      <p style="margin: 10px 0 0 0; font-size: 12px; color: #999;">
        This is an automated email. Please do not reply to this message.
      </p>
    </div>
  </div>
</body>
</html>
`;

    // Send email using Resend API
    const response = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${RESEND_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        from: 'easyjpgtopdf <noreply@easyjpgtopdf.com>',
        to: [email],
        subject: `Payment Receipt - Transaction ${transactionId.substring(0, 12)}...`,
        html: emailHTML
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      console.error('Resend API error:', errorData);
      throw new Error(`Resend API error: ${response.status}`);
    }

    const result = await response.json();
    console.log('Email sent successfully:', result.id);

    return res.status(200).json({
      success: true,
      message: 'Receipt email sent successfully',
      emailId: result.id
    });

  } catch (error) {
    console.error('Error sending receipt email:', error);
    return res.status(500).json({
      success: false,
      error: 'Failed to send email',
      message: process.env.NODE_ENV === 'development' ? error.message : 'Please try again later'
    });
  }
};
