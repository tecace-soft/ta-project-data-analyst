import React, { useState } from 'react';
import { DataProvider } from './contexts/DataContext';
import UpdateButton from './components/UpdateButton';
import ProjectCharts from './components/ProjectCharts';
import ChatWindow from './components/ChatWindow';
import './ChatWindow.css';

function App() {
    const [isChatVisible, setIsChatVisible] = useState(false);
    const [dataLoaded, setDataLoaded] = useState(false);

    const handleDataUpdated = () => {
        // Show the chat window when data is updated and mark data as loaded
        setIsChatVisible(true);
        setDataLoaded(true);
    };

    return (
        <DataProvider>
            <div className="min-h-screen bg-gray-100 relative">
                <div className="container mx-auto px-4 py-8">
                    <h1 className="text-3xl font-bold text-gray-900 mb-8">
                        Project Portfolio Dashboard
                    </h1>
                    <UpdateButton onDataUpdated={handleDataUpdated} />
                    <ProjectCharts />
                </div>
                
                {/* Chat Window Component - Only render when data is loaded */}
                {dataLoaded && (
                    <ChatWindow 
                        isVisible={isChatVisible} 
                        onClose={() => setIsChatVisible(false)} 
                    />
                )}
                
                {/* Toggle Chat Button - Only show after data is loaded */}
                {dataLoaded && !isChatVisible && (
                    <button
                        onClick={() => setIsChatVisible(true)}
                        className="chat-toggle-button"
                        aria-label="Open chat"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                        </svg>
                    </button>
                )}
            </div>
        </DataProvider>
    );
}

export default App; 