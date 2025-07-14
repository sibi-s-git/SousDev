import React, { useState, useEffect } from 'react';
import { StatusBar } from 'expo-status-bar';
import { StyleSheet, View } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

import { SetupScreen } from './screens/SetupScreen';
import { VoiceScreen } from './screens/VoiceScreen';

export default function App() {
  const [isSetupComplete, setIsSetupComplete] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    checkSetupStatus();
  }, []);

  const checkSetupStatus = async () => {
    try {
      const projectFolder = await AsyncStorage.getItem('PROJECT_FOLDER');
      const claudeApiKey = await AsyncStorage.getItem('CLAUDE_API_KEY');
      
      // Setup is complete if both values exist
      setIsSetupComplete(!!(projectFolder && claudeApiKey));
    } catch (error) {
      console.error('Error checking setup status:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSetupComplete = () => {
    setIsSetupComplete(true);
  };

  if (isLoading) {
    // You could add a loading screen here
    return <View style={styles.container} />;
  }

  return (
    <View style={styles.container}>
      <StatusBar style="light" />
      {isSetupComplete ? (
        <VoiceScreen />
      ) : (
        <SetupScreen onSetupComplete={handleSetupComplete} />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
}); 