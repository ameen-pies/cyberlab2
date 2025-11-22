
// Check authentication
if (!Storage.getToken()) {
    window.location.href = 'index.html';
}

let currentUserPermissions = [];
let currentUserRole = 'normal';

// Initialize dashboard
document.addEventListener('DOMContentLoaded', async () => {
    // ✅ Load permissions FIRST, then apply RBAC
    await loadUserPermissions();
    loadUserInfo();
    initializeEncryptionCount();
    applyRBAC();
    
    // ✅ Handle hash navigation for sections (e.g., #settings, #encryption)
    const hash = window.location.hash.substring(1); // Remove the #
    if (hash) {
        showSection(hash);
    }
});

// Load user permissions from API
async function loadUserPermissions() {
    try {
        const response = await apiRequest('/users/permissions', {
            method: 'GET'
        });
        
        currentUserPermissions = response.permissions || [];
        currentUserRole = response.role || 'normal';
        
        console.log('✅ User Permissions:', currentUserPermissions);
        console.log('✅ User Role:', currentUserRole);
        
        // Update stored user data
        const existingUser = Storage.getUser() || {};
        Storage.setUser({
            ...existingUser,
            email: response.email,
            full_name: response.full_name || existingUser.full_name,
            role: response.role
        });
        
    } catch (error) {
        console.error('❌ Failed to load permissions:', error);
        const storedUser = Storage.getUser();
        if (storedUser && storedUser.role) {
            currentUserRole = storedUser.role;
        }
    }
}

// Apply RBAC to UI
function applyRBAC() {
    const role = currentUserRole;
    
    console.log('🔒 Applying RBAC for role:', role);
    
    // Role badge with emoji
    const roleBadge = getRoleBadge(role);
    document.getElementById('userRoleBadge').innerHTML = roleBadge;
    document.getElementById('userRoleHeader').textContent = formatRole(role);
    document.getElementById('overviewRole').textContent = formatRole(role);
    document.getElementById('settingsRole').value = formatRole(role);
    
    // Show/hide admin features
    const isAdmin = (role === 'admin' || role === 'co_admin');
    
    if (isAdmin) {
        console.log('✅ Admin access granted');
        document.getElementById('navAdmin').style.display = 'flex';
        document.getElementById('serviceAdmin').style.display = 'block';
    } else {
        console.log('❌ Not admin - hiding admin panel');
        document.getElementById('navAdmin').style.display = 'none';
        document.getElementById('serviceAdmin').style.display = 'none';
    }
    
    // Update header subtitle with emoji
    const subtitles = {
        'admin': '👑 Administrator Dashboard - Full System Access',
        'co_admin': '🛡️ Co-Administrator - User Management Access',
        'normal': 'Manage your security simulations',
        'limited': '⚠️ Limited Access Account'
    };
    document.getElementById('headerSubtitle').textContent = subtitles[role] || subtitles.normal;
}

// Helper functions
function hasPermission(permission) {
    return currentUserPermissions.includes(permission);
}

function formatRole(role) {
    const roles = {
        'admin': 'Administrator',
        'co_admin': 'Co-Administrator',
        'normal': 'Normal User',
        'limited': 'Limited Access'
    };
    return roles[role] || role;
}

function getRoleBadge(role) {
    const badges = {
        'admin': '<span class="status-badge" style="background: #fee2e2; color: #dc2626; width: 100%;">👑 Admin</span>',
        'co_admin': '<span class="status-badge" style="background: #dbeafe; color: #2563eb; width: 100%;">🛡️ Co-Admin</span>',
        'normal': '<span class="status-badge" style="background: #dcfce7; color: #16a34a; width: 100%;">✓ Normal</span>',
        'limited': '<span class="status-badge" style="background: #fef3c7; color: #d97706; width: 100%;">⚠️ Limited</span>'
    };
    return badges[role] || badges.normal;
}

// Load user information
function loadUserInfo() {
    const user = Storage.getUser();
    if (user && user.email) {
        const name = user.full_name || user.email.split('@')[0];
        const initials = name.charAt(0).toUpperCase();
        
        document.getElementById('userName').textContent = name;
        document.getElementById('userEmailHeader').textContent = user.email;
        document.getElementById('userAvatar').textContent = initials;
        
        // Settings page
        document.getElementById('settingsName').value = name;
        document.getElementById('settingsEmail').value = user.email;
        
        displayUserPermissions();
    }
}

// Display user permissions
async function displayUserPermissions() {
    const container = document.getElementById('userPermissions');
    
    if (currentUserPermissions.length === 0) {
        container.innerHTML = '<p style="color: #6b7280;">No permissions assigned</p>';
        return;
    }
    
    // Add emojis to permissions
    const permissionEmojis = {
        'encrypt_text': '🔐',
        'encrypt_file': '📁',
        'decrypt_text': '🔓',
        'decrypt_file': '📂',
        'keyvault_generate_keys': '🔑',
        'keyvault_view_keys': '👁️',
        'keyvault_download_keys': '⬇️',
        'password_check': '🔍',
        'scanner_text': '📝',
        'view_users': '👀',
        'create_users': '➕',
        'manage_permissions': '🔐'
    };
    
    container.innerHTML = currentUserPermissions.map(perm => {
        const emoji = permissionEmojis[perm] || '✓';
        const formatted = perm.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        return `<span class="status-badge" style="background: #e0e7ff; color: #4f46e5;">${emoji} ${formatted}</span>`;
    }).join('');
}

// Initialize encryption counter
function initializeEncryptionCount() {
    const count = localStorage.getItem('encryption_count') || '0';
    document.getElementById('encryptionCount').textContent = count;
}

// Increment encryption counter
function incrementEncryptionCount() {
    let count = parseInt(localStorage.getItem('encryption_count') || '0');
    count++;
    localStorage.setItem('encryption_count', count.toString());
    document.getElementById('encryptionCount').textContent = count;
}

// Show section
function showSection(sectionName) {
    console.log('📄 Showing section:', sectionName);
    
    // Check permissions for admin section
    if (sectionName === 'admin') {
        if (currentUserRole !== 'admin' && currentUserRole !== 'co_admin') {
            alert('❌ You do not have permission to access User Management');
            return;
        }
        // Redirect to dedicated admin panel
        window.location.href = 'admin.html';
        return;
    }
    
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Remove active from nav items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Show selected section
    const sectionElement = document.getElementById(`${sectionName}Section`);
    if (sectionElement) {
        sectionElement.classList.add('active');
    }
    
    // Set active nav item based on section
    const navMap = {
        'overview': document.querySelectorAll('.nav-item')[0],
        'encryption': document.getElementById('navEncryption'),
        'settings': document.querySelectorAll('.nav-item')[document.querySelectorAll('.nav-item').length - 1]
    };
    
    if (navMap[sectionName]) {
        navMap[sectionName].classList.add('active');
    }
    
    // Also handle event-based clicks
    if (event && event.target && event.target.closest('.nav-item')) {
        event.target.closest('.nav-item').classList.add('active');
    }
}

// Switch encryption tabs
function switchEncryptionTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    document.getElementById(`${tabName}Tab`).classList.add('active');
    
    if (event && event.target) {
        event.target.classList.add('active');
    }
}

// Handle logout
function handleLogout() {
    if (confirm('🚪 Are you sure you want to logout?')) {
        Storage.clear();
        window.location.href = 'index.html';
    }
}

// ============= ENCRYPTION FUNCTIONS =============

// In Transit - Encrypt Text
async function handleEncryptInTransit(event) {
    event.preventDefault();
    
    const data = document.getElementById('transitData').value;
    const password = document.getElementById('transitPassword').value;
    const recipientEmail = document.getElementById('transitEmail').value;
    const button = event.target.querySelector('button[type="submit"]');
    
    setLoading(button, true);
    
    try {
        const response = await apiRequest(API_CONFIG.ENDPOINTS.ENCRYPT_TRANSIT, {
            method: 'POST',
            body: JSON.stringify({
                data: data,
                password: password,
                recipient_email: recipientEmail || null
            })
        });
        
        if (response.success) {
            displayEncryptionResult('transitResult', response);
            incrementEncryptionCount();
            
            if (recipientEmail) {
                alert('✅ Data encrypted and sent to ' + recipientEmail);
            }
        }
    } catch (error) {
        alert('❌ Encryption failed: ' + error.message);
    } finally {
        setLoading(button, false);
    }
}

// In Transit - Encrypt File
async function handleEncryptFileInTransit(event) {
    event.preventDefault();
    
    const fileInput = document.getElementById('fileInTransit');
    const file = fileInput.files[0];
    const password = document.getElementById('fileTransitPassword').value;
    const recipientEmail = document.getElementById('fileTransitEmail').value;
    const button = event.target.querySelector('button[type="submit"]');
    
    if (!file) {
        alert('❌ Please select a file');
        return;
    }
    
    setLoading(button, true);
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('password', password);
        if (recipientEmail) {
            formData.append('recipient_email', recipientEmail);
        }
        
        const response = await apiRequest(API_CONFIG.ENDPOINTS.ENCRYPT_FILE_TRANSIT, {
            method: 'POST',
            body: formData
        });
        
        if (response.success) {
            displayFileEncryptionResult('fileTransitResult', response);
            incrementEncryptionCount();
            
            if (recipientEmail) {
                alert('✅ File encrypted and sent to ' + recipientEmail);
            }
        }
    } catch (error) {
        alert('❌ File encryption failed: ' + error.message);
    } finally {
        setLoading(button, false);
    }
}

// In Transit - Decrypt
async function handleDecryptInTransit(event) {
    event.preventDefault();
    
    const encryptedData = document.getElementById('transitDecryptData').value;
    const password = document.getElementById('transitDecryptPassword').value;
    const salt = document.getElementById('transitDecryptSalt').value;
    const button = event.target.querySelector('button[type="submit"]');
    
    setLoading(button, true);
    
    try {
        const response = await apiRequest(API_CONFIG.ENDPOINTS.DECRYPT_TRANSIT, {
            method: 'POST',
            body: JSON.stringify({
                encrypted_data: encryptedData,
                password: password,
                salt: salt
            })
        });
        
        if (response.success) {
            displayDecryptionResult('transitDecryptResult', response);
        }
    } catch (error) {
        alert('❌ Decryption failed: ' + error.message);
    } finally {
        setLoading(button, false);
    }
}

// In Transit - Decrypt File
async function handleDecryptFileInTransit(event) {
    event.preventDefault();
    
    const fileInput = document.getElementById('fileDecryptInTransit');
    const file = fileInput.files[0];
    const password = document.getElementById('fileTransitDecryptPassword').value;
    const salt = document.getElementById('fileTransitDecryptSalt').value;
    const button = event.target.querySelector('button[type="submit"]');
    
    if (!file) {
        alert('❌ Please select a file');
        return;
    }
    
    setLoading(button, true);
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('password', password);
        formData.append('salt', salt);
        
        const response = await apiRequest(API_CONFIG.ENDPOINTS.DECRYPT_FILE_TRANSIT, {
            method: 'POST',
            body: formData
        });
        
        if (response.success) {
            displayFileDecryptionResult('fileTransitDecryptResult', response);
        }
    } catch (error) {
        alert('❌ File decryption failed: ' + error.message);
    } finally {
        setLoading(button, false);
    }
}

// At Rest - Encrypt Text
async function handleEncryptAtRest(event) {
    event.preventDefault();
    
    const data = document.getElementById('restData').value;
    const recipientEmail = document.getElementById('restEmail').value;
    const button = event.target.querySelector('button[type="submit"]');
    
    setLoading(button, true);
    
    try {
        const response = await apiRequest(API_CONFIG.ENDPOINTS.ENCRYPT_REST, {
            method: 'POST',
            body: JSON.stringify({
                data: data,
                recipient_email: recipientEmail || null
            })
        });
        
        if (response.success) {
            displayEncryptionResult('restResult', response);
            incrementEncryptionCount();
            
            if (recipientEmail) {
                alert('✅ Data encrypted and sent to ' + recipientEmail);
            }
        }
    } catch (error) {
        alert('❌ Encryption failed: ' + error.message);
    } finally {
        setLoading(button, false);
    }
}

// At Rest - Encrypt File
async function handleEncryptFileAtRest(event) {
    event.preventDefault();
    
    const fileInput = document.getElementById('fileAtRest');
    const file = fileInput.files[0];
    const recipientEmail = document.getElementById('fileRestEmail').value;
    const button = event.target.querySelector('button[type="submit"]');
    
    if (!file) {
        alert('❌ Please select a file');
        return;
    }
    
    setLoading(button, true);
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        if (recipientEmail) {
            formData.append('recipient_email', recipientEmail);
        }
        
        const response = await apiRequest(API_CONFIG.ENDPOINTS.ENCRYPT_FILE_REST, {
            method: 'POST',
            body: formData
        });
        
        if (response.success) {
            displayFileEncryptionResult('fileRestResult', response);
            incrementEncryptionCount();
            
            if (recipientEmail) {
                alert('✅ File encrypted and sent to ' + recipientEmail);
            }
        }
    } catch (error) {
        alert('❌ File encryption failed: ' + error.message);
    } finally {
        setLoading(button, false);
    }
}

// At Rest - Decrypt
async function handleDecryptAtRest(event) {
    event.preventDefault();
    
    const encryptedData = document.getElementById('restDecryptData').value;
    const key = document.getElementById('restDecryptKey').value;
    const button = event.target.querySelector('button[type="submit"]');
    
    setLoading(button, true);
    
    try {
        const response = await apiRequest(API_CONFIG.ENDPOINTS.DECRYPT_REST, {
            method: 'POST',
            body: JSON.stringify({
                encrypted_data: encryptedData,
                key: key
            })
        });
        
        if (response.success) {
            displayDecryptionResult('restDecryptResult', response);
        }
    } catch (error) {
        alert('❌ Decryption failed: ' + error.message);
    } finally {
        setLoading(button, false);
    }
}

// At Rest - Decrypt File
async function handleDecryptFileAtRest(event) {
    event.preventDefault();
    
    const fileInput = document.getElementById('fileDecryptAtRest');
    const file = fileInput.files[0];
    const key = document.getElementById('fileDecryptKey').value;
    const button = event.target.querySelector('button[type="submit"]');
    
    if (!file) {
        alert('❌ Please select a file');
        return;
    }
    
    if (!key) {
        alert('❌ Please enter the encryption key');
        return;
    }
    
    setLoading(button, true);
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('key', key);
        
        const response = await apiRequest(API_CONFIG.ENDPOINTS.DECRYPT_FILE_REST, {
            method: 'POST',
            body: formData
        });
        
        if (response.success) {
            displayFileDecryptionResult('fileDecryptResult', response);
        }
    } catch (error) {
        alert('❌ File decryption failed: ' + error.message);
    } finally {
        setLoading(button, false);
    }
}

// Full Lifecycle Demo
async function handleLifecycleDemo(event) {
    event.preventDefault();
    
    const data = document.getElementById('lifecycleData').value;
    const recipientEmail = document.getElementById('lifecycleEmail').value;
    const button = event.target.querySelector('button[type="submit"]');
    
    setLoading(button, true);
    
    try {
        const response = await apiRequest(API_CONFIG.ENDPOINTS.LIFECYCLE, {
            method: 'POST',
            body: JSON.stringify({
                data: data,
                recipient_email: recipientEmail || null
            })
        });
        
        if (response.success) {
            displayLifecycleResult('lifecycleResult', response);
            incrementEncryptionCount();
            
            if (recipientEmail) {
                alert('✅ Lifecycle demo completed and sent to ' + recipientEmail);
            }
        }
    } catch (error) {
        alert('❌ Lifecycle demo failed: ' + error.message);
    } finally {
        setLoading(button, false);
    }
}

// File Lifecycle Demo
async function handleFileLifecycleDemo(event) {
    event.preventDefault();
    
    const fileInput = document.getElementById('lifecycleFile');
    const file = fileInput.files[0];
    const recipientEmail = document.getElementById('fileLifecycleEmail').value;
    const button = event.target.querySelector('button[type="submit"]');
    
    if (!file) {
        alert('❌ Please select a file');
        return;
    }
    
    setLoading(button, true);
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        if (recipientEmail) {
            formData.append('recipient_email', recipientEmail);
        }
        
        const response = await apiRequest(API_CONFIG.ENDPOINTS.FILE_LIFECYCLE, {
            method: 'POST',
            body: formData
        });
        
        if (response.success) {
            displayFileLifecycleResult('fileLifecycleResult', response);
            incrementEncryptionCount();
            
            if (recipientEmail) {
                alert('✅ File lifecycle demo completed and sent to ' + recipientEmail);
            }
        }
    } catch (error) {
        alert('❌ File lifecycle demo failed: ' + error.message);
    } finally {
        setLoading(button, false);
    }
}

function displayEncryptionResult(containerId, response) {
    const container = document.getElementById(containerId);
    container.style.display = 'block';
    
    let html = '<h4>✅ Encryption Successful</h4>';
    
    if (response.encrypted_data) {
        html += `
            <div class="result-item">
                <label>🔐 Encrypted Data:</label>
                <textarea readonly rows="3">${response.encrypted_data}</textarea>
            </div>
        `;
    }
    
    if (response.salt) {
        html += `
            <div class="result-item">
                <label>🔑 Salt (save this!):</label>
                <input type="text" readonly value="${response.salt}">
            </div>
        `;
    }
    
    if (response.key) {
        html += `
            <div class="result-item">
                <label>🔑 Encryption Key (save this!):</label>
                <input type="text" readonly value="${response.key}">
            </div>
        `;
    }
    
    if (response.method) {
        html += `<div class="alert alert-info">🔒 Method: ${response.method}</div>`;
    }
    
    container.innerHTML = html;
}

function displayDecryptionResult(containerId, response) {
    const container = document.getElementById(containerId);
    container.style.display = 'block';
    
    let html = '<h4>✅ Decryption Successful</h4>';
    
    if (response.decrypted_data) {
        html += `
            <div class="result-item">
                <label>🔓 Decrypted Data:</label>
                <textarea readonly rows="3">${response.decrypted_data}</textarea>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

function displayFileEncryptionResult(containerId, response) {
    const container = document.getElementById(containerId);
    container.style.display = 'block';
    
    let html = '<h4>✅ File Encryption Successful</h4>';
    
    if (response.download_url) {
        html += `
            <div class="result-item">
                <label>📥 Download Encrypted File:</label>
                <a href="${response.download_url}" download class="btn btn-primary">Download File</a>
            </div>
        `;
    }
    
    if (response.key) {
        html += `
            <div class="result-item">
                <label>🔑 Encryption Key (save this!):</label>
                <input type="text" readonly value="${response.key}">
            </div>
        `;
    }
    
    if (response.salt) {
        html += `
            <div class="result-item">
                <label>🧂 Salt (save this!):</label>
                <input type="text" readonly value="${response.salt}">
            </div>
        `;
    }
    
    if (response.file_size) {
        html += `<div class="alert alert-info">📊 Original Size: ${response.file_size} bytes</div>`;
    }
    
    if (response.encrypted_size) {
        html += `<div class="alert alert-info">📊 Encrypted Size: ${response.encrypted_size} bytes</div>`;
    }
    
    container.innerHTML = html;
}

function displayFileDecryptionResult(containerId, response) {
    const container = document.getElementById(containerId);
    container.style.display = 'block';
    
    let html = '<h4>✅ File Decryption Successful</h4>';
    
    if (response.download_url) {
        html += `
            <div class="result-item">
                <label>📥 Download Decrypted File:</label>
                <a href="${response.download_url}" download class="btn btn-primary">Download File</a>
            </div>
        `;
    }
    
    if (response.file_size) {
        html += `<div class="alert alert-info">📊 Decrypted Size: ${response.file_size} bytes</div>`;
    }
    
    container.innerHTML = html;
}

function displayLifecycleResult(containerId, response) {
    const container = document.getElementById(containerId);
    container.style.display = 'block';
    
    let html = '<h4>✅ Lifecycle Demo Completed</h4>';
    
    if (response.stages) {
        const stages = response.stages;
        
        if (stages['1_at_rest_encryption']) {
            const stage1 = stages['1_at_rest_encryption'];
            html += `
                <div style="margin: 20px 0; padding: 15px; background: #f0fdf4; border-left: 4px solid #22c55e; border-radius: 8px;">
                    <h5 style="color: #16a34a;">📦 Stage 1: At-Rest Encryption</h5>
                    <div class="result-item">
                        <label>Encrypted Data:</label>
                        <textarea readonly rows="2">${stage1.encrypted_data}</textarea>
                    </div>
                </div>
            `;
        }
        
        if (stages['3_in_transit_encryption']) {
            const stage3 = stages['3_in_transit_encryption'];
            html += `
                <div style="margin: 20px 0; padding: 15px; background: #fef3c7; border-left: 4px solid #f59e0b; border-radius: 8px;">
                    <h5 style="color: #d97706;">🚀 Stage 3: In-Transit Encryption</h5>
                    <div class="result-item">
                        <label>Encrypted for Transmission:</label>
                        <textarea readonly rows="2">${stage3.encrypted_data}</textarea>
                    </div>
                </div>
            `;
        }
    }
    
    container.innerHTML = html;
}

function displayFileLifecycleResult(containerId, response) {
    const container = document.getElementById(containerId);
    container.style.display = 'block';
    
    let html = '<h4>✅ File Lifecycle Demo Completed</h4>';
    
    if (response.stages) {
        const stages = response.stages;
        
        if (stages['1_at_rest_encryption']) {
            const stage1 = stages['1_at_rest_encryption'];
            html += `
                <div style="margin: 20px 0; padding: 15px; background: #f0fdf4; border-left: 4px solid #22c55e; border-radius: 8px;">
                    <h5 style="color: #16a34a;">📦 Stage 1: At-Rest Encryption</h5>
                    <div class="result-item">
                        <label>File Encrypted Successfully</label>
                        ${stage1.download_url ? `<a href="${stage1.download_url}" download class="btn btn-primary">Download Encrypted File</a>` : ''}
                    </div>
                </div>
            `;
        }
        
        if (stages['3_in_transit_encryption']) {
            const stage3 = stages['3_in_transit_encryption'];
            html += `
                <div style="margin: 20px 0; padding: 15px; background: #fef3c7; border-left: 4px solid #f59e0b; border-radius: 8px;">
                    <h5 style="color: #d97706;">🚀 Stage 3: In-Transit Encryption</h5>
                    <div class="result-item">
                        <label>File Ready for Transmission</label>
                        ${stage3.download_url ? `<a href="${stage3.download_url}" download class="btn btn-primary">Download for Transmission</a>` : ''}
                    </div>
                </div>
            `;
        }
    }
    
    container.innerHTML = html;
}

// Make functions globally available
window.showSection = showSection;
window.switchEncryptionTab = switchEncryptionTab;
window.handleLogout = handleLogout;
window.handleEncryptInTransit = handleEncryptInTransit;
window.handleEncryptFileInTransit = handleEncryptFileInTransit;
window.handleDecryptInTransit = handleDecryptInTransit;
window.handleDecryptFileInTransit = handleDecryptFileInTransit;
window.handleEncryptAtRest = handleEncryptAtRest;
window.handleEncryptFileAtRest = handleEncryptFileAtRest;
window.handleDecryptAtRest = handleDecryptAtRest;
window.handleDecryptFileAtRest = handleDecryptFileAtRest;
window.handleLifecycleDemo = handleLifecycleDemo;
window.handleFileLifecycleDemo = handleFileLifecycleDemo;
