/**
 * GHC Digital Twin JavaScript Interface
 * Provides functions to interact with the Digital Twin API
 */

class GHCDigitalTwin {
    constructor() {
        // Get API URL from environment or use default
        this.apiUrl = this.getApiUrl();
        this.healthStatus = 'unknown';
        
        // Initialize health check
        this.checkHealth();
        
        console.log(`?? GHC Digital Twin initialized with API: ${this.apiUrl}`);
    }
    
    getApiUrl() {
        // Try to get from various sources
        if (typeof window !== 'undefined') {
            // From global window object (set by HTML)
            if (window.TWIN_API_URL) return window.TWIN_API_URL;
            
            // From meta tag
            const metaTag = document.querySelector('meta[name="twin-api-url"]');
            if (metaTag) return metaTag.getAttribute('content');
            
            // From data attribute on script tag
            const scriptTag = document.querySelector('script[data-twin-api-url]');
            if (scriptTag) return scriptTag.getAttribute('data-twin-api-url');
        }
        
        // Default fallback (for development)
        return 'https://digitalroots-bf3899aefd705f6789c2466e0c9b974d.us.langgraph.app';
    }
    
    async checkHealth() {
        try {
            const response = await fetch(`${this.apiUrl}/health`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.healthStatus = 'healthy';
                console.log('? Digital Twin API is healthy:', data);
            } else {
                this.healthStatus = 'error';
                console.warn('?? Digital Twin API health check failed:', response.status);
            }
        } catch (error) {
            this.healthStatus = 'error';
            console.error('? Digital Twin API health check error:', error);
        }
        
        // Update health indicator if it exists
        this.updateHealthIndicator();
    }
    
    updateHealthIndicator() {
        const healthElement = document.getElementById('twin-health-status');
        if (healthElement) {
            const isHealthy = this.healthStatus === 'healthy';
            healthElement.textContent = isHealthy ? '? API Online' : '? API Offline';
            healthElement.className = `health-indicator ${isHealthy ? 'healthy' : 'error'}`;
            healthElement.title = `Digital Twin API is ${this.healthStatus}`;
        }
    }
    
    async query(question, sourceType = 'public') {
        if (!question || typeof question !== 'string') {
            throw new Error('Question must be a non-empty string');
        }
        
        console.log(`?? Asking Digital Twin: "${question}"`);
        
        try {
            const response = await fetch(`${this.apiUrl}/api/twin/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    question: question.trim(),
                    source_type: sourceType
                })
            });
            
            if (!response.ok) {
                if (response.status === 500) {
                    const errorData = await response.json().catch(() => ({ detail: 'Internal server error' }));
                    throw new Error(`Server error: ${errorData.detail || 'Unknown error'}`);
                } else {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
            }
            
            const data = await response.json();
            console.log('?? Digital Twin response:', data);
            
            return {
                success: true,
                answer: data.final_answer || data.answer || 'No answer provided',
                status: data.status || 'success',
                question: question
            };
            
        } catch (error) {
            console.error('? Query error:', error);
            
            return {
                success: false,
                answer: `Sorry, I encountered an error: ${error.message}`,
                status: 'error',
                question: question,
                error: error.message
            };
        }
    }
    
    // Convenience method for simple queries
    async ask(question) {
        return await this.query(question);
    }
    
    // Method to display results in a DOM element
    displayAnswer(result, targetElementId = 'twin-answer') {
        const targetElement = document.getElementById(targetElementId);
        if (!targetElement) {
            console.warn(`Element with ID '${targetElementId}' not found`);
            return;
        }
        
        targetElement.innerHTML = `
            <div class="twin-response ${result.success ? 'success' : 'error'}">
                <div class="question">
                    <strong>Question:</strong> ${this.escapeHtml(result.question)}
                </div>
                <div class="answer">
                    <strong>Answer:</strong> ${this.escapeHtml(result.answer)}
                </div>
                ${result.error ? `<div class="error">Error: ${this.escapeHtml(result.error)}</div>` : ''}
                <div class="status">Status: ${result.status}</div>
            </div>
        `;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Auto-initialize if in browser environment
let twinAPI = null;
if (typeof window !== 'undefined') {
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            twinAPI = new GHCDigitalTwin();
            window.twinAPI = twinAPI;
        });
    } else {
        twinAPI = new GHCDigitalTwin();
        window.twinAPI = twinAPI;
    }
}

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GHCDigitalTwin;
}

// AMD support
if (typeof define === 'function' && define.amd) {
    define([], function() {
        return GHCDigitalTwin;
    });
}

/**
 * Utility functions for easy integration
 */

// Simple query function for inline use
async function askDigitalTwin(question, targetElementId) {
    if (!window.twinAPI) {
        console.error('Digital Twin API not initialized');
        return;
    }
    
    const result = await window.twinAPI.query(question);
    
    if (targetElementId) {
        window.twinAPI.displayAnswer(result, targetElementId);
    }
    
    return result;
}

// Health check function
async function checkTwinHealth() {
    if (!window.twinAPI) {
        console.error('Digital Twin API not initialized');
        return false;
    }
    
    await window.twinAPI.checkHealth();
    return window.twinAPI.healthStatus === 'healthy';
}

// Make functions globally available
if (typeof window !== 'undefined') {
    window.askDigitalTwin = askDigitalTwin;
    window.checkTwinHealth = checkTwinHealth;
}