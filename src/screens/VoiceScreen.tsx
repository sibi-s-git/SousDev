import React, { useState, useEffect, useRef } from 'react';
import VoiceVisualizer from '../components/VoiceVisualizer';
import './VoiceScreen.css';

interface VoiceScreenProps {
  folderPath: string;
  claudeApiKey: string;
  onReset: () => void;
}

const VoiceScreen: React.FC<VoiceScreenProps> = ({ folderPath, claudeApiKey, onReset }) => {
  const [isListening, setIsListening] = useState<boolean>(false);
  const [transcript, setTranscript] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [audioLevel, setAudioLevel] = useState<number>(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);

  // Initialize audio context and analyzer
  useEffect(() => {
    const initializeAudio = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioContextRef.current = new AudioContext();
        analyserRef.current = audioContextRef.current.createAnalyser();
        
        const source = audioContextRef.current.createMediaStreamSource(stream);
        source.connect(analyserRef.current);
        
        analyserRef.current.fftSize = 256;
        
        // Start audio level monitoring
        const updateAudioLevel = () => {
          if (analyserRef.current && isListening) {
            const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
            analyserRef.current.getByteFrequencyData(dataArray);
            
            const average = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length;
            setAudioLevel(average / 255); // Normalize to 0-1
          }
          requestAnimationFrame(updateAudioLevel);
        };
        
        updateAudioLevel();
        
      } catch (error) {
        console.error('Error accessing microphone:', error);
      }
    };
    
    initializeAudio();
    
    return () => {
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, [isListening]);

  const startListening = () => {
    setIsListening(true);
    setTranscript('');
    
    // Here you would integrate with your Python backend for speech recognition
    // For now, this is a placeholder
    console.log('Starting voice recognition...');
  };

  const stopListening = () => {
    setIsListening(false);
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
  };

  const handleProcessCommand = async () => {
    if (!transcript.trim()) return;
    
    setIsProcessing(true);
    
    try {
      // Here you would call your Python backend with the transcript
      // and the folderPath and claudeApiKey for processing
      console.log('Processing command:', transcript);
      console.log('Folder path:', folderPath);
      console.log('API key available:', !!claudeApiKey);
      
      // Simulate processing delay
      await new Promise(resolve => setTimeout(resolve, 2000));
      
    } catch (error) {
      console.error('Error processing command:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="voice-screen">
      <div className="voice-header">
        <h1>SousDev</h1>
        <div className="project-info">
          <span className="folder-path">{folderPath}</span>
          <button onClick={onReset} className="reset-btn">
            Change Settings
          </button>
        </div>
      </div>
      
      <div className="voice-content">
        <VoiceVisualizer 
          isListening={isListening}
          audioLevel={audioLevel}
          onToggleListening={isListening ? stopListening : startListening}
        />
        
        <div className="transcript-section">
          <div className="transcript-container">
            <h3>Transcript</h3>
            <div className="transcript-text">
              {transcript || 'Say something...'}
            </div>
          </div>
          
          <div className="controls">
            <button 
              onClick={isListening ? stopListening : startListening}
              className={`control-btn ${isListening ? 'listening' : ''}`}
            >
              {isListening ? 'Stop Listening' : 'Start Listening'}
            </button>
            
            <button 
              onClick={handleProcessCommand}
              disabled={!transcript.trim() || isProcessing}
              className="control-btn process-btn"
            >
              {isProcessing ? 'Processing...' : 'Process Command'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VoiceScreen; 