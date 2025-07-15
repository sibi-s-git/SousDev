const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const isDev = process.env.ELECTRON_IS_DEV === 'true';

let mainWindow;

// Environment variables file path
const envFilePath = path.join(__dirname, '..', '.env');
const contentFolderPath = path.join(__dirname, '..', 'content');

// Load environment variables from .env file
function loadEnvVariables() {
  try {
    if (fs.existsSync(envFilePath)) {
      const envContent = fs.readFileSync(envFilePath, 'utf8');
      const envVars = {};
      envContent.split('\n').forEach(line => {
        const [key, value] = line.split('=');
        if (key && value !== undefined) {
          envVars[key.trim()] = value.trim();
        }
      });
      return envVars;
    }
  } catch (error) {
    console.error('Error loading environment variables:', error);
  }
  return {};
}

// Save environment variables to .env file
function saveEnvVariables(variables) {
  try {
    const envContent = Object.entries(variables)
      .map(([key, value]) => `${key}=${value}`)
      .join('\n');
    fs.writeFileSync(envFilePath, envContent, 'utf8');
    return true;
  } catch (error) {
    console.error('Error saving environment variables:', error);
    return false;
  }
}

// Create context folder for project
function ensureProjectContextFolder() {
  try {
    const envVars = loadEnvVariables();
    const projectFolder = envVars.PROJECT_FOLDER;
    
    if (!projectFolder) {
      console.log('No project folder set in environment variables');
      return null;
    }
    
    // Extract just the folder name from the full path
    const folderName = path.basename(projectFolder);
    const contextFolderPath = path.join(contentFolderPath, folderName);
    
    // Ensure content directory exists
    if (!fs.existsSync(contentFolderPath)) {
      fs.mkdirSync(contentFolderPath, { recursive: true });
      console.log('Created content directory');
    }
    
    // Check if project context folder exists, create if not
    if (!fs.existsSync(contextFolderPath)) {
      fs.mkdirSync(contextFolderPath, { recursive: true });
      console.log(`Created context folder for project: ${folderName}`);
    } else {
      console.log(`Context folder already exists for project: ${folderName}`);
    }
    
    return contextFolderPath;
  } catch (error) {
    console.error('Error ensuring project context folder:', error);
    return null;
  }
}

function createWindow() {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    icon: path.join(__dirname, 'assets', 'icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    titleBarStyle: 'default',
    show: false,
    backgroundColor: '#000000'
  });

  // Load the app
  if (isDev) {
    mainWindow.loadURL('http://localhost:3000');
    // mainWindow.webContents.openDevTools(); // Uncomment to enable dev tools
  } else {
    mainWindow.loadFile(path.join(__dirname, '../build/index.html'));
  }

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    
    // Ensure project context folder exists on startup
    ensureProjectContextFolder();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// Handle folder selection
ipcMain.handle('select-folder', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory']
  });
  return result.filePaths[0];
});

// Handle environment variables loading
ipcMain.handle('load-env-vars', async () => {
  return loadEnvVariables();
});

// Handle environment variables saving
ipcMain.handle('save-env-vars', async (event, variables) => {
  const success = saveEnvVariables(variables);
  if (success) {
    // Ensure context folder is created/updated after saving env vars
    ensureProjectContextFolder();
  }
  return success;
});

// Handle creating context folder manually
ipcMain.handle('ensure-context-folder', async () => {
  return ensureProjectContextFolder();
});

// Set app icon for dock/taskbar
if (process.platform !== 'darwin') {
  // For Windows and Linux, set the icon
  app.setAppUserModelId('com.sousdev.app');
}

// Handle app lifecycle
app.whenReady().then(() => {
  // Set the dock icon on macOS
  if (process.platform === 'darwin') {
    app.dock.setIcon(path.join(__dirname, 'assets', 'icon.png'));
  }
  createWindow();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
}); 