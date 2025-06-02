import axios from 'axios';

// Use environment variable for API base URL, fallback to production backend for universal access
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'https://ta-project-data-analyst-backend.onrender.com';

export const fetchProjectData = async () => {
    try {
        const response = await axios.get(`${API_BASE_URL}/api/get-data`);
        return response.data;
    } catch (error) {
        console.error('Error fetching project data:', error);
        if (error.response) {
            // The request was made and the server responded with a status code
            // that falls out of the range of 2xx
            throw new Error(error.response.data.message || 'Server error occurred');
        } else if (error.request) {
            // The request was made but no response was received
            throw new Error('No response from server. Please check if the backend is running.');
        } else {
            // Something happened in setting up the request that triggered an Error
            throw new Error('Error setting up the request');
        }
    }
};

export const uploadAndGetData = async (file) => {
    try {
        const formData = new FormData();
        formData.append('file', file);

        console.log("MAKING API REQUEST: Uploading Excel file to backend");

        const response = await fetch(`${API_BASE_URL}/api/data`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to upload and process file');
        }

        const responseData = await response.json();
        console.log("API RESPONSE RECEIVED: Raw response:", JSON.stringify(responseData).substring(0, 500) + "...");
        
        // Check if the response has the expected structure
        if (responseData.projects && Array.isArray(responseData.projects)) {
            console.log(`Received ${responseData.projects.length} projects and ${responseData.invoices?.length || 0} invoices`);
            
            // Debug: Verify project uniqueness
            if (responseData.projects.length > 0) {
                const projectCodes = responseData.projects.map(p => p['Project Code']);
                const uniqueCodes = new Set(projectCodes);
                console.log(`Projects received: ${responseData.projects.length}, Unique project codes: ${uniqueCodes.size}`);
                
                if (uniqueCodes.size !== responseData.projects.length) {
                    console.warn("WARNING: Received duplicated projects from backend!");
                    
                    // Find the duplicates
                    const duplicates = projectCodes.filter((code, index) => 
                        projectCodes.indexOf(code) !== index
                    );
                    console.warn("Duplicate project codes:", [...new Set(duplicates)]);
                }
            }
            
            return responseData;
        } else if (Array.isArray(responseData)) {
            // Handle legacy API response format (array of projects only)
            console.log(`Received ${responseData.length} projects in legacy format`);
            
            // Debug: Verify project uniqueness in legacy format
            if (responseData.length > 0) {
                const projectCodes = responseData.map(p => p['Project Code']);
                const uniqueCodes = new Set(projectCodes);
                console.log(`Projects received: ${responseData.length}, Unique project codes: ${uniqueCodes.size}`);
                
                if (uniqueCodes.size !== responseData.length) {
                    console.warn("WARNING: Received duplicated projects from backend!");
                }
            }
            
            return {
                projects: responseData,
                invoices: []
            };
        } else {
            console.error('Unexpected API response format:', responseData);
            throw new Error('Unexpected data format received from server');
        }
    } catch (error) {
        console.error('Error uploading file:', error);
        throw error;
    }
};

export const getGPTAnalysis = async (data) => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ data })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to get GPT analysis');
        }

        const result = await response.text();
        return result;
    } catch (error) {
        console.error('Error getting GPT analysis:', error);
        throw error;
    }
}; 