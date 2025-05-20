import React, { useState } from 'react';
import { uploadAndGetData, getGPTAnalysis, analyzeExcelFile } from '../services/api';
import { useData } from '../contexts/DataContext';
import ReactMarkdown from 'react-markdown';

const UpdateButton = () => {
    const [isLoading, setIsLoading] = useState(false);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [isDiagnosing, setIsDiagnosing] = useState(false);
    const [error, setError] = useState(null);
    const { data, setData, invoiceData, setInvoiceData } = useData();
    const [selectedFile, setSelectedFile] = useState(null);
    const [analysis, setAnalysis] = useState(null);
    const [fileDetails, setFileDetails] = useState(null);
    const [showDetails, setShowDetails] = useState(false);
    const [excelDiagnostic, setExcelDiagnostic] = useState(null);
    const [showDiagnostic, setShowDiagnostic] = useState(false);

    const handleFileChange = (event) => {
        const file = event.target.files[0];
        if (file) {
            setSelectedFile(file);
            setError(null);
            setAnalysis(null);
            setExcelDiagnostic(null);
            setFileDetails({
                name: file.name,
                type: file.type,
                size: `${(file.size / 1024).toFixed(2)} KB`,
                lastModified: new Date(file.lastModified).toLocaleString()
            });
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
        setExcelDiagnostic(null);

        console.log("======== STARTING DATA UPLOAD ========");
        console.log("File selected:", selectedFile.name);

        try {
            console.log("Calling uploadAndGetData API...");
            const response = await uploadAndGetData(selectedFile);
            console.log("API response received:", response);
            
            // Store sheet names and other details from the response if available
            if (response.fileInfo) {
                setFileDetails(prev => ({
                    ...prev,
                    ...response.fileInfo
                }));
            }
            
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
        } catch (err) {
            setError(err.message || 'Failed to update data');
            console.error("Error during upload:", err);
        } finally {
            setIsLoading(false);
            setIsAnalyzing(false);
            console.log("======== UPLOAD PROCESS COMPLETED ========");
        }
    };

    const handleDiagnostic = async () => {
        if (!selectedFile) {
            setError('Please select a file first');
            return;
        }

        setIsDiagnosing(true);
        setError(null);
        
        try {
            const diagnosticResult = await analyzeExcelFile(selectedFile);
            setExcelDiagnostic(diagnosticResult);
            setShowDiagnostic(true);
            console.log('Diagnostic results:', diagnosticResult);
        } catch (err) {
            setError(`Excel diagnostic failed: ${err.message}`);
        } finally {
            setIsDiagnosing(false);
        }
    };

    // Add hard refresh function
    const handleHardRefresh = () => {
        console.log("PERFORMING HARD REFRESH - Clearing React cache and reloading page");
        
        // Reset the context data
        setData([]);
        setInvoiceData([]);
        
        // Clear localStorage if it's being used
        try {
            localStorage.removeItem('projectData');
            localStorage.removeItem('invoiceData');
        } catch (e) {
            console.error("Error clearing localStorage:", e);
        }
        
        // Force a full page reload
        setTimeout(() => {
            window.location.reload(true);
        }, 100);
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
                
                {selectedFile && (
                    <button
                        onClick={handleDiagnostic}
                        disabled={isDiagnosing}
                        className={`px-4 py-2 rounded-md text-white font-medium
                            ${isDiagnosing
                                ? 'bg-gray-400 cursor-not-allowed'
                                : 'bg-yellow-600 hover:bg-yellow-700'
                            }`}
                    >
                        {isDiagnosing ? 'Diagnosing...' : 'Diagnose Excel'}
                    </button>
                )}
                
                {/* Add Hard Refresh button */}
                <button
                    onClick={handleHardRefresh}
                    className="px-4 py-2 rounded-md text-white font-medium bg-red-600 hover:bg-red-700"
                >
                    Hard Refresh
                </button>
            </div>
            
            {fileDetails && (
                <div className="w-full">
                    <button 
                        onClick={() => setShowDetails(!showDetails)}
                        className="text-sm text-blue-600 hover:text-blue-800 flex items-center"
                    >
                        {showDetails ? '▼ Hide File Details' : '► Show File Details'}
                    </button>
                    
                    {showDetails && (
                        <div className="mt-2 p-3 bg-gray-50 rounded border text-sm">
                            <h4 className="font-semibold mb-2">File Details:</h4>
                            <ul className="space-y-1">
                                <li><span className="font-medium">Name:</span> {fileDetails.name}</li>
                                <li><span className="font-medium">Type:</span> {fileDetails.type}</li>
                                <li><span className="font-medium">Size:</span> {fileDetails.size}</li>
                                <li><span className="font-medium">Last Modified:</span> {fileDetails.lastModified}</li>
                                {fileDetails.sheetNames && (
                                    <li>
                                        <span className="font-medium">Available Sheets:</span>
                                        <ul className="list-disc list-inside pl-4 mt-1">
                                            {fileDetails.sheetNames.map((sheet, index) => (
                                                <li key={index} className={
                                                    sheet === 'Project Table' || 
                                                    sheet.toLowerCase().includes('invoice') || 
                                                    sheet.toLowerCase().includes('payment') ? 
                                                    'text-green-600 font-medium' : ''
                                                }>
                                                    {sheet}
                                                    {sheet === 'Project Table' && 
                                                        <span className="text-green-600 ml-2">(Used for project data)</span>
                                                    }
                                                    {sheet === 'Invoice Data Imported' && 
                                                        <span className="text-green-600 ml-2">(Used for invoice data)</span>
                                                    }
                                                    {sheet !== 'Project Table' && sheet !== 'Invoice Data Imported' && 
                                                     (sheet.toLowerCase().includes('invoice') || sheet.toLowerCase().includes('payment')) &&
                                                        <span className="text-yellow-600 ml-2">(Potential invoice data source)</span>
                                                    }
                                                </li>
                                            ))}
                                        </ul>
                                    </li>
                                )}
                            </ul>
                            
                            <div className="mt-2">
                                <h4 className="font-semibold">Data Summary:</h4>
                                <ul className="space-y-1">
                                    <li><span className="font-medium">Projects:</span> {fileDetails.projectCount || 0}</li>
                                    <li><span className="font-medium">Invoices:</span> {fileDetails.invoiceCount || 0}
                                        {fileDetails.invoiceCount === 0 && (
                                            <span className="text-red-500 ml-2">(No invoice data found!)</span>
                                        )}
                                    </li>
                                    {fileDetails.invoiceCount === 0 && (
                                        <li className="text-red-500 mt-2 p-2 bg-red-50 rounded border-red-200 border">
                                            <p className="font-semibold">Invoice Data Issues:</p>
                                            <p className="mt-1">The expected revenue chart needs invoice data to show actualized revenue. The system is looking for:</p>
                                            <ul className="list-disc list-inside pl-4 mt-1">
                                                <li>A sheet named "Invoice Data Imported" (or similar name containing "invoice" or "payment")</li>
                                                <li>Column A: Invoice ID</li>
                                                <li>Column B: Project Code</li>
                                                <li>Column C: Invoice Date</li>
                                                <li>Column O: Payment Amount (USD)</li>
                                            </ul>
                                            <p className="mt-2">Troubleshooting steps:</p>
                                            <ol className="list-decimal list-inside pl-4">
                                                <li>Check if your Excel file has an invoice data sheet</li>
                                                <li>Verify the sheet has data starting in row 2 (row 1 contains headers)</li>
                                                <li>Ensure Column O contains numeric payment amounts</li>
                                                <li>Try the "Diagnose Excel" button for detailed file analysis</li>
                                            </ol>
                                        </li>
                                    )}
                                </ul>
                            </div>
                        </div>
                    )}
                </div>
            )}
            
            {excelDiagnostic && (
                <div className="w-full">
                    <button 
                        onClick={() => setShowDiagnostic(!showDiagnostic)}
                        className="text-sm text-yellow-600 hover:text-yellow-800 flex items-center"
                    >
                        {showDiagnostic ? '▼ Hide Excel Diagnostic' : '► Show Excel Diagnostic'}
                    </button>
                    
                    {showDiagnostic && (
                        <div className="mt-2 p-3 bg-yellow-50 rounded border text-sm">
                            <h4 className="font-semibold mb-2">Excel Diagnostic Results:</h4>
                            <p>File: {excelDiagnostic.file_name}</p>
                            <p>Total sheets: {excelDiagnostic.sheet_count}</p>
                            
                            <div className="mt-2">
                                <h5 className="font-semibold">Sheets:</h5>
                                
                                {excelDiagnostic.sheet_names.map((sheetName, sheetIndex) => {
                                    const sheetData = excelDiagnostic.sheets[sheetName];
                                    return (
                                        <div key={sheetIndex} className="mt-3 p-2 bg-white rounded border">
                                            <h6 className="font-semibold">
                                                {sheetName} 
                                                {sheetName === 'Project Table' && 
                                                    <span className="text-green-600 ml-2">(Project Data)</span>
                                                }
                                                {(sheetName === 'Invoice Data Imported' || sheetName === 'Invoice Data') && 
                                                    <span className="text-green-600 ml-2">(Invoice Data)</span>
                                                }
                                            </h6>
                                            <p>Rows: {sheetData.row_count}, Columns: {sheetData.column_count}</p>
                                            
                                            {sheetData.columns.length > 0 && (
                                                <div className="mt-2 overflow-x-auto">
                                                    <h6 className="font-medium">Columns:</h6>
                                                    <table className="min-w-full text-xs border">
                                                        <thead>
                                                            <tr className="bg-gray-100">
                                                                <th className="border p-1">Excel</th>
                                                                <th className="border p-1">Index</th>
                                                                <th className="border p-1">Name</th>
                                                                <th className="border p-1">Type</th>
                                                            </tr>
                                                        </thead>
                                                        <tbody>
                                                            {sheetData.columns.map((col, colIndex) => (
                                                                <tr key={colIndex} className={
                                                                    (sheetName === 'Invoice Data Imported' || sheetName === 'Invoice Data') && 
                                                                    (colIndex === 0 || colIndex === 1 || colIndex === 2 || colIndex === 14) ?
                                                                    'bg-yellow-100' : ''
                                                                }>
                                                                    <td className="border p-1">{col.excel_column}</td>
                                                                    <td className="border p-1">{col.index}</td>
                                                                    <td className="border p-1">{col.name}</td>
                                                                    <td className="border p-1">{col.data_type}</td>
                                                                </tr>
                                                            ))}
                                                        </tbody>
                                                    </table>
                                                </div>
                                            )}
                                            
                                            {sheetData.sample_rows.length > 0 && (
                                                <div className="mt-2">
                                                    <h6 className="font-medium">Sample Data:</h6>
                                                    <div className="overflow-x-auto max-h-60">
                                                        <table className="min-w-full text-xs border">
                                                            <thead>
                                                                <tr className="bg-gray-100">
                                                                    <th className="border p-1">Row</th>
                                                                    {sheetData.columns.map((col, colIndex) => (
                                                                        <th key={colIndex} className="border p-1">
                                                                            {col.name} ({col.excel_column})
                                                                        </th>
                                                                    ))}
                                                                </tr>
                                                            </thead>
                                                            <tbody>
                                                                {sheetData.sample_rows.map((row, rowIndex) => (
                                                                    <tr key={rowIndex}>
                                                                        <td className="border p-1 font-medium">{rowIndex + 1}</td>
                                                                        {sheetData.columns.map((col, colIndex) => (
                                                                            <td key={colIndex} className="border p-1 truncate max-w-xs">
                                                                                {row[col.name] !== undefined ? 
                                                                                 String(row[col.name]) : ''}
                                                                            </td>
                                                                        ))}
                                                                    </tr>
                                                                ))}
                                                            </tbody>
                                                        </table>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}
                </div>
            )}
            
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