
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
    // Hide all main tab contents
    document.querySelectorAll('#encryptionSection > .tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active from main tab buttons only (first set)
    const mainTabContainer = document.querySelector('#encryptionSection > .encryption-tabs');
    if (mainTabContainer) {
        mainTabContainer.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
    }
    
    // Show selected main tab
    document.getElementById(`${tabName}Tab`).classList.add('active');
    
    // Set active button
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
// Add these functions to the bottom of your dashboard.js file
function switchInTransitSubTab(tabName) {
    // Remove active from all sub-tab contents
    document.querySelectorAll('#inTransitTab .sub-tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active from sub-tab buttons only (second set of tabs)
    const subTabContainer = document.querySelectorAll('#inTransitTab .encryption-tabs')[0];
    if (subTabContainer) {
        subTabContainer.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
    }
    
    // Properly capitalize: encryptText -> EncryptText, decryptFile -> DecryptFile
    const capitalizedTabName = tabName.charAt(0).toUpperCase() + tabName.slice(1);
    const targetTab = document.getElementById(`inTransit${capitalizedTabName}Tab`);
    
    if (targetTab) {
        targetTab.classList.add('active');
    } else {
        console.error('Target tab not found:', `inTransit${capitalizedTabName}Tab`);
    }
    
    // Set active button
    if (typeof event !== 'undefined' && event && event.target) {
        event.target.classList.add('active');
    }
}
function switchAtRestSubTab(tabName) {
    // Remove active from all sub-tab contents
    document.querySelectorAll('#atRestTab .sub-tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active from sub-tab buttons only
    const subTabContainer = document.querySelectorAll('#atRestTab .encryption-tabs')[0];
    if (subTabContainer) {
        subTabContainer.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
    }
    
    // Capitalize first letter of tabName
    const capitalizedTabName = tabName.charAt(0).toUpperCase() + tabName.slice(1);
    const targetTab = document.getElementById(`atRest${capitalizedTabName}Tab`);
    
    if (targetTab) {
        targetTab.classList.add('active');
    }
    
    // Set active button
    if (event && event.target) {
        event.target.classList.add('active');
    }
}
function switchLifecycleSubTab(tabName) {
    // Remove active from all sub-tab contents
    document.querySelectorAll('#lifecycleTab .sub-tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active from sub-tab buttons only
    const subTabContainer = document.querySelectorAll('#lifecycleTab .encryption-tabs')[0];
    if (subTabContainer) {
        subTabContainer.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
    }
    
    // Capitalize first letter of tabName
    const capitalizedTabName = tabName.charAt(0).toUpperCase() + tabName.slice(1);
    const targetTab = document.getElementById(`lifecycle${capitalizedTabName}Tab`);
    
    if (targetTab) {
        targetTab.classList.add('active');
    }
    
    // Set active button
    if (event && event.target) {
        event.target.classList.add('active');
    }
}

// ============= FIXED FILE DOWNLOAD AND DISPLAY FUNCTIONS =============

function displayFileEncryptionResult(containerId, response) {
    const container = document.getElementById(containerId);
    container.style.display = 'block';
    
    let html = '<h4>✅ File Encryption Successful</h4>';
    
    // Create download button for encrypted data (response.encrypted_data exists)
    if (response.encrypted_data) {
        const encFilename = (response.original_filename || 'encrypted_file') + '.enc';
        const buttonId = 'downloadBtn_' + containerId;
        
        html += `
            <div class="result-item">
                <label>📥 Download Encrypted File:</label>
                <button id="${buttonId}" class="btn btn-primary" style="width: 100%; padding: 12px; font-size: 16px;">
                    📥 Download ${encFilename}
                </button>
                <small style="color: #6b7280; display: block; margin-top: 8px;">
                    Click the button above to download the encrypted file
                </small>
            </div>
        `;
    }
    
    // Display encryption key if present (at-rest encryption)
    if (response.key) {
        const keyId = 'encKey_' + containerId;
        html += `
            <div class="result-item">
                <label>🔑 Encryption Key (SAVE THIS!):</label>
                <input type="text" id="${keyId}" readonly value="${response.key}" style="width: 100%; font-family: monospace; font-size: 12px; padding: 10px; margin-bottom: 8px; box-sizing: border-box;">
                <button id="copyBtn_${keyId}" class="btn" style="background: #10b981; color: white; padding: 10px 16px; width: 100%; font-size: 14px;">
                    📋 Copy Key
                </button>
                <div style="background: #fee2e2; padding: 12px; border-radius: 6px; border-left: 4px solid #dc2626; margin-top: 12px;">
                    <strong style="color: #dc2626;">⚠️ CRITICAL:</strong>
                    <p style="color: #991b1b; margin: 8px 0 0 0; font-size: 14px;">
                        You MUST save this key! Without it, you cannot decrypt your file. Copy it now and store it safely.
                    </p>
                </div>
            </div>
        `;
    }
    
    // Display salt if present (in-transit encryption)
    if (response.salt) {
        const saltId = 'encSalt_' + containerId;
        html += `
            <div class="result-item">
                <label>🧂 Salt (SAVE THIS!):</label>
                <input type="text" id="${saltId}" readonly value="${response.salt}" style="width: 100%; font-family: monospace; font-size: 12px; padding: 10px; margin-bottom: 8px; box-sizing: border-box;">
                <button id="copyBtn_${saltId}" class="btn" style="background: #10b981; color: white; padding: 10px 16px; width: 100%; font-size: 14px;">
                    📋 Copy Salt
                </button>
                <div style="background: #fee2e2; padding: 12px; border-radius: 6px; border-left: 4px solid #dc2626; margin-top: 12px;">
                    <strong style="color: #dc2626;">⚠️ CRITICAL:</strong>
                    <p style="color: #991b1b; margin: 8px 0 0 0; font-size: 14px;">
                        You MUST save this salt along with your password! Without it, you cannot decrypt your file.
                    </p>
                </div>
            </div>
        `;
    }
    
    // File size info
    if (response.file_size) {
        html += `<div class="alert alert-info" style="margin-top: 16px;">📊 Original Size: ${formatBytes(response.file_size)}</div>`;
    }
    
    if (response.encrypted_size) {
        html += `<div class="alert alert-info">📊 Encrypted Size: ${formatBytes(response.encrypted_size)}</div>`;
    }
    
    if (response.method) {
        html += `<div class="alert alert-info">🔐 Method: ${response.method}</div>`;
    }
    
    container.innerHTML = html;
    
    // Attach event listeners after DOM update
    setTimeout(() => {
        // Download button for encrypted file
        if (response.encrypted_data) {
            const encFilename = (response.original_filename || 'encrypted_file') + '.enc';
            const downloadBtn = document.getElementById('downloadBtn_' + containerId);
            if (downloadBtn) {
                downloadBtn.addEventListener('click', function() {
                    downloadEncryptedFile(response.encrypted_data, encFilename);
                });
            }
        }
        
        // Copy button for key
        if (response.key) {
            const keyId = 'encKey_' + containerId;
            const copyKeyBtn = document.getElementById('copyBtn_' + keyId);
            if (copyKeyBtn) {
                copyKeyBtn.addEventListener('click', function() {
                    copyToClipboard(keyId, this);
                });
            }
        }
        
        // Copy button for salt
        if (response.salt) {
            const saltId = 'encSalt_' + containerId;
            const copySaltBtn = document.getElementById('copyBtn_' + saltId);
            if (copySaltBtn) {
                copySaltBtn.addEventListener('click', function() {
                    copyToClipboard(saltId, this);
                });
            }
        }
    }, 100);
}

function displayFileDecryptionResult(containerId, response) {
    const container = document.getElementById(containerId);
    container.style.display = 'block';
    
    let html = '<h4>✅ File Decryption Successful</h4>';
    
    // Download button for decrypted file
    if (response.decrypted_data) {
        const decFilename = response.original_filename || 'decrypted_file';
        const buttonId = 'downloadDecBtn_' + containerId;
        
        html += `
            <div class="result-item">
                <label>📥 Download Decrypted File:</label>
                <button id="${buttonId}" class="btn btn-primary" style="width: 100%; padding: 12px; font-size: 16px; background: #10b981;">
                    📥 Download ${decFilename}
                </button>
                <small style="color: #6b7280; display: block; margin-top: 8px;">
                    Your file has been successfully decrypted! Click above to download.
                </small>
            </div>
        `;
    }
    
    if (response.file_size) {
        html += `<div class="alert alert-info" style="margin-top: 16px;">📊 File Size: ${formatBytes(response.file_size)}</div>`;
    }
    
    if (response.method) {
        html += `<div class="alert alert-info">🔓 Method: ${response.method}</div>`;
    }
    
    container.innerHTML = html;
    
    // Attach event listener to download button
    if (response.decrypted_data) {
        setTimeout(() => {
            const decFilename = response.original_filename || 'decrypted_file';
            const downloadBtn = document.getElementById('downloadDecBtn_' + containerId);
            if (downloadBtn) {
                downloadBtn.addEventListener('click', function() {
                    downloadDecryptedFile(response.decrypted_data, decFilename);
                });
            }
        }, 100);
    }
}

// Helper function to download encrypted file (saves as plain text .enc file)
function downloadEncryptedFile(encryptedData, filename) {
    try {
        console.log('📥 Downloading encrypted file:', filename);
        console.log('📊 Data length:', encryptedData.length);
        
        // The encrypted_data is base64 text, save it as a text file
        const blob = new Blob([encryptedData], { type: 'text/plain' });
        
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        
        // Cleanup
        setTimeout(() => {
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        }, 100);
        
        console.log('✅ File download initiated:', filename);
    } catch (error) {
        console.error('❌ Download error:', error);
        alert('❌ Failed to download file: ' + error.message);
    }
}

// Helper function to download decrypted file (converts base64 back to binary)
function downloadDecryptedFile(base64Data, filename) {
    try {
        console.log('📥 Downloading decrypted file:', filename);
        console.log('📊 Base64 data length:', base64Data.length);
        
        // Convert base64 to binary
        const byteCharacters = atob(base64Data);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: 'application/octet-stream' });
        
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        
        // Cleanup
        setTimeout(() => {
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        }, 100);
        
        console.log('✅ File download initiated:', filename);
    } catch (error) {
        console.error('❌ Download error:', error);
        alert('❌ Failed to download file: ' + error.message);
    }
}

// Helper function to copy text to clipboard
function copyToClipboard(elementId, buttonElement) {
    const element = document.getElementById(elementId);
    if (!element) {
        console.error('Element not found:', elementId);
        return;
    }
    
    // Select the text
    element.select();
    element.setSelectionRange(0, 99999); // For mobile devices
    
    try {
        // Try modern clipboard API first
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(element.value).then(() => {
                showCopySuccess(buttonElement);
            }).catch(() => {
                // Fallback to execCommand
                fallbackCopy(element, buttonElement);
            });
        } else {
            // Fallback for older browsers
            fallbackCopy(element, buttonElement);
        }
    } catch (err) {
        console.error('Copy failed:', err);
        alert('Failed to copy. Please select and copy manually.');
    }
}

function fallbackCopy(element, buttonElement) {
    const successful = document.execCommand('copy');
    if (successful) {
        showCopySuccess(buttonElement);
    } else {
        alert('Failed to copy. Please select and copy manually.');
    }
}

function showCopySuccess(buttonElement) {
    if (buttonElement) {
        const originalHTML = buttonElement.innerHTML;
        const originalBg = buttonElement.style.background;
        
        buttonElement.innerHTML = '✅ Copied!';
        buttonElement.style.background = '#059669';
        
        setTimeout(() => {
            buttonElement.innerHTML = originalHTML;
            buttonElement.style.background = originalBg;
        }, 2000);
    }
}

// Helper function to format bytes
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}
window.switchInTransitSubTab = switchInTransitSubTab;
window.switchAtRestSubTab = switchAtRestSubTab;
window.switchLifecycleSubTab = switchLifecycleSubTab;

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
