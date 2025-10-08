// API Configuration
const API_BASE = '/api';

// SOPHIA service runs on port 8000
// Auto-detect the proper base URL
const getSophiaBase = () => {
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        return 'http://localhost:8000';
    }
    // For Replit and other cloud environments, use same protocol and host but different port
    // In Replit, this will be handled by the proxy
    return `${window.location.protocol}//${window.location.hostname}:8000`;
};

const SOPHIA_BASE = getSophiaBase();

// State
let authToken = null;
let currentUser = null;
let currentThreadId = null;

// Initialize from localStorage
window.onload = function() {
    const savedToken = localStorage.getItem('authToken');
    const savedUser = localStorage.getItem('currentUser');
    
    if (savedToken && savedUser) {
        authToken = savedToken;
        currentUser = JSON.parse(savedUser);
        showAdminPanel();
    }
};

// Helper: Make API request with auth
async function apiRequest(method, endpoint, body = null, useSophiaBase = false) {
    const base = useSophiaBase ? SOPHIA_BASE : API_BASE;
    
    try {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            }
        };

        if (authToken) {
            options.headers['Authorization'] = `Bearer ${authToken}`;
        }

        if (body) {
            options.body = JSON.stringify(body);
        }

        const response = await fetch(base + endpoint, options);
        
        // Handle empty responses (e.g., 204 No Content)
        let data = null;
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            data = await response.json();
        } else if (response.status !== 204) {
            // Try to parse as JSON, but don't fail if it's not
            const text = await response.text();
            try {
                data = JSON.parse(text);
            } catch {
                data = { message: text };
            }
        }

        if (response.ok) {
            return { success: true, data: data || {} };
        } else {
            return { success: false, error: data?.error || data?.message || 'Request failed' };
        }
    } catch (error) {
        return { success: false, error: error.message };
    }
}

// Helper: Show status message
function showStatus(elementId, message, type = 'info') {
    const element = document.getElementById(elementId);
    element.innerHTML = `<div class="status ${type}">${message}</div>`;
}

// Helper: Show response
function showResponse(elementId, data) {
    const element = document.getElementById(elementId);
    element.innerHTML = `<div class="response">${JSON.stringify(data, null, 2)}</div>`;
}

// Toggle Forms
function showLoginForm() {
    document.getElementById('registerForm').classList.add('hidden');
    document.getElementById('loginForm').classList.remove('hidden');
}

function showRegisterForm() {
    document.getElementById('loginForm').classList.add('hidden');
    document.getElementById('registerForm').classList.remove('hidden');
}

// Register
async function register() {
    const company_name = document.getElementById('registerCompanyName').value;
    const username = document.getElementById('registerUsername').value;
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;

    if (!company_name || !username || !email || !password) {
        showStatus('registerStatus', 'All fields are required', 'error');
        return;
    }

    const result = await apiRequest('POST', '/auth/register', { 
        company_name, 
        username, 
        email, 
        password 
    });

    if (result.success) {
        authToken = result.data.access_token;
        currentUser = result.data.user;
        
        // Save to localStorage
        localStorage.setItem('authToken', authToken);
        localStorage.setItem('currentUser', JSON.stringify(currentUser));
        
        showStatus('registerStatus', 'Registration successful!', 'success');
        setTimeout(showAdminPanel, 500);
    } else {
        showStatus('registerStatus', `Registration failed: ${result.error}`, 'error');
    }
}

// Login
async function login() {
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;

    if (!username || !password) {
        showStatus('loginStatus', 'Please enter username and password', 'error');
        return;
    }

    const result = await apiRequest('POST', '/auth/login', { username, password });

    if (result.success) {
        authToken = result.data.access_token;
        currentUser = result.data.user;
        
        // Save to localStorage
        localStorage.setItem('authToken', authToken);
        localStorage.setItem('currentUser', JSON.stringify(currentUser));
        
        showStatus('loginStatus', 'Login successful!', 'success');
        setTimeout(showAdminPanel, 500);
    } else {
        showStatus('loginStatus', `Login failed: ${result.error}`, 'error');
    }
}

// Logout
function logout() {
    authToken = null;
    currentUser = null;
    currentThreadId = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    
    // Clear chat history
    document.getElementById('chatHistory').innerHTML = '';
    document.getElementById('threadId').value = '';
    
    // Show register form and hide admin panel
    document.getElementById('authSection').classList.remove('hidden');
    document.getElementById('adminPanel').classList.add('hidden');
    showRegisterForm();
    
    // Clear forms
    document.getElementById('registerCompanyName').value = '';
    document.getElementById('registerUsername').value = '';
    document.getElementById('registerEmail').value = '';
    document.getElementById('registerPassword').value = '';
    document.getElementById('loginUsername').value = '';
    document.getElementById('loginPassword').value = '';
}

// Show Admin Panel
function showAdminPanel() {
    document.getElementById('authSection').classList.add('hidden');
    document.getElementById('adminPanel').classList.remove('hidden');
    
    document.getElementById('userDisplay').textContent = currentUser.username;
    document.getElementById('companyDisplay').textContent = currentUser.company?.name || `ID: ${currentUser.company_id}`;
}

// Show/Hide Create Form
function showCreateForm() {
    document.getElementById('createInstanceForm').classList.remove('hidden');
}

function hideCreateForm() {
    document.getElementById('createInstanceForm').classList.add('hidden');
}

// Load Agent Instances
async function loadAgentInstances() {
    const result = await apiRequest('GET', '/admin/agent-instances');

    if (result.success) {
        showResponse('instancesStatus', result.data);
    } else {
        showStatus('instancesStatus', `Failed to load instances: ${result.error}`, 'error');
    }
}

// Create Agent Instance
async function createAgentInstance() {
    const requestBody = {
        azureOpenaiEndpoint: document.getElementById('azureOpenaiEndpoint').value,
        azureOpenaiKey: document.getElementById('azureOpenaiKey').value,
        azureOpenaiDeployment: document.getElementById('azureOpenaiDeployment').value,
        azureProjectId: document.getElementById('azureProjectId').value,
        azureSearchEndpoint: document.getElementById('azureSearchEndpoint').value,
        azureSearchKey: document.getElementById('azureSearchKey').value,
        azureSpeechEndpoint: document.getElementById('azureSpeechEndpoint').value,
        azureSpeechKey: document.getElementById('azureSpeechKey').value,
        azureSpeechRegion: document.getElementById('azureSpeechRegion').value,
        azureSpeechVoiceName: document.getElementById('azureSpeechVoiceName').value
    };

    // Remove empty fields
    Object.keys(requestBody).forEach(key => {
        if (!requestBody[key]) delete requestBody[key];
    });

    const result = await apiRequest('POST', '/admin/agent-instances', requestBody);

    if (result.success) {
        showStatus('instancesStatus', 
            `Instance created successfully! Access Key: ${result.data.agent_access_key}`, 
            'success'
        );
        
        // Also show full response
        showResponse('instancesStatus', result.data);
        
        // Clear form
        document.getElementById('azureOpenaiEndpoint').value = '';
        document.getElementById('azureOpenaiKey').value = '';
        document.getElementById('azureOpenaiDeployment').value = '';
        document.getElementById('azureProjectId').value = '';
        document.getElementById('azureSearchEndpoint').value = '';
        document.getElementById('azureSearchKey').value = '';
        document.getElementById('azureSpeechEndpoint').value = '';
        document.getElementById('azureSpeechKey').value = '';
        document.getElementById('azureSpeechRegion').value = '';
        document.getElementById('azureSpeechVoiceName').value = '';
        
        hideCreateForm();
    } else {
        showStatus('instancesStatus', `Failed to create instance: ${result.error}`, 'error');
    }
}

// Update Credentials
async function updateCredentials() {
    const instanceId = document.getElementById('updateInstanceId').value;
    
    if (!instanceId) {
        showStatus('updateStatus', 'Please enter an Instance ID', 'error');
        return;
    }

    const requestBody = {
        azureOpenaiEndpoint: document.getElementById('updateAzureOpenaiEndpoint').value,
        azureOpenaiKey: document.getElementById('updateAzureOpenaiKey').value,
        azureOpenaiDeployment: document.getElementById('updateAzureOpenaiDeployment').value,
        azureSearchEndpoint: document.getElementById('updateAzureSearchEndpoint').value,
        azureSearchKey: document.getElementById('updateAzureSearchKey').value
    };

    // Remove empty fields
    Object.keys(requestBody).forEach(key => {
        if (!requestBody[key]) delete requestBody[key];
    });

    const result = await apiRequest('PUT', `/admin/agent-instances/${instanceId}`, requestBody);

    if (result.success) {
        showStatus('updateStatus', 'Credentials updated successfully!', 'success');
        showResponse('updateStatus', result.data);
    } else {
        showStatus('updateStatus', `Failed to update credentials: ${result.error}`, 'error');
    }
}

// Test Configuration
async function testConfiguration() {
    const companyId = document.getElementById('testCompanyId').value;
    const agentAccessKey = document.getElementById('testAccessKey').value;

    if (!companyId || !agentAccessKey) {
        showStatus('testStatus', 'Please enter Company ID and Agent Access Key', 'error');
        return;
    }

    const requestBody = {
        companyId: parseInt(companyId),
        agentAccessKey: agentAccessKey
    };

    const result = await apiRequest('POST', '/config/test', requestBody, true);

    if (result.success) {
        const status = result.data.status === 'ready' ? 'success' : 'info';
        showStatus('testStatus', result.data.message, status);
        showResponse('testStatus', result.data);
    } else {
        showStatus('testStatus', `Test failed: ${result.error}`, 'error');
    }
}

// Send Message to SOPHIA
async function sendMessage() {
    const companyId = document.getElementById('chatCompanyId').value;
    const agentAccessKey = document.getElementById('chatAccessKey').value;
    const message = document.getElementById('chatMessage').value;
    let threadId = document.getElementById('threadId').value;

    if (!companyId || !agentAccessKey || !message) {
        showStatus('chatStatus', 'Please enter Company ID, Access Key, and Message', 'error');
        return;
    }

    // Check if user is logged in to get userId
    if (!currentUser || !currentUser.id) {
        showStatus('chatStatus', 'Please login first to use the chat', 'error');
        return;
    }

    // Use current thread ID if available and no manual input
    if (!threadId && currentThreadId) {
        threadId = currentThreadId;
    }

    const requestBody = {
        companyId: parseInt(companyId),
        userId: currentUser.id,
        agentAccessKey: agentAccessKey,
        message: message,
        threadId: threadId || undefined
    };

    // Show user message
    addChatMessage(message, 'user');
    
    // Clear message input
    document.getElementById('chatMessage').value = '';

    showStatus('chatStatus', 'Sending message to SOPHIA...', 'info');

    const result = await apiRequest('POST', '/chat', requestBody, true);

    if (result.success) {
        // Update thread ID for next message
        if (result.data.threadId) {
            currentThreadId = result.data.threadId;
            document.getElementById('threadId').value = currentThreadId;
        }

        // Show SOPHIA response
        addChatMessage(result.data.response, 'sophia');
        
        showStatus('chatStatus', 'Message sent successfully!', 'success');
    } else {
        showStatus('chatStatus', `Failed to send message: ${result.error}`, 'error');
    }
}

// Add chat message to history
function addChatMessage(message, type) {
    const chatHistory = document.getElementById('chatHistory');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${type}`;
    messageDiv.innerHTML = `<strong>${type === 'user' ? 'You' : 'SOPHIA'}:</strong> ${message}`;
    chatHistory.appendChild(messageDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}
