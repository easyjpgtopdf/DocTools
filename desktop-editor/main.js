const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const axios = require('axios');

// Backend API URL (same Cloud Run service)
const API_BASE_URL = process.env.API_BASE_URL || 'https://pdf-editor-service-564572183797.us-central1.run.app';

let mainWindow;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        icon: path.join(__dirname, 'assets', 'icon.png')
    });

    // Load the React app (will be built later)
    // For now, load a simple HTML page
    mainWindow.loadFile('index.html');

    // Open DevTools in development
    if (process.env.NODE_ENV === 'development') {
        mainWindow.webContents.openDevTools();
    }
}

app.whenReady().then(() => {
    createWindow();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

// IPC handlers for backend communication
ipcMain.handle('open-pdf-file', async () => {
    const result = await dialog.showOpenDialog(mainWindow, {
        properties: ['openFile'],
        filters: [
            { name: 'PDF Files', extensions: ['pdf'] }
        ]
    });

    if (!result.canceled && result.filePaths.length > 0) {
        return result.filePaths[0];
    }
    return null;
});

ipcMain.handle('save-pdf-file', async (event, pdfBytes) => {
    const result = await dialog.showSaveDialog(mainWindow, {
        filters: [
            { name: 'PDF Files', extensions: ['pdf'] }
        ],
        defaultPath: 'edited-document.pdf'
    });

    if (!result.canceled && result.filePath) {
        const fs = require('fs');
        fs.writeFileSync(result.filePath, Buffer.from(pdfBytes));
        return result.filePath;
    }
    return null;
});

// Backend API calls (reuse existing Cloud Run service)
ipcMain.handle('api-call', async (event, { endpoint, method = 'GET', data = null }) => {
    try {
        const response = await axios({
            method,
            url: `${API_BASE_URL}${endpoint}`,
            data,
            headers: {
                'Content-Type': 'application/json'
            }
        });
        return { success: true, data: response.data };
    } catch (error) {
        console.error('API call error:', error);
        return { success: false, error: error.message };
    }
});

// User credits check
ipcMain.handle('check-credits', async (event, userId) => {
    try {
        const response = await axios.get(`${API_BASE_URL}/user/credits`, {
            params: { user_id: userId }
        });
        return { success: true, credits: response.data.credits || 0 };
    } catch (error) {
        return { success: false, error: error.message };
    }
});

