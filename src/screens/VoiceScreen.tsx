import React, { useState, useRef } from 'react';
import './VoiceScreen.css';

interface VoiceScreenProps {
  folderPath: string;
  anthropicApiKey: string;
  openaiApiKey: string;
  onReset: () => void;
}

interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  images?: string[];
  timestamp: Date;
}

const VoiceScreen: React.FC<VoiceScreenProps> = ({ folderPath, anthropicApiKey, openaiApiKey, onReset }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState<string>('');
  const [uploadedImages, setUploadedImages] = useState<string[]>([]);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [isReloading, setIsReloading] = useState<boolean>(false);
  const [isDragOver, setIsDragOver] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  const handleReload = async () => {
    if (isReloading) return;
    
    setIsReloading(true);
    try {
      // Get the project name from the folder path
      const projectName = folderPath.split('/').pop() || 'Unknown Project';
      const contentPath = `content/${projectName}`;
      
      // Call the combined reload process (analysis + vectorization)
      const reloadResult = await (window as any).electronAPI.reloadProject(
        folderPath, 
        contentPath, 
        openaiApiKey, 
        anthropicApiKey
      );
      
      console.log('Reload result:', reloadResult);
      
      // Add a success message to indicate reload completion
      const reloadMessage: ChatMessage = {
        id: Date.now().toString(),
        type: 'assistant',
        content: '🔄 Project refresh completed! Both project analysis and vectorization have been updated with the latest changes.',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, reloadMessage]);
      
      // Scroll to bottom to show the new message
      setTimeout(() => {
        if (chatContainerRef.current) {
          chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
        }
      }, 100);
      
    } catch (error) {
      console.error('Error during project reload:', error);
      
      // Add error message to chat
      const errorMessage: ChatMessage = {
        id: Date.now().toString(),
        type: 'assistant',
        content: '❌ Failed to refresh project knowledge. Please check your API keys and try again.',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsReloading(false);
    }
  };

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files) return;

    processImageFiles(Array.from(files));
  };

  const processImageFiles = (files: File[]) => {
    files.forEach(file => {
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (e) => {
          if (e.target?.result) {
            setUploadedImages(prev => [...prev, e.target!.result as string]);
          }
        };
        reader.readAsDataURL(file);
      }
    });
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isDragOver) {
      setIsDragOver(true);
    }
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    // Only set isDragOver to false if we're leaving the entire drop zone
    if (!e.currentTarget.contains(e.relatedTarget as Node)) {
      setIsDragOver(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    const files = Array.from(e.dataTransfer.files);
    const imageFiles = files.filter(file => file.type.startsWith('image/'));
    
    if (imageFiles.length > 0) {
      processImageFiles(imageFiles);
    }
  };

  const removeImage = (index: number) => {
    setUploadedImages(prev => prev.filter((_, i) => i !== index));
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() && uploadedImages.length === 0) return;
    
    // Create user message
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: inputMessage.trim(),
      images: uploadedImages.length > 0 ? [...uploadedImages] : undefined,
      timestamp: new Date()
    };
    
    // Add user message to chat
    setMessages(prev => [...prev, userMessage]);
    
    // Clear input and show processing state
    const userInput = inputMessage.trim();
    const userImages = [...uploadedImages];
    setInputMessage('');
    setUploadedImages([]);
    setIsProcessing(true);
    
    // Scroll to bottom
    setTimeout(() => {
      if (chatContainerRef.current) {
        chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
      }
    }, 100);
    
    try {
      // Get project info
      const projectName = folderPath.split('/').pop() || 'Unknown Project';
      const contentPath = `content/${projectName}`;
      
      // Call intelligent chat system
      const chatResult = await (window as any).electronAPI.intelligentChat(
        userInput,
        userImages,
        folderPath,
        contentPath,
        anthropicApiKey
      );
      
      if (chatResult.success) {
        // Add AI response to chat
        const aiMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: chatResult.response,
          timestamp: new Date()
        };
        
        setMessages(prev => [...prev, aiMessage]);
        
        console.log('Search strategy used:', chatResult.search_strategy);
        console.log('Search results found:', chatResult.search_results_count);
      } else {
        // Add error message
        const errorMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: `❌ Sorry, I encountered an error: ${chatResult.error}`,
          timestamp: new Date()
        };
        
        setMessages(prev => [...prev, errorMessage]);
      }
      
    } catch (error) {
      console.error('Error in intelligent chat:', error);
      
      // Add error message to chat
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: '❌ Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsProcessing(false);
      
      // Scroll to bottom again to show the response
      setTimeout(() => {
        if (chatContainerRef.current) {
          chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
        }
      }, 100);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const openImageModal = (imageSrc: string) => {
    setSelectedImage(imageSrc);
  };

  const closeImageModal = () => {
    setSelectedImage(null);
  };

  return (
    <div 
      className="voice-screen"
      onDragOver={handleDragOver}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {/* Drag Overlay */}
      {isDragOver && (
        <div className="drag-overlay">
          <div className="drag-message">
            <div className="drag-icon">📁</div>
            <p>Drop images here</p>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="chat-header">
        <div className="header-left">
          <button onClick={onReset} className="change-settings-btn">
            Change Settings
          </button>
          <span className="project-location">{folderPath}</span>
        </div>
        <div className="header-right">
          <button onClick={handleReload} disabled={isReloading} className="reload-btn">
            {isReloading ? 'Refreshing...' : 'Refresh Knowledge'}
          </button>
        </div>
      </div>

      {/* Divider Line */}
      <div className="header-divider"></div>

      {/* Chat Container */}
      <div className="chat-container" ref={chatContainerRef}>
        {messages.length === 0 ? (
          <div className="empty-chat">
            <p>Start a conversation about your project: {folderPath.split('/').pop() || 'Unknown Project'}</p>
          </div>
        ) : (
          messages.map((message) => (
            <div key={message.id} className={`message ${message.type}`}>
              {message.images && (
                <div className="message-images">
                  {message.images.map((img, index) => (
                    <img
                      key={index}
                      src={img}
                      alt={`Uploaded ${index + 1}`}
                      className="message-image"
                      onClick={() => openImageModal(img)}
                    />
                  ))}
                </div>
              )}
              <div className="message-content">
                {message.content}
              </div>
              <div className="message-timestamp">
                {message.timestamp.toLocaleTimeString()}
              </div>
            </div>
          ))
        )}
        
        {isProcessing && (
          <div className="message assistant">
            <div className="message-content typing">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="chat-input-container">
        {/* Image Preview */}
        {uploadedImages.length > 0 && (
          <div className="image-preview-container">
            {uploadedImages.map((img, index) => (
              <div key={index} className="image-preview">
                <img src={img} alt={`Preview ${index + 1}`} />
                <button 
                  onClick={() => removeImage(index)}
                  className="remove-image-btn"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Input Row */}
        <div className="input-row">
          <button 
            onClick={() => fileInputRef.current?.click()}
            className="upload-btn"
            title="Upload images"
          >
            📎
          </button>
          
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about your project..."
            className="message-input"
            rows={1}
          />
          
          <button 
            onClick={handleSendMessage}
            disabled={isProcessing || (!inputMessage.trim() && uploadedImages.length === 0)}
            className="send-btn"
          >
            Send
          </button>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          multiple
          onChange={handleImageUpload}
          style={{ display: 'none' }}
        />
      </div>

      {/* Image Modal */}
      {selectedImage && (
        <div className="image-modal" onClick={closeImageModal}>
          <div className="image-modal-content">
            <img src={selectedImage} alt="Enlarged" />
            <button className="close-modal-btn" onClick={closeImageModal}>
              ×
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default VoiceScreen; 