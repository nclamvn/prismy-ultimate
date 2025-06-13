const fs = require('fs');

const newApiClient = `const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class ApiClient {
  private token: string | null = null;

  setToken(token: string) {
    this.token = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', token);
    }
  }

  getToken(): string | null {
    if (typeof window !== 'undefined' && !this.token) {
      this.token = localStorage.getItem('auth_token');
    }
    return this.token;
  }

  async request(endpoint: string, options: RequestInit = {}) {
    const url = \`\${API_URL}\${endpoint}\`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    const token = this.getToken();
    if (token) {
      headers['Authorization'] = \`Bearer \${token}\`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      throw new Error(\`API Error: \${response.statusText}\`);
    }

    return response.json();
  }

  // Auth methods (keep existing for compatibility)
  async login(username: string, password: string) {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await fetch(\`\${API_URL}/api/auth/token\`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    });

    const data = await response.json();
    if (data.access_token) {
      this.setToken(data.access_token);
    }
    return data;
  }

  // UPDATED: Translation methods for PRISMY-ULTIMATE
  async translateText(text: string, sourceLang: string = 'auto', targetLang: string = 'vi', tier: string = 'basic') {
    // For text translation, create a blob and use PDF endpoint
    const blob = new Blob([text], { type: 'text/plain' });
    const file = new File([blob], 'text.txt', { type: 'text/plain' });
    return this.translatePDF(file, targetLang, tier);
  }

  async translatePDF(file: File, targetLanguage: string = 'vi', tier: string = 'standard') {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('target_language', targetLanguage);
    formData.append('tier', tier);

    // Use PRISMY-ULTIMATE endpoint
    const response = await fetch(\`\${API_URL}/api/v2/translate/pdf/async\`, {
      method: 'POST',
      body: formData, // No Content-Type header for FormData
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Network error' }));
      throw new Error(error.error || \`HTTP \${response.status}\`);
    }

    return response.json();
  }

  // NEW: Job tracking methods for PRISMY-ULTIMATE
  async getJobStatus(jobId: string) {
    const response = await fetch(\`\${API_URL}/api/v2/translate/job/\${jobId}\`);
    
    if (!response.ok) {
      throw new Error(\`Failed to get job status: HTTP \${response.status}\`);
    }

    return response.json();
  }

  async downloadResult(outputPath: string) {
    const response = await fetch(\`\${API_URL}/api/v2/outputs/\${outputPath}/download\`);
    
    if (!response.ok) {
      throw new Error(\`Failed to download: HTTP \${response.status}\`);
    }

    return response;
  }

  // NEW: Health check for PRISMY-ULTIMATE
  async getHealth() {
    const response = await fetch(\`\${API_URL}/health\`);
    return response.json();
  }

  async getTiers() {
    const response = await fetch(\`\${API_URL}/tiers\`);
    return response.json();
  }

  // File methods (keep existing for compatibility)
  async uploadFile(file: File) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(\`\${API_URL}/api/files/upload\`, {
      method: 'POST',
      headers: {
        'Authorization': \`Bearer \${this.getToken()}\`,
      },
      body: formData,
    });

    return response.json();
  }
}

export const apiClient = new ApiClient();`;

fs.writeFileSync('src/lib/api-client.ts', newApiClient);
console.log('✅ API client updated for PRISMY-ULTIMATE');
