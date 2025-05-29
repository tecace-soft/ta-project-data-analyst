/**
 * Chat API service for data assistant
 */
import axios from 'axios';

const WEBHOOK_URL = 'https://gdkim.app.n8n.cloud/webhook/67cb173e-b768-43f2-99cc-45aaf49fc108';

/**
 * Send a chat message to the webhook endpoint
 * @param {string} message - The user's message
 * @param {Array} projectData - The project data array
 * @param {Array} invoiceData - The invoice data array
 * @param {number} sessionId - The current session ID
 * @returns {Promise<Object>} - The response from the API
 */
export const sendChatMessage = async (message, projectData, invoiceData, sessionId) => {
    try {
        console.log(`Sending message to webhook: "${message}" with sessionId: ${sessionId}`);
        
        const requestData = {
            request: message,
            projectData: projectData || [],
            invoiceData: invoiceData || [],
            sessionId: sessionId
        };
        
        // Log the request data (for debugging)
        console.log('Request payload:', JSON.stringify(requestData, null, 2));
        
        // Send the POST request to the webhook endpoint
        const response = await axios.post(WEBHOOK_URL, requestData);
        
        // Return the response from the API
        return {
            response: response.data
        };
    } catch (error) {
        console.error('Error sending message to webhook:', error);
        
        // Return a user-friendly error message
        return {
            response: `Error: ${error.message || 'Failed to get a response from the server'}`
        };
    }
}; 