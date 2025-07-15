import React, { useState } from 'react';
import SetupScreen from './screens/SetupScreen';
import VoiceScreen from './screens/VoiceScreen';
import './App.css';

interface AppState {
  folderPath: string | null;
  anthropicApiKey: string | null;
  openaiApiKey: string | null;
  isSetupComplete: boolean;
}

function App() {
  const [appState, setAppState] = useState<AppState>({
    folderPath: null,
    anthropicApiKey: null,
    openaiApiKey: null,
    isSetupComplete: false
  });

  const handleSetupComplete = (folderPath: string, anthropicApiKey: string, openaiApiKey: string) => {
    setAppState({
      folderPath,
      anthropicApiKey,
      openaiApiKey,
      isSetupComplete: true
    });
  };

  const handleReset = () => {
    setAppState({
      folderPath: null,
      anthropicApiKey: null,
      openaiApiKey: null,
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
          anthropicApiKey={appState.anthropicApiKey!}
          openaiApiKey={appState.openaiApiKey!}
          onReset={handleReset}
        />
      )}
    </div>
  );
}

export default App; 