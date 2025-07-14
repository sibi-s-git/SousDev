import React, { useState, useEffect } from 'react';
import SetupScreen from './screens/SetupScreen';
import VoiceScreen from './screens/VoiceScreen';
import './App.css';



interface AppState {
  folderPath: string | null;
  claudeApiKey: string | null;
  isSetupComplete: boolean;
}

function App() {
  const [appState, setAppState] = useState<AppState>({
    folderPath: null,
    claudeApiKey: null,
    isSetupComplete: false
  });

  // Load saved settings from localStorage
  useEffect(() => {
    const savedFolderPath = localStorage.getItem('sousdev_folderPath');
    const savedApiKey = localStorage.getItem('sousdev_claudeApiKey');
    
    if (savedFolderPath && savedApiKey) {
      setAppState({
        folderPath: savedFolderPath,
        claudeApiKey: savedApiKey,
        isSetupComplete: true
      });
    }
  }, []);

  const handleSetupComplete = (folderPath: string, claudeApiKey: string) => {
    // Save to localStorage
    localStorage.setItem('sousdev_folderPath', folderPath);
    localStorage.setItem('sousdev_claudeApiKey', claudeApiKey);
    
    setAppState({
      folderPath,
      claudeApiKey,
      isSetupComplete: true
    });
  };

  const handleReset = () => {
    localStorage.removeItem('sousdev_folderPath');
    localStorage.removeItem('sousdev_claudeApiKey');
    setAppState({
      folderPath: null,
      claudeApiKey: null,
      isSetupComplete: false
    });
  };

  return (
    <div className="App">
      <div className="app-header">
        <img src="/assets/logo.png" alt="SousDev" className="app-logo" />
      </div>
      
      {!appState.isSetupComplete ? (
        <SetupScreen onSetupComplete={handleSetupComplete} />
      ) : (
        <VoiceScreen 
          folderPath={appState.folderPath!}
          claudeApiKey={appState.claudeApiKey!}
          onReset={handleReset}
        />
      )}
    </div>
  );
}

export default App; 