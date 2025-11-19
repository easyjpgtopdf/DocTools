// Returns a safe subset of public environment variables
module.exports = async (req, res) => {
  try {
    const publicEnv = {
      RAZORPAY_KEY: process.env.RAZORPAY_KEY || null
    };
    res.setHeader('Content-Type', 'application/json');
    res.status(200).send(JSON.stringify({ success: true, env: publicEnv }));
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
};
