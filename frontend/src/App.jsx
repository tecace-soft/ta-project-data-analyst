import React from 'react';
import { DataProvider } from './contexts/DataContext';
import UpdateButton from './components/UpdateButton';
import ProjectCharts from './components/ProjectCharts';

function App() {
    return (
        <DataProvider>
            <div className="min-h-screen bg-gray-100">
                <div className="container mx-auto px-4 py-8">
                    <h1 className="text-3xl font-bold text-gray-900 mb-8">
                        Project Portfolio Dashboard
                    </h1>
                    <UpdateButton />
                    <ProjectCharts />
                </div>
            </div>
        </DataProvider>
    );
}

export default App; 