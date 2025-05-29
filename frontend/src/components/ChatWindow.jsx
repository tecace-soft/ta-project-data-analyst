import React, { useState, useRef, useEffect } from 'react';
import { sendChatMessage } from '../services/chatApi';
import '../ChatWindow.css';
import { useData } from '../contexts/DataContext';
import ReactMarkdown from 'react-markdown';

const ChatWindow = ({ isVisible, onClose }) => {
    // Get project and invoice data from context
    const { data: projectData, invoiceData } = useData();
    
    const [messages, setMessages] = useState([
        { role: 'system', content: 'Hello! I can help you analyze your project data. What would you like to know?' }
    ]);
    const [input, setInput] = useState('');
    const messagesEndRef = useRef(null);
    const [isLoading, setIsLoading] = useState(false);
    
    // Generate a random session ID when the component mounts
    // This will be used to maintain the conversation context
    const [sessionId] = useState(() => Math.floor(Math.random() * 1000000));
    
    // Log the sessionId and data once on mount
    useEffect(() => {
        console.log(`Chat session initialized with ID: ${sessionId}`);
        console.log(`Current project data count: ${projectData?.length || 0}`);
        console.log(`Current invoice data count: ${invoiceData?.length || 0}`);
    }, [sessionId, projectData, invoiceData]);

    // Scroll to bottom of messages when new messages are added
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // Helper function to extract output from response
    const extractOutputFromResponse = (response) => {
        // Log the raw response for debugging
        console.log('Raw API response:', response);
        
        // If response is a string, return it directly
        if (typeof response === 'string') {
            return response;
        }
        
        // Handle array response with the specific structure [{ output: "..." }]
        if (Array.isArray(response)) {
            if (response.length > 0 && response[0] && typeof response[0] === 'object' && 'output' in response[0]) {
                return response[0].output;
            }
            
            // Try to find any object with an output property in the array
            for (const item of response) {
                if (item && typeof item === 'object' && 'output' in item) {
                    return item.output;
                }
            }
        }
        
        // If response is an object with an output field, extract it
        if (response && typeof response === 'object') {
            if ('output' in response) {
                return response.output;
            }
            
            // Handle nested response structure
            if (response.response && typeof response.response === 'object' && 'output' in response.response) {
                return response.response.output;
            }
        }
        
        // If we can't extract an output field, stringify the whole response
        try {
            return JSON.stringify(response, null, 2);
        } catch (e) {
            return String(response);
        }
    };
    
    // Function to render message content
    const renderMessageContent = (content) => {
        if (typeof content !== 'string') {
            content = String(content);
        }
        
        // Check if content looks like JSON
        if (content.trim().startsWith('{') || content.trim().startsWith('[')) {
            try {
                // Try to parse as JSON for syntax highlighting
                const parsedJson = JSON.parse(content);
                return (
                    <pre>
                        <code>{JSON.stringify(parsedJson, null, 2)}</code>
                    </pre>
                );
            } catch (e) {
                // If parsing fails, treat as markdown
                return <ReactMarkdown>{content}</ReactMarkdown>;
            }
        } else {
            // Render as markdown
            return <ReactMarkdown>{content}</ReactMarkdown>;
        }
    };

    // Handle sending a message
    const handleSendMessage = async () => {
        if (input.trim() === '') return;
        
        // Add user message to chat
        const userMessage = { role: 'user', content: input };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);
        
        try {
            // Call the chat API service with data and session ID
            const response = await sendChatMessage(
                input, 
                projectData || [], 
                invoiceData || [], 
                sessionId
            );
            
            // Extract output from the response
            const outputContent = extractOutputFromResponse(response.response);
            
            // Add response to chat
            const botResponse = {
                role: 'assistant',
                content: outputContent
            };
            
            setMessages(prev => [...prev, botResponse]);
        } catch (error) {
            console.error('Error getting chat response:', error);
            setMessages(prev => [...prev, { 
                role: 'assistant', 
                content: 'Sorry, I encountered an error processing your request.' 
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    // Handle pressing Enter in the input
    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    return (
        <div className={`chat-window ${isVisible ? 'visible' : ''}`}>
            {/* Header */}
            <div className="chat-header">
                <h3>Data Assistant</h3>
                <button 
                    onClick={onClose}
                    className="close-button"
                    aria-label="Close chat"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>
            
            {/* Messages area */}
            <div className="messages-area">
                {messages.map((message, index) => (
                    <div 
                        key={index}
                        className={`message ${
                            message.role === 'user' 
                                ? 'user-message' 
                                : 'assistant-message'
                        }`}
                    >
                        {renderMessageContent(message.content)}
                    </div>
                ))}
                {isLoading && (
                    <div className="typing-indicator">
                        <div className="dots-container">
                            <div className="dot"></div>
                            <div className="dot"></div>
                            <div className="dot"></div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>
            
            {/* Input area */}
            <div className="input-area">
                <div className="input-container">
                    <textarea
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Type your question..."
                        className="chat-textarea"
                        rows={2}
                    />
                    <button
                        onClick={handleSendMessage}
                        disabled={input.trim() === '' || isLoading}
                        className="send-button"
                        aria-label="Send message"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                            <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ChatWindow; 