import React, { useState } from 'react';
import './SetupScreen.css';

interface SetupScreenProps {
  onSetupComplete: (folderPath: string, claudeApiKey: string) => void;
}

const SetupScreen: React.FC<SetupScreenProps> = ({ onSetupComplete }) => {
  const [folderPath, setFolderPath] = useState<string>('');
  const [claudeApiKey, setClaudeApiKey] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errors, setErrors] = useState<{folder?: string; apiKey?: string}>({});

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

  const handleSave = () => {
    const newErrors: {folder?: string; apiKey?: string} = {};
    
    if (!folderPath.trim()) {
      newErrors.folder = 'Please select a folder';
    }
    
    if (!claudeApiKey.trim()) {
      newErrors.apiKey = 'Please enter your Claude API key';
    } else if (!claudeApiKey.startsWith('sk-ant-')) {
      newErrors.apiKey = 'Invalid Claude API key format';
    }
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    
    setIsLoading(true);
    
    // Simulate save delay
    setTimeout(() => {
      onSetupComplete(folderPath, claudeApiKey);
      setIsLoading(false);
    }, 500);
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
            <label htmlFor="claude-api-key">Claude API Key</label>
            <input
              id="claude-api-key"
              type="password"
              value={claudeApiKey}
              onChange={(e) => {
                setClaudeApiKey(e.target.value);
                setErrors(prev => ({ ...prev, apiKey: undefined }));
              }}
              placeholder="sk-ant-..."
              className={errors.apiKey ? 'error' : ''}
            />
            {errors.apiKey && <span className="error-text">{errors.apiKey}</span>}
          </div>
          
          <button 
            onClick={handleSave}
            disabled={isLoading}
            className="save-btn"
          >
            {isLoading ? 'Saving...' : 'Get Started'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SetupScreen; 