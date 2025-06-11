// PRISMY API Client
const PRISMY_API_URL = 'http://localhost:8000';

class PrismyAPIClient {
    constructor(apiUrl = PRISMY_API_URL) {
        this.apiUrl = apiUrl;
    }

    async translateFile(file, config) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('config', JSON.stringify(config));

        try {
            const response = await fetch(`${this.apiUrl}/translate/file`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || `API Error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
    }

    async checkHealth() {
        try {
            const response = await fetch(`${this.apiUrl}/health`);
            return await response.json();
        } catch (error) {
            console.error('Health check failed:', error);
            return { status: 'error', message: error.message };
        }
    }
}
cat > frontend/js/api-client.js << 'EOF'
// PRISMY API Client
const PRISMY_API_URL = 'http://localhost:8000';

class PrismyAPIClient {
    constructor(apiUrl = PRISMY_API_URL) {
        this.apiUrl = apiUrl;
    }

    async translateFile(file, config) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('config', JSON.stringify(config));

        try {
            const response = await fetch(`${this.apiUrl}/translate/file`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || `API Error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
    }

    async checkHealth() {
        try {
            const response = await fetch(`${this.apiUrl}/health`);
            return await response.json();
        } catch (error) {
            console.error('Health check failed:', error);
            return { status: 'error', message: error.message };
        }
    }
}

// Initialize global API client
const prismyAPI = new PrismyAPIClient();
