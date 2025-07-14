import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export const VoiceScreen: React.FC = () => {
  return (
    <View style={styles.container}>
      <Text style={styles.text}>Voice Visualizer Coming Soon!</Text>
      <Text style={styles.subText}>
        This is where the voice assistant will live
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 30,
  },
  text: {
    fontSize: 24,
    color: '#fff',
    textAlign: 'center',
    marginBottom: 20,
    fontWeight: '600',
  },
  subText: {
    fontSize: 16,
    color: '#888',
    textAlign: 'center',
  },
}); 