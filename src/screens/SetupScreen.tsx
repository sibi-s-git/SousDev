import React, { useState, useEffect } from 'react';
import './SetupScreen.css';

interface SetupScreenProps {
  onSetupComplete: (folderPath: string, anthropicApiKey: string, openaiApiKey: string) => void;
}

const SetupScreen: React.FC<SetupScreenProps> = ({ onSetupComplete }) => {
  const [folderPath, setFolderPath] = useState<string>('');
  const [anthropicApiKey, setAnthropicApiKey] = useState<string>('');
  const [openaiApiKey, setOpenaiApiKey] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [loadingMessage, setLoadingMessage] = useState<string>('');
  const [errors, setErrors] = useState<{folder?: string; anthropicApiKey?: string; openaiApiKey?: string}>({});

  // Load environment variables on component mount
  useEffect(() => {
    const loadEnvVars = async () => {
      try {
        const envVars = await window.electronAPI.loadEnvVars();
        if (envVars.PROJECT_FOLDER) {
          setFolderPath(envVars.PROJECT_FOLDER);
        }
        if (envVars.ANTHROPIC_API_KEY) {
          setAnthropicApiKey(envVars.ANTHROPIC_API_KEY);
        }
        if (envVars.OPENAI_API_KEY) {
          setOpenaiApiKey(envVars.OPENAI_API_KEY);
        }
      } catch (error) {
        console.error('Error loading environment variables:', error);
      }
    };
    
    loadEnvVars();
  }, []);

  const handleChooseFolder = async () => {
    try {
      const selectedPath = await window.electronAPI.selectFolder();
      if (selectedPath) {
        setFolderPath(selectedPath);
        setErrors(prev => ({ ...prev, folder: undefined }));
      }
    } catch (error) {
      console.error('Error selecting folder:', error);
    }
  };

  const handleSave = async () => {
    const newErrors: {folder?: string; anthropicApiKey?: string; openaiApiKey?: string} = {};
    
    if (!folderPath.trim()) {
      newErrors.folder = 'Please select a folder';
    }
    
    if (!anthropicApiKey.trim()) {
      newErrors.anthropicApiKey = 'Please enter your Anthropic API key';
    } else if (!anthropicApiKey.startsWith('sk-ant-')) {
      newErrors.anthropicApiKey = 'Invalid Anthropic API key format';
    }

    if (!openaiApiKey.trim()) {
      newErrors.openaiApiKey = 'Please enter your OpenAI API key';
    } else if (!openaiApiKey.startsWith('sk-')) {
      newErrors.openaiApiKey = 'Invalid OpenAI API key format';
    }
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    
    setIsLoading(true);
    setLoadingMessage('Saving settings...');
    
    try {
      // Save environment variables
      const envVars = {
        PROJECT_FOLDER: folderPath,
        ANTHROPIC_API_KEY: anthropicApiKey,
        OPENAI_API_KEY: openaiApiKey
      };
      
      await window.electronAPI.saveEnvVars(envVars);
      
      // Get the project name from the folder path and create correct content path
      const projectName = folderPath.split('/').pop() || 'Unknown Project';
      const contentPath = `content/${projectName}`;
      
      // Step 1: Check if project intelligence already exists
      setLoadingMessage('Checking existing project data...');
      const projectCheck = await window.electronAPI.checkProjectIntelligence(contentPath);
      console.log('Project intelligence check:', projectCheck);
      
      // Step 2: Only proceed if either intelligence OR embeddings are missing
      if (!projectCheck.intelligence_exists || !projectCheck.embeddings_exist) {
        
        // Run project analysis if intelligence doesn't exist
        if (!projectCheck.intelligence_exists) {
          setLoadingMessage('Analyzing project structure...');
          console.log('Starting project analysis...');
          
          try {
            const analysisResult = await window.electronAPI.analyzeProject(
              folderPath,
              contentPath,
              anthropicApiKey
            );
            
            console.log('Analysis result:', analysisResult);
            console.log('Project analysis completed successfully');
          } catch (analysisError) {
            console.error('Project analysis failed:', analysisError);
            // Continue anyway - analysis failure shouldn't block setup
          }
        } else {
          console.log('Project intelligence already exists, skipping analysis');
        }
        
        // Run vectorization if embeddings don't exist
        if (!projectCheck.embeddings_exist) {
          setLoadingMessage('Vectorizing project files...');
          console.log('Starting project vectorization...');
          
          try {
            const vectorizationResult = await window.electronAPI.vectorizeProject(
              folderPath,
              contentPath,
              openaiApiKey
            );
            
            console.log('Vectorization result:', vectorizationResult);
            
            if (vectorizationResult.status === 'completed') {
              console.log(`Successfully vectorized ${vectorizationResult.total_files} files into ${vectorizationResult.total_chunks} chunks`);
            } else if (vectorizationResult.status === 'no_files') {
              console.log('No supported files found in project for vectorization');
            } else {
              console.warn('Vectorization completed with status:', vectorizationResult.status);
            }
          } catch (vectorizationError) {
            console.error('Vectorization failed:', vectorizationError);
            // Don't block the setup process if vectorization fails
          }
        } else {
          console.log('Embeddings already exist, skipping vectorization');
        }
        
      } else {
        console.log('Both project intelligence and embeddings already exist - skipping all processing');
        setLoadingMessage('Using existing project data...');
        // Small delay for user feedback
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
      
              // Complete setup
        setLoadingMessage('Finalizing...');
        setTimeout(() => {
          onSetupComplete(folderPath, anthropicApiKey, openaiApiKey);
          setIsLoading(false);
          setLoadingMessage('');
        }, 1000);
      } catch (error) {
        console.error('Error saving environment variables:', error);
        setIsLoading(false);
        setLoadingMessage('');
      }
  };

  return (
    <div className="setup-screen">
      <div className="setup-container">
        <div className="setup-form">
          <div className="input-group">
            <label htmlFor="folder-path">Project Folder</label>
            <div className="folder-input-container">
              <input
                id="folder-path"
                type="text"
                value={folderPath}
                placeholder="Select your project folder..."
                readOnly
                className={errors.folder ? 'error' : ''}
              />
              <button 
                onClick={handleChooseFolder}
                className="choose-folder-btn"
                type="button"
              >
                Choose Folder
              </button>
            </div>
            {errors.folder && <span className="error-text">{errors.folder}</span>}
          </div>
          
          <div className="input-group">
            <label htmlFor="anthropic-api-key">Anthropic API Key</label>
            <input
              id="anthropic-api-key"
              type="password"
              value={anthropicApiKey}
              onChange={(e) => {
                setAnthropicApiKey(e.target.value);
                setErrors(prev => ({ ...prev, anthropicApiKey: undefined }));
              }}
              placeholder="sk-ant-..."
              className={errors.anthropicApiKey ? 'error' : ''}
            />
            {errors.anthropicApiKey && <span className="error-text">{errors.anthropicApiKey}</span>}
          </div>

          <div className="input-group">
            <label htmlFor="openai-api-key">OpenAI API Key</label>
                         <input
               id="openai-api-key"
               type="password"
               value={openaiApiKey}
               onChange={(e) => {
                 setOpenaiApiKey(e.target.value);
                 setErrors(prev => ({ ...prev, openaiApiKey: undefined }));
               }}
               placeholder="sk-..."
               className={errors.openaiApiKey ? 'error' : ''}
             />
            {errors.openaiApiKey && <span className="error-text">{errors.openaiApiKey}</span>}
          </div>
          
          <button 
            onClick={handleSave}
            disabled={isLoading}
            className="save-btn"
          >
            {isLoading ? (loadingMessage || 'Processing...') : 'Get Started'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SetupScreen; 