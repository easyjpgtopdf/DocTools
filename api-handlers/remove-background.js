// Free background removal using @imgly/background-removal
// Smart size-based processing for optimal speed and quality
// No paid API required - 100% free solution

module.exports = async function handler(req, res) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { fileSize } = req.body;
    
    // Smart model selection based on file size for optimal performance
    let modelConfig;
    if (fileSize < 20 * 1024 * 1024) {
      // 0-20 MB: Fast processing with small model
      modelConfig = {
        model: 'small',
        description: 'Fast Processing',
        quality: 0.8
      };
    } else if (fileSize < 50 * 1024 * 1024) {
      // 20-50 MB: Balanced quality with medium model
      modelConfig = {
        model: 'medium',
        description: 'Balanced Quality',
        quality: 0.9
      };
    } else {
      // 50+ MB: Best quality but slower
      modelConfig = {
        model: 'medium',
        description: 'Best Quality',
        quality: 1.0
      };
    }
    
    // Return configuration for client-side processing
    // Client will use @imgly/background-removal with these settings
    res.status(200).json({
      success: true,
      useClientSide: true,
      config: modelConfig,
      message: `Using ${modelConfig.description} mode for optimal results`
    });

  } catch (error) {
    console.error('Config error:', error);
    res.status(200).json({ 
      success: true,
      useClientSide: true,
      config: {
        model: 'medium',
        description: 'Standard Quality',
        quality: 0.9
      }
    });
  }
};
