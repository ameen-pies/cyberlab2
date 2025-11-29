// API Configuration

const API_CONFIG = {
    BASE_URL: 'http://localhost:8000',
    ENDPOINTS: {
        // Auth endpoints
        REGISTER: '/auth/register',
        LOGIN: '/auth/login',
        MFA_SEND: '/auth/mfa/send',
        MFA_VERIFY: '/auth/mfa/verify',
        ME: '/auth/me',
        
        // Encryption endpoints
        ENCRYPT_TRANSIT: '/simulations/encrypt/in-transit',
        DECRYPT_TRANSIT: '/simulations/decrypt/in-transit',
        ENCRYPT_REST: '/simulations/encrypt/at-rest',
        DECRYPT_REST: '/simulations/decrypt/at-rest',
        LIFECYCLE: '/simulations/encrypt/lifecycle',
        ENCRYPT_FILE_TRANSIT: '/simulations/encrypt/file/in-transit',
        DECRYPT_FILE_TRANSIT: '/simulations/decrypt/file/in-transit',  // ✅ Added missing endpoint
        ENCRYPT_FILE_REST: '/simulations/encrypt/file/at-rest',
        DECRYPT_FILE_REST: '/simulations/decrypt/file/at-rest',  // ✅ Added missing endpoint
        FILE_LIFECYCLE: '/simulations/encrypt/file/lifecycle',  // ✅ Fixed endpoint name
        
        // KeyVault endpoints
        KEYVAULT_GENERATE_KEY: '/keyvault/keys/generate',
        KEYVAULT_LIST_KEYS: '/keyvault/keys',
        KEYVAULT_GET_KEY: '/keyvault/keys/',
        KEYVAULT_ROTATE_KEY: '/keyvault/keys/',
        KEYVAULT_DELETE_KEY: '/keyvault/keys/',
        KEYVAULT_GENERATE_CERT: '/keyvault/certificates/generate',
        KEYVAULT_LIST_CERTS: '/keyvault/certificates',
        KEYVAULT_VALIDATE_CERT: '/keyvault/certificates/',
        KEYVAULT_STATS: '/keyvault/statistics',
        
        // Password Checker endpoints
        PASSWORD_ANALYZE: '/password-checker/analyze',
        PASSWORD_CHECK_BREACH: '/password-checker/check-breach',
        PASSWORD_SAVE_POLICY: '/password-checker/policies',
        PASSWORD_GET_POLICIES: '/password-checker/policies',
        PASSWORD_DEFAULT_POLICY: '/password-checker/policies/default',
        PASSWORD_ANALYTICS: '/password-checker/analytics',
        PASSWORD_BATCH: '/password-checker/batch-analyze',
        
        // Secret Scanner endpoints
        SCANNER_SCAN_TEXT: '/secret-scanner/scan/text',
        SCANNER_SCAN_FILE: '/secret-scanner/scan/file',
        SCANNER_SCAN_GITHUB: '/secret-scanner/scan/github-url',
        SCANNER_REDACT: '/secret-scanner/redact',
        SCANNER_HISTORY: '/secret-scanner/history',
        SCANNER_PATTERNS: '/secret-scanner/patterns',
        SCANNER_STATS: '/secret-scanner/statistics'
    }
};

// Utility Functions
function showError(elementId, message) {
    const errorEl = document.getElementById(elementId);
    if (errorEl) {
        errorEl.textContent = message;
        errorEl.classList.add('show');
        setTimeout(() => errorEl.classList.remove('show'), 5000);
    }
}

function showSuccess(elementId, message) {
    const successEl = document.getElementById(elementId);
    if (successEl) {
        successEl.textContent = message;
        successEl.classList.add('show');
        setTimeout(() => successEl.classList.remove('show'), 5000);
    }
}

function setLoading(buttonElement, isLoading) {
    const btnText = buttonElement.querySelector('.btn-text');
    const btnLoader = buttonElement.querySelector('.btn-loader');
    
    if (isLoading) {
        if (btnText) btnText.style.display = 'none';
        if (btnLoader) btnLoader.style.display = 'block';
        buttonElement.disabled = true;
    } else {
        if (btnText) btnText.style.display = 'block';
        if (btnLoader) btnLoader.style.display = 'none';
        buttonElement.disabled = false;
    }
}

// Local Storage Helpers
const Storage = {
    setToken: (token) => localStorage.setItem('auth_token', token),
    getToken: () => localStorage.getItem('auth_token'),
    removeToken: () => localStorage.removeItem('auth_token'),
    setUser: (user) => localStorage.setItem('user_data', JSON.stringify(user)),
    getUser: () => {
        const data = localStorage.getItem('user_data');
        return data ? JSON.parse(data) : null;
    },
    removeUser: () => localStorage.removeItem('user_data'),
    clear: () => localStorage.clear()
};

// API Request Helper
async function apiRequest(endpoint, options = {}) {
    const url = `${API_CONFIG.BASE_URL}${endpoint}`;
    const token = Storage.getToken();
    
    const defaultHeaders = {};
    
    // ✅ Only set Content-Type for non-FormData requests
    // When sending FormData, browser automatically sets Content-Type with boundary
    if (!(options.body instanceof FormData)) {
        defaultHeaders['Content-Type'] = 'application/json';
    }
    
    if (token && !options.skipAuth) {
        defaultHeaders['Authorization'] = `Bearer ${token}`;
    }
    
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                ...defaultHeaders,
                ...options.headers
            }
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            // ✅ Better error handling - extract the error message properly
            const errorMessage = data.detail || data.error || data.message || 'Request failed';
            throw new Error(errorMessage);
        }
        
        return data;
    } catch (error) {
        console.error('API Request Error:', error);
        // ✅ Re-throw with proper error message
        throw error;
    }
}