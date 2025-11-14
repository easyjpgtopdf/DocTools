# Image Repair Backend

## Features
- 🎨 100+ AI-powered image tools
- 🖼️ Background removal (rembg)
- 👤 Face enhancement
- 🎭 Avatar creation
- 🌈 Advanced filters & effects
- 📤 Multiple export formats (JPG, PNG, WEBP)

## API Endpoints

### Health Check
```
GET /test
```

### Upload Image
```
POST /upload
Form-data: file (image)
```

### Process Image
```
POST /process
JSON: {
  "filename": "image.jpg",
  "tool": "auto-fix",
  "params": {}
}
```

### Remove Background
```
POST /remove-background
JSON: {
  "filename": "image.jpg"
}
```

### Face Enhancement
```
POST /face-enhance
JSON: {
  "filename": "image.jpg",
  "type": "smooth" | "sharpen"
}
```

### Download
```
GET /download/<filename>?format=png|jpg|jpeg|webp
```

## Local Development
```bash
pip install -r requirements.txt
python app.py
```

## Deploy to Render
1. Push to GitHub
2. Connect repository to Render
3. Deploy as Web Service
4. Set root directory: `image-repair-backend`
