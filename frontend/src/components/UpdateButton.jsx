import React, { useState } from 'react';
import { uploadAndGetData, getGPTAnalysis } from '../services/api';
import { useData } from '../contexts/DataContext';
import ReactMarkdown from 'react-markdown';

const UpdateButton = ({ onDataUpdated }) => {
    const [isLoading, setIsLoading] = useState(false);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [error, setError] = useState(null);
    const { data, setData, invoiceData, setInvoiceData } = useData();
    const [selectedFile, setSelectedFile] = useState(null);
    const [analysis, setAnalysis] = useState(null);

    const handleFileChange = (event) => {
        const file = event.target.files[0];
        if (file) {
            setSelectedFile(file);
            setError(null);
            setAnalysis(null);
        }
    };

    const handleUpdate = async () => {
        if (!selectedFile) {
            setError('Please select a file first');
            return;
        }

        setIsLoading(true);
        setError(null);
        setAnalysis(null);

        console.log("======== STARTING DATA UPLOAD ========");
        console.log("File selected:", selectedFile.name);

        try {
            console.log("Calling uploadAndGetData API...");
            const response = await uploadAndGetData(selectedFile);
            console.log("API response received:", response);
            
            // Handle both new and legacy response formats
            if (response.projects && Array.isArray(response.projects)) {
                // New format with projects and invoices
                
                // DEBUG: Log exact structure of first few projects
                console.log("===== DETAILED PROJECT DATA STRUCTURE =====");
                if (response.projects.length > 0) {
                    console.log("First project exact structure:");
                    console.log(response.projects[0]);
                    
                    // Log all keys in the first project
                    console.log("All keys in first project:");
                    const keys = Object.keys(response.projects[0]);
                    console.log(keys);
                    
                    // Log all 2024/2025 related fields
                    console.log("All fields with 2024/2025:");
                    const yearFields = keys.filter(key => key.includes("2024") || key.includes("2025"));
                    yearFields.forEach(field => {
                        console.log(`${field}: ${response.projects[0][field]}`);
                    });
                    
                    // Look specifically for Jan-Dec fields
                    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                    console.log("Searching for specific month fields:");
                    for (const year of [2024, 2025]) {
                        for (const month of months) {
                            const fieldName = `${year} ${month}`;
                            console.log(`Field "${fieldName}" exists: ${fieldName in response.projects[0]}, value: ${response.projects[0][fieldName]}`);
                        }
                    }
                }
                console.log("===== END DETAILED PROJECT DATA STRUCTURE =====");
                
                console.log(`Before setting data. Current data length: ${data ? data.length : 0}`);
                console.log(`Setting new data with ${response.projects.length} projects and ${response.invoices?.length || 0} invoices`);
                setData(response.projects);
                setInvoiceData(response.invoices || []);
                console.log(`After calling setData(). This should trigger a recalculation.`);

                // Add a small delay and then verify the context was updated
                setTimeout(() => {
                    console.log("VERIFICATION CHECK: Current data context after update:", data);
                    if (data === response.projects) {
                        console.log("✅ Data context reference updated successfully!");
                    } else {
                        console.log("❌ Warning: Data context reference not updated as expected!");
                        if (data && data.length === response.projects.length) {
                            console.log("  Length matches, but reference is different (this is fine with React state)");
                        } else {
                            console.log("  Length mismatch or data is null/undefined!");
                        }
                    }
                }, 500);
                
                console.log(`Updated with ${response.projects.length} projects and ${response.invoices?.length || 0} invoices`);
            } else if (Array.isArray(response)) {
                // Legacy format (just an array of projects)
                console.log(`Setting legacy data format with ${response.length} projects`);
                setData(response);
                setInvoiceData([]);
                console.log(`Updated with ${response.length} projects (legacy format)`);
            }
            
            // Make GPT analysis optional
            if (true) { // Re-enabled GPT analysis
                // Trigger GPT analysis after successful data update
                setIsAnalyzing(true);
                try {
                    // Use the projects data for analysis (not the invoices)
                    const projectData = response.projects || response;
                    
                    console.log("Attempting to get GPT analysis...");
                    const analysisResult = await getGPTAnalysis(projectData);
                    
                    if (analysisResult) {
                        setAnalysis(analysisResult);
                        console.log("GPT analysis completed successfully");
                    } else {
                        console.warn("GPT analysis returned empty result");
                        setError("Analysis completed but returned no insights");
                    }
                } catch (analysisError) {
                    console.error("Error during GPT analysis:", analysisError);
                    // Don't fail the whole process if analysis doesn't work
                    setError(`Note: Data updated successfully, but analysis failed: ${analysisError.message}`);
                } finally {
                    setIsAnalyzing(false);
                }
            } else {
                // Skip GPT analysis
                console.log("Skipping GPT analysis to avoid API issues");
            }
            
            // Call the onDataUpdated callback if provided
            if (onDataUpdated && typeof onDataUpdated === 'function') {
                onDataUpdated();
            }
        } catch (err) {
            setError(err.message || 'Failed to update data');
            console.error("Error during upload:", err);
        } finally {
            setIsLoading(false);
            setIsAnalyzing(false);
            console.log("======== UPLOAD PROCESS COMPLETED ========");
        }
    };

    return (
        <div className="flex flex-col items-center gap-4">
            <div className="flex items-center gap-4">
                <input
                    type="file"
                    accept=".xlsx,.xls,.xlsm"
                    onChange={handleFileChange}
                    className="block w-full text-sm text-gray-500
                        file:mr-4 file:py-2 file:px-4
                        file:rounded-full file:border-0
                        file:text-sm file:font-semibold
                        file:bg-blue-50 file:text-blue-700
                        hover:file:bg-blue-100"
                />
                <button
                    onClick={handleUpdate}
                    disabled={isLoading || isAnalyzing || !selectedFile}
                    className={`px-4 py-2 rounded-md text-white font-medium
                        ${(isLoading || isAnalyzing || !selectedFile)
                            ? 'bg-gray-400 cursor-not-allowed'
                            : 'bg-blue-600 hover:bg-blue-700'
                        }`}
                >
                    {isLoading ? 'Updating...' : isAnalyzing ? 'Analyzing...' : 'Update Data'}
                </button>
            </div>
            
            {error && (
                <div className="text-red-500 text-sm">
                    {error}
                </div>
            )}
            {analysis && (
                <div className="mt-4 p-6 bg-white rounded-lg shadow-md w-full max-w-5xl">
                    <h3 className="text-xl font-semibold mb-4 text-blue-700 border-b pb-2">Business Analysis</h3>
                    <div className="prose prose-blue max-w-none">
                        <ReactMarkdown>{analysis}</ReactMarkdown>
                    </div>
                </div>
            )}
        </div>
    );
};

export default UpdateButton; 