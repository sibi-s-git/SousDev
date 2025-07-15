const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  selectFolder: () => ipcRenderer.invoke('select-folder'),
  loadEnvVars: () => ipcRenderer.invoke('load-env-vars'),
  saveEnvVars: (variables) => ipcRenderer.invoke('save-env-vars', variables),
  ensureContextFolder: () => ipcRenderer.invoke('ensure-context-folder'),
  checkProjectIntelligence: (contentPath) => ipcRenderer.invoke('check-project-intelligence', contentPath),
  analyzeProject: (projectPath, contentPath, anthropicApiKey) => ipcRenderer.invoke('analyze-project', projectPath, contentPath, anthropicApiKey),
  vectorizeProject: (projectPath, contentPath, openaiApiKey) => ipcRenderer.invoke('vectorize-project', projectPath, contentPath, openaiApiKey),
  reloadProject: (projectPath, contentPath, openaiApiKey, anthropicApiKey) => ipcRenderer.invoke('reload-project', projectPath, contentPath, openaiApiKey, anthropicApiKey),
  intelligentChat: (userMessage, images, projectPath, contentPath, anthropicApiKey) => ipcRenderer.invoke('intelligent-chat', userMessage, images, projectPath, contentPath, anthropicApiKey),
  
  // Add more API methods here as needed
  platform: process.platform,
  versions: process.versions
}); 