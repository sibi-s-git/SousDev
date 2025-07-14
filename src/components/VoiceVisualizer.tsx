import React, { useEffect, useRef } from 'react';
import './VoiceVisualizer.css';

interface VoiceVisualizerProps {
  isListening: boolean;
  audioLevel: number;
  onToggleListening: () => void;
}

const VoiceVisualizer: React.FC<VoiceVisualizerProps> = ({ 
  isListening, 
  audioLevel, 
  onToggleListening 
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number | undefined>(undefined);

  useEffect(() => {
    if (!canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const baseRadius = 40;
    
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      if (isListening) {
        // Animated pulsing circle based on audio level
        const pulseRadius = baseRadius + (audioLevel * 20);
        const time = Date.now() * 0.005;
        
        // Outer pulse ring
        ctx.beginPath();
        ctx.arc(centerX, centerY, pulseRadius + Math.sin(time) * 10, 0, 2 * Math.PI);
        ctx.strokeStyle = `rgba(74, 144, 226, ${0.3 + audioLevel * 0.3})`;
        ctx.lineWidth = 3;
        ctx.stroke();
        
        // Inner circle
        ctx.beginPath();
        ctx.arc(centerX, centerY, pulseRadius, 0, 2 * Math.PI);
        ctx.fillStyle = `rgba(74, 144, 226, ${0.7 + audioLevel * 0.3})`;
        ctx.fill();
        
        // Audio level bars around the circle
        const barCount = 20;
        for (let i = 0; i < barCount; i++) {
          const angle = (i / barCount) * 2 * Math.PI;
          const barHeight = 5 + audioLevel * 25 + Math.sin(time + i) * 5;
          const startRadius = pulseRadius + 15;
          const endRadius = startRadius + barHeight;
          
          const startX = centerX + Math.cos(angle) * startRadius;
          const startY = centerY + Math.sin(angle) * startRadius;
          const endX = centerX + Math.cos(angle) * endRadius;
          const endY = centerY + Math.sin(angle) * endRadius;
          
          ctx.beginPath();
          ctx.moveTo(startX, startY);
          ctx.lineTo(endX, endY);
          ctx.strokeStyle = `rgba(74, 144, 226, ${0.5 + audioLevel * 0.5})`;
          ctx.lineWidth = 3;
          ctx.stroke();
        }
      } else {
        // Static circle when not listening
        ctx.beginPath();
        ctx.arc(centerX, centerY, baseRadius, 0, 2 * Math.PI);
        ctx.fillStyle = 'rgba(100, 100, 100, 0.5)';
        ctx.fill();
        ctx.strokeStyle = 'rgba(150, 150, 150, 0.8)';
        ctx.lineWidth = 2;
        ctx.stroke();
      }
      
      animationRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isListening, audioLevel]);

  return (
    <div className="voice-visualizer">
      <canvas
        ref={canvasRef}
        width={300}
        height={300}
        onClick={onToggleListening}
        className="visualizer-canvas"
      />
      <div className="visualizer-status">
        {isListening ? (
          <div className="status-listening">
            <div className="pulse-dot"></div>
            <span>Listening...</span>
          </div>
        ) : (
          <span className="status-idle">Click to start listening</span>
        )}
      </div>
    </div>
  );
};

export default VoiceVisualizer; 