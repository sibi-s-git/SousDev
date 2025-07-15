const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  selectFolder: () => ipcRenderer.invoke('select-folder'),
  loadEnvVars: () => ipcRenderer.invoke('load-env-vars'),
  saveEnvVars: (variables) => ipcRenderer.invoke('save-env-vars', variables),
  ensureContextFolder: () => ipcRenderer.invoke('ensure-context-folder'),
  vectorizeProject: (projectPath, contentPath, openaiApiKey) => ipcRenderer.invoke('vectorize-project', projectPath, contentPath, openaiApiKey),
  
  // Add more API methods here as needed
  platform: process.platform,
  versions: process.versions
}); 