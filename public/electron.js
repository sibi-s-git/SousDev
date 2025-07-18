const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
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

// Check if project intelligence exists
ipcMain.handle('check-project-intelligence', async (event, contentPath) => {
  try {
    const resolvedContentPath = path.resolve(__dirname, '..', contentPath);
    const intelligencePath = path.join(resolvedContentPath, 'project_intelligence');
    const embeddingsPath = path.join(resolvedContentPath, 'embeddings');
    
    const intelligenceExists = fs.existsSync(intelligencePath) && 
                              fs.existsSync(path.join(intelligencePath, 'full_analysis.json'));
    const embeddingsExist = fs.existsSync(embeddingsPath) && 
                           fs.existsSync(path.join(embeddingsPath, 'embeddings.index'));
    
    return {
      intelligence_exists: intelligenceExists,
      embeddings_exist: embeddingsExist
    };
  } catch (error) {
    console.error('Error checking project intelligence:', error);
    return {
      intelligence_exists: false,
      embeddings_exist: false
    };
  }
});

// Handle project analysis (always runs)
ipcMain.handle('analyze-project', async (event, projectPath, contentPath, anthropicApiKey) => {
  return new Promise((resolve, reject) => {
    console.log('Starting project analysis...');
    console.log('Project path:', projectPath);
    console.log('Content path:', contentPath);
    
    // Resolve content path relative to app directory
    const resolvedContentPath = path.resolve(__dirname, '..', contentPath);
    console.log('Resolved content path:', resolvedContentPath);
    
    // Path to the Python analysis script
    const scriptPath = path.join(__dirname, '..', 'src', 'vectorization', 'project_analyzer.py');
    
    // Spawn Python process for analysis
    const pythonProcess = spawn('python3', [
      scriptPath,
      projectPath,
      resolvedContentPath,
      anthropicApiKey
    ], {
      cwd: path.join(__dirname, '..')
    });
    
    let stdout = '';
    let stderr = '';
    
    pythonProcess.stdout.on('data', (data) => {
      stdout += data.toString();
      console.log('Analysis stdout:', data.toString());
    });
    
    pythonProcess.stderr.on('data', (data) => {
      stderr += data.toString();
      console.error('Analysis stderr:', data.toString());
    });
    
    pythonProcess.on('close', (code) => {
      if (code === 0) {
        console.log('Project analysis completed successfully');
        resolve({ success: true, output: stdout });
      } else {
        console.error('Project analysis failed with code:', code);
        console.error('Error output:', stderr);
        reject(new Error(`Analysis failed: ${stderr}`));
      }
    });
    
    pythonProcess.on('error', (error) => {
      console.error('Failed to start analysis process:', error);
      reject(error);
    });
  });
});

// Handle project vectorization (conditionally runs on Get Started)
ipcMain.handle('vectorize-project', async (event, projectPath, contentPath, openaiApiKey) => {
  return new Promise((resolve, reject) => {
    console.log('Starting project vectorization...');
    console.log('Project path:', projectPath);
    console.log('Content path:', contentPath);
    
    // Resolve content path relative to app directory
    const resolvedContentPath = path.resolve(__dirname, '..', contentPath);
    console.log('Resolved content path:', resolvedContentPath);
    
    // Path to the Python script
    const scriptPath = path.join(__dirname, '..', 'src', 'vectorization', 'project_vectorizer.py');
    
    // Spawn Python process
    const pythonProcess = spawn('python3', [
      scriptPath,
      projectPath,
      resolvedContentPath,
      openaiApiKey
    ], {
      cwd: path.join(__dirname, '..')
    });
    
    let stdout = '';
    let stderr = '';
    
    pythonProcess.stdout.on('data', (data) => {
      stdout += data.toString();
      console.log('Python stdout:', data.toString());
    });
    
    pythonProcess.stderr.on('data', (data) => {
      stderr += data.toString();
      console.log('Python stderr:', data.toString());
    });
    
    pythonProcess.on('close', (code) => {
      console.log('Python process exited with code:', code);
      
      if (code === 0) {
        try {
          const result = JSON.parse(stdout);
          resolve(result);
        } catch (e) {
          reject(new Error('Failed to parse Python output: ' + e.message));
        }
      } else {
        reject(new Error(`Vectorization failed with code ${code}: ${stderr}`));
      }
    });
    
    pythonProcess.on('error', (error) => {
      console.error('Failed to start Python process:', error);
      reject(new Error('Failed to start vectorization process: ' + error.message));
    });
  });
});

// Handle full reload (analysis + vectorization)
ipcMain.handle('reload-project', async (event, projectPath, contentPath, openaiApiKey, anthropicApiKey) => {
  try {
    console.log('Starting full project reload...');
    
    // Step 1: Run project analysis
    const analysisResult = await new Promise((resolve, reject) => {
      const resolvedContentPath = path.resolve(__dirname, '..', contentPath);
      const scriptPath = path.join(__dirname, '..', 'src', 'vectorization', 'project_analyzer.py');
      
      const analysisProcess = spawn('python3', [
        scriptPath,
        projectPath,
        resolvedContentPath,
        anthropicApiKey
      ], {
        cwd: path.join(__dirname, '..')
      });
      
      let stdout = '';
      let stderr = '';
      
      analysisProcess.stdout.on('data', (data) => {
        stdout += data.toString();
        console.log('Analysis stdout:', data.toString());
      });
      
      analysisProcess.stderr.on('data', (data) => {
        stderr += data.toString();
        console.error('Analysis stderr:', data.toString());
      });
      
      analysisProcess.on('close', (code) => {
        if (code === 0) {
          resolve({ success: true, output: stdout });
        } else {
          reject(new Error(`Analysis failed: ${stderr}`));
        }
      });
      
      analysisProcess.on('error', (error) => {
        reject(error);
      });
    });
    
    // Step 2: Run vectorization
    const vectorizationResult = await new Promise((resolve, reject) => {
      const resolvedContentPath = path.resolve(__dirname, '..', contentPath);
      const scriptPath = path.join(__dirname, '..', 'src', 'vectorization', 'project_vectorizer.py');
      
      const vectorProcess = spawn('python3', [
        scriptPath,
        projectPath,
        resolvedContentPath,
        openaiApiKey
      ], {
        cwd: path.join(__dirname, '..')
      });
      
      let stdout = '';
      let stderr = '';
      
      vectorProcess.stdout.on('data', (data) => {
        stdout += data.toString();
        console.log('Vectorization stdout:', data.toString());
      });
      
      vectorProcess.stderr.on('data', (data) => {
        stderr += data.toString();
        console.error('Vectorization stderr:', data.toString());
      });
      
      vectorProcess.on('close', (code) => {
        if (code === 0) {
          try {
            const result = JSON.parse(stdout);
            resolve(result);
          } catch (e) {
            reject(new Error('Failed to parse vectorization output: ' + e.message));
          }
        } else {
          reject(new Error(`Vectorization failed: ${stderr}`));
        }
      });
      
      vectorProcess.on('error', (error) => {
        reject(error);
      });
    });
    
    console.log('Full project reload completed successfully');
    return { 
      success: true, 
      analysis: analysisResult, 
      vectorization: vectorizationResult 
    };
    
  } catch (error) {
    console.error('Project reload failed:', error);
    throw error;
  }
});

// Handle intelligent chat processing
ipcMain.handle('intelligent-chat', async (event, userMessage, images, projectPath, contentPath, anthropicApiKey) => {
  return new Promise((resolve, reject) => {
    console.log('Starting intelligent chat processing...');
    console.log('User message:', userMessage.substring(0, 100) + '...');
    console.log('Images count:', images ? images.length : 0);
    
    // Resolve content path relative to app directory
    const resolvedContentPath = path.resolve(__dirname, '..', contentPath);
    console.log('Resolved content path:', resolvedContentPath);
    
    // Path to the Python chat script
    const scriptPath = path.join(__dirname, '..', 'src', 'chatbot', 'intelligent_chat.py');
    
    // Prepare images JSON
    const imagesJson = images && images.length > 0 ? JSON.stringify(images) : 'null';
    
    // Spawn Python process for intelligent chat
    const pythonProcess = spawn('python3', [
      scriptPath,
      userMessage,
      imagesJson,
      projectPath,
      resolvedContentPath,
      anthropicApiKey
    ], {
      cwd: path.join(__dirname, '..')
    });
    
    let stdout = '';
    let stderr = '';
    
    pythonProcess.stdout.on('data', (data) => {
      stdout += data.toString();
      console.log('Chat stdout:', data.toString());
    });
    
    pythonProcess.stderr.on('data', (data) => {
      stderr += data.toString();
      console.error('Chat stderr:', data.toString());
    });
    
    pythonProcess.on('close', (code) => {
      if (code === 0) {
        try {
          const result = JSON.parse(stdout);
          console.log('Intelligent chat completed successfully');
          resolve(result);
        } catch (e) {
          reject(new Error('Failed to parse chat response: ' + e.message));
        }
      } else {
        reject(new Error(`Intelligent chat failed with code ${code}: ${stderr}`));
      }
    });
    
    pythonProcess.on('error', (error) => {
      console.error('Failed to start chat process:', error);
      reject(new Error('Failed to start intelligent chat process: ' + error.message));
    });
  });
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