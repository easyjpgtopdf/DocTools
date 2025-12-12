# Background Workspace Backup - 2025-12-12

This backup contains all files related to the Background Workspace and Background Removal functionality.

## Contents

### Frontend Files
- `server/public/background-workspace.html` - Main workspace page for editing transparent images
- `server/public/background-remover.html` - Initial upload page for background removal

### Backend API Files
- `api/tools/bg-remove-free.js` - Free preview background removal handler (512px)
- `api/tools/bg-remove-premium.js` - Premium HD background removal handler (2000-4000px)

### Server Routes
- `server-server-background-routes.js` - Background removal proxy endpoints from server.js
  - `/api/background-remove` - Legacy endpoint
  - `/api/background-remove/health` - Health check
  - `/api/background-remove-birefnet` - BiRefNet proxy endpoint (POST)
  - `/api/background-remove-birefnet/health` - BiRefNet health check
  - `/api/background-remove-birefnet/usage` - Usage statistics (stub)

### Vercel Configuration
- `vercel-routes.json` - Vercel routing configuration for background removal pages

### Backend Service
- `bg-removal-backend/` - Complete BiRefNet GPU backend service
  - Python Flask application
  - BiRefNet model integration
  - Cloud Run deployment configuration

## API Endpoints

### Frontend → Backend Flow
1. User uploads image on `background-remover.html`
2. Image is sent to workspace: `background-workspace.html`
3. Processing request → `/api/background-remove-birefnet`
4. Proxy forwards to Cloud Run: `https://bg-removal-birefnet-564572183797.us-central1.run.app`
5. Response returned with processed image

### Cloud Run Service
- **URL**: `https://bg-removal-birefnet-564572183797.us-central1.run.app`
- **Free Preview**: `/api/free-preview-bg` (512px)
- **Premium HD**: `/api/premium-bg` (2000-4000px)
- **Health Check**: `/health`

## Configuration

### Environment Variables
- `CLOUDRUN_API_URL_BG_REMOVAL` - BiRefNet Cloud Run service URL
- Default: `https://bg-removal-birefnet-564572183797.us-central1.run.app`

### Technology Stack
- **Frontend**: HTML, JavaScript (ES6 modules), CSS
- **Backend**: Node.js (Express), Python (Flask)
- **AI Model**: BiRefNet (GPU-accelerated)
- **Deployment**: Google Cloud Run (backend), Vercel (frontend)

## Restoration Instructions

1. Copy frontend files to `server/public/`
2. Copy API files to `api/tools/`
3. Merge server routes into `server/server.js`
4. Add routes to `vercel.json`
5. Restore `bg-removal-backend/` folder if needed

## Backup Date
**2025-12-12**

This backup represents the complete, working state of the background removal feature with:
- ✅ BiRefNet GPU backend integration
- ✅ Free preview (512px) functionality
- ✅ Premium HD (2000-4000px) functionality
- ✅ Image preview fix in workspace
- ✅ All API endpoints synced
- ✅ PyTorch backend removed

