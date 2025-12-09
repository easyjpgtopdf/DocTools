const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
    openPdfFile: () => ipcRenderer.invoke('open-pdf-file'),
    savePdfFile: (pdfBytes) => ipcRenderer.invoke('save-pdf-file', pdfBytes),
    apiCall: (options) => ipcRenderer.invoke('api-call', options),
    checkCredits: (userId) => ipcRenderer.invoke('check-credits', userId)
});

