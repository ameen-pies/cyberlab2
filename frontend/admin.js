// Check authentication
if (!Storage.getToken()) {
    window.location.href = 'index.html';
}

let allUsers = [];
let permissionCategories = {};
let currentEditingUser = null;

// Permission categories (fallback if API fails)
const DEFAULT_CATEGORIES = {
    "Encryption Service": [
        { value: "encrypt_text", name: "Encrypt Text" },
        { value: "encrypt_file", name: "Encrypt Files" },
        { value: "decrypt_text", name: "Decrypt Text" },
        { value: "decrypt_file", name: "Decrypt Files" }
    ],
    "KeyVault - Keys": [
        { value: "keyvault_generate_keys", name: "Generate Keys" },
        { value: "keyvault_view_keys", name: "View Keys" },
        { value: "keyvault_download_keys", name: "Download Keys" },
        { value: "keyvault_rotate_keys", name: "Rotate Keys" },
        { value: "keyvault_delete_keys", name: "Delete Keys" },
        { value: "keyvault_send_email", name: "Send via Email" }
    ],
    "KeyVault - Certificates": [
        { value: "keyvault_generate_certs", name: "Generate Certificates" },
        { value: "keyvault_view_certs", name: "View Certificates" },
        { value: "keyvault_download_certs", name: "Download Certificates" }
    ],
    "Password Checker": [
        { value: "password_check", name: "Check Password Strength" },
        { value: "password_breach_check", name: "Check Breach Database" },
        { value: "password_policy_manage", name: "Manage Policies" }
    ],
    "Secret Scanner": [
        { value: "scanner_text", name: "Scan Text" },
        { value: "scanner_file", name: "Scan Files" },
        { value: "scanner_github", name: "Scan GitHub URLs" }
    ],
    "User Management": [
        { value: "view_users", name: "View Users" },
        { value: "create_users", name: "Create Users" },
        { value: "update_users", name: "Update Users" },
        { value: "delete_users", name: "Delete Users" },
        { value: "manage_permissions", name: "Manage Permissions" }
    ]
};

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    await loadPermissionCategories();
    await loadUsers();
});

// Load permission categories
async function loadPermissionCategories() {
    try {
        const response = await apiRequest('/users/permissions/categories', { method: 'GET' });
        if (response.success) {
            permissionCategories = response.categories;
        }
    } catch (error) {
        console.warn('Using default permission categories');
        permissionCategories = DEFAULT_CATEGORIES;
    }
}

// Load users
async function loadUsers() {
    try {
        const response = await apiRequest('/users/all', { method: 'GET' });
        allUsers = response;
        updateStats();
        displayUsers(allUsers);
    } catch (error) {
        console.error('Failed to load users:', error);
        document.getElementById('usersList').innerHTML = `
            <p style="color: #dc2626; text-align: center; padding: 20px;">
                ❌ Failed to load users. Make sure you have admin permissions.
            </p>`;
    }
}

// Update statistics
function updateStats() {
    document.getElementById('totalUsers').textContent = allUsers.length;
    document.getElementById('totalAdmins').textContent = allUsers.filter(u => u.role === 'admin').length;
    document.getElementById('activeUsers').textContent = allUsers.filter(u => u.is_active).length;
}

// Filter users
function filterUsers() {
    const search = document.getElementById('searchInput').value.toLowerCase();
    const roleFilter = document.getElementById('roleFilter').value;
    
    let filtered = allUsers;
    
    if (search) {
        filtered = filtered.filter(u => 
            u.email.toLowerCase().includes(search) || 
            u.full_name.toLowerCase().includes(search)
        );
    }
    
    if (roleFilter) {
        filtered = filtered.filter(u => u.role === roleFilter);
    }
    
    displayUsers(filtered);
}

// Display users
function displayUsers(users) {
    const container = document.getElementById('usersList');
    
    if (users.length === 0) {
        container.innerHTML = '<p style="color: #6b7280; text-align: center; padding: 20px;">No users found</p>';
        return;
    }
    
    let html = '';
    
    users.forEach(user => {
        const roleClass = `role-${user.role}`;
        const statusClass = user.is_active ? 'status-active' : 'status-inactive';
        const statusIcon = user.is_active ? '✅' : '❌';
        const verifiedIcon = user.is_verified ? '✓ Verified' : '✗ Not Verified';
        
        // Role emoji
        const roleEmoji = {
            'admin': '👑',
            'co_admin': '🛡️',
            'normal': '👤',
            'limited': '🔒'
        }[user.role] || '👤';
        
        html += `
            <div class="user-card" data-email="${user.email}">
                <div class="user-header">
                    <div class="user-info">
                        <h4>${roleEmoji} ${user.full_name}</h4>
                        <p>📧 ${user.email}</p>
                        <p style="font-size: 12px; margin-top: 5px;">
                            <span class="${statusClass}">${statusIcon} ${user.is_active ? 'Active' : 'Inactive'}</span>
                            &nbsp;|&nbsp;
                            <span style="color: ${user.is_verified ? '#16a34a' : '#dc2626'}">${verifiedIcon}</span>
                            &nbsp;|&nbsp;
                            <span>🔐 Custom Perms: ${user.custom_permissions?.length || 0}</span>
                        </p>
                    </div>
                    <span class="role-badge ${roleClass}">${user.role.replace('_', ' ')}</span>
                </div>
                
                <div class="quick-actions">
                    <button onclick="openPermissionModal('${user.email}')" class="btn btn-primary btn-sm">
                        🔐 Edit Permissions
                    </button>
                    <button onclick="changeUserRole('${user.email}', '${user.role}')" class="btn btn-secondary btn-sm">
                        🎭 Change Role
                    </button>
                    <button onclick="toggleUserStatus('${user.email}', ${user.is_active})" class="btn btn-secondary btn-sm">
                        ${user.is_active ? '🚫 Deactivate' : '✅ Activate'}
                    </button>
                    <button onclick="deleteUser('${user.email}')" class="btn btn-secondary btn-sm" style="background: #fee2e2; color: #dc2626;">
                        🗑️ Delete
                    </button>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// Open permission modal with enhanced two-column design
async function openPermissionModal(email) {
    const user = allUsers.find(u => u.email === email);
    if (!user) return;
    
    currentEditingUser = email;
    
    // Role emoji
    const roleEmoji = {
        'admin': '👑',
        'co_admin': '🛡️',
        'normal': '👤'
    }[user.role] || '👤';
    
    document.getElementById('permModalTitle').innerHTML = `${roleEmoji} Edit Permissions - ${user.full_name}`;
    
    // Fetch current permissions
    let userPerms = { custom_permissions: [], role_permissions: [], effective_permissions: [] };
    try {
        userPerms = await apiRequest(`/users/${email}/permissions`, { method: 'GET' });
    } catch (e) {
        console.error('Failed to fetch permissions:', e);
    }
    
    const rolePerms = userPerms.role_permissions || [];
    const customPerms = userPerms.custom_permissions || [];
    const effectivePerms = userPerms.effective_permissions || [];
    
    // Get all available permissions
    const categories = Object.keys(permissionCategories).length > 0 ? permissionCategories : DEFAULT_CATEGORIES;
    const allPermissions = [];
    
    for (const [category, perms] of Object.entries(categories)) {
        perms.forEach(perm => {
            allPermissions.push({
                value: perm.value || perm,
                name: perm.name || perm,
                category: category
            });
        });
    }
    
    let html = `
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 24px; border-radius: 12px; margin-bottom: 24px;">
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px;">
                <div style="text-align: center;">
                    <div style="font-size: 14px; opacity: 0.9;">📧 Email</div>
                    <div style="font-weight: 600; font-size: 16px;">${user.email}</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 14px; opacity: 0.9;">🎭 Role</div>
                    <div style="font-weight: 600; font-size: 16px;">${user.role.toUpperCase()}</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 14px; opacity: 0.9;">🔐 Role Perms</div>
                    <div style="font-weight: 600; font-size: 16px;">${rolePerms.length}</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 14px; opacity: 0.9;">➕ Custom Perms</div>
                    <div style="font-weight: 600; font-size: 16px;">${customPerms.length}</div>
                </div>
            </div>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 24px;">
            <!-- Available Permissions -->
            <div style="background: white; border-radius: 12px; padding: 0; border: 1px solid #e5e7eb; overflow: hidden;">
                <div style="background: #f8fafc; padding: 16px 20px; border-bottom: 1px solid #e5e7eb;">
                    <h4 style="margin: 0; color: #374151; display: flex; align-items: center; gap: 8px;">
                        <span style="background: #3b82f6; color: white; width: 24px; height: 24px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 12px;">📋</span>
                        Available Permissions
                    </h4>
                </div>
                <div style="padding: 16px;">
                    <input type="text" id="permSearchAvailable" placeholder="🔍 Search permissions..." 
                        style="width: 100%; padding: 12px; border: 1px solid #e5e7eb; border-radius: 8px; margin-bottom: 16px; font-size: 14px;"
                        onkeyup="filterPermissionLists()">
                    <div id="availablePermsList" style="max-height: 400px; overflow-y: auto; border-radius: 8px; background: #f9fafb;">
                    </div>
                </div>
            </div>
            
            <!-- Granted Permissions -->
            <div style="background: white; border-radius: 12px; padding: 0; border: 1px solid #e5e7eb; overflow: hidden;">
                <div style="background: #f0fdf4; padding: 16px 20px; border-bottom: 1px solid #dcfce7;">
                    <h4 style="margin: 0; color: #374151; display: flex; align-items: center; gap: 8px;">
                        <span style="background: #16a34a; color: white; width: 24px; height: 24px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 12px;">✅</span>
                        Granted Permissions
                    </h4>
                </div>
                <div style="padding: 16px;">
                    <input type="text" id="permSearchGranted" placeholder="🔍 Search granted..." 
                        style="width: 100%; padding: 12px; border: 1px solid #dcfce7; border-radius: 8px; margin-bottom: 16px; font-size: 14px; background: #f0fdf4;"
                        onkeyup="filterPermissionLists()">
                    <div id="grantedPermsList" style="max-height: 400px; overflow-y: auto; border-radius: 8px; background: #f0fdf4;">
                    </div>
                </div>
            </div>
        </div>
        
        <div style="display: flex; gap: 12px; justify-content: flex-end; padding-top: 20px; border-top: 1px solid #e5e7eb;">
            <button type="button" onclick="closePermissionModal()" class="btn btn-secondary" style="padding: 12px 24px;">
                ❌ Cancel
            </button>
            <button type="button" onclick="savePermissions()" class="btn btn-primary" style="padding: 12px 24px;">
                💾 Save Changes
            </button>
        </div>
    `;
    
    document.getElementById('permModalContent').innerHTML = html;
    document.getElementById('permissionModal').style.display = 'flex';
    
    // Store data for rendering
    window.currentPermissionData = {
        allPermissions,
        rolePerms,
        customPerms,
        effectivePerms
    };
    
    renderPermissionLists();
}

// Enhanced renderPermissionLists function
function renderPermissionLists(searchAvailable = '', searchGranted = '') {
    const data = window.currentPermissionData;
    if (!data) return;
    
    const { allPermissions, rolePerms, customPerms } = data;
    
    // Available permissions (not granted as custom)
    const availableContainer = document.getElementById('availablePermsList');
    const available = allPermissions.filter(p => 
        !customPerms.includes(p.value) && 
        !rolePerms.includes(p.value) &&
        (p.name.toLowerCase().includes(searchAvailable.toLowerCase()) || 
         p.category.toLowerCase().includes(searchAvailable.toLowerCase()))
    );
    
    let availableHtml = '';
    let currentCategory = '';
    
    if (available.length === 0) {
        availableHtml = `
            <div style="text-align: center; padding: 40px 20px; color: #6b7280;">
                <div style="font-size: 48px; margin-bottom: 16px;">📭</div>
                <div style="font-weight: 600; margin-bottom: 8px;">No permissions available</div>
                <div style="font-size: 14px;">All permissions have been granted</div>
            </div>
        `;
    } else {
        available.forEach(perm => {
            if (perm.category !== currentCategory) {
                currentCategory = perm.category;
                availableHtml += `
                    <div style="background: #e5e7eb; padding: 12px 16px; font-weight: 600; font-size: 13px; color: #374151; display: flex; align-items: center; gap: 8px;">
                        <span style="background: #6b7280; color: white; width: 20px; height: 20px; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 10px;">📁</span>
                        ${perm.category}
                    </div>
                `;
            }
            
            availableHtml += `
                <div style="padding: 12px 16px; border-bottom: 1px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center; transition: background-color 0.2s;">
                    <div>
                        <div style="font-weight: 500; font-size: 14px; color: #111827;">${perm.name}</div>
                        <div style="font-size: 12px; color: #6b7280; margin-top: 2px;">${perm.value}</div>
                    </div>
                    <button onclick="addPermission('${perm.value}')" 
                            class="btn btn-primary btn-sm" 
                            style="padding: 6px 12px; font-size: 12px; background: #3b82f6; border: none; border-radius: 6px; color: white; cursor: pointer; transition: all 0.2s;"
                            onmouseover="this.style.background='#2563eb'" 
                            onmouseout="this.style.background='#3b82f6'">
                        ➕ Add
                    </button>
                </div>
            `;
        });
    }
    
    availableContainer.innerHTML = availableHtml;
    
    // Granted permissions (custom + role)
    const grantedContainer = document.getElementById('grantedPermsList');
    const granted = allPermissions.filter(p => 
        (customPerms.includes(p.value) || rolePerms.includes(p.value)) &&
        (p.name.toLowerCase().includes(searchGranted.toLowerCase()) || 
         p.category.toLowerCase().includes(searchGranted.toLowerCase()))
    );
    
    let grantedHtml = '';
    currentCategory = '';
    
    if (granted.length === 0) {
        grantedHtml = `
            <div style="text-align: center; padding: 40px 20px; color: #6b7280;">
                <div style="font-size: 48px; margin-bottom: 16px;">🔒</div>
                <div style="font-weight: 600; margin-bottom: 8px;">No permissions granted</div>
                <div style="font-size: 14px;">Add permissions from the left panel</div>
            </div>
        `;
    } else {
        granted.forEach(perm => {
            if (perm.category !== currentCategory) {
                currentCategory = perm.category;
                grantedHtml += `
                    <div style="background: #dcfce7; padding: 12px 16px; font-weight: 600; font-size: 13px; color: #166534; display: flex; align-items: center; gap: 8px;">
                        <span style="background: #16a34a; color: white; width: 20px; height: 20px; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 10px;">📁</span>
                        ${perm.category}
                    </div>
                `;
            }
            
            const isRolePerm = rolePerms.includes(perm.value);
            const isCustomPerm = customPerms.includes(perm.value);
            
            grantedHtml += `
                <div style="padding: 12px 16px; border-bottom: 1px solid #dcfce7; display: flex; justify-content: space-between; align-items: center; transition: background-color 0.2s; ${isRolePerm ? 'opacity: 0.7;' : ''}">
                    <div style="flex: 1;">
                        <div style="font-weight: 500; font-size: 14px; color: #111827; display: flex; align-items: center; gap: 6px;">
                            ${perm.name}
                            ${isRolePerm ? 
                                '<span style="background: #6366f1; color: white; padding: 2px 6px; border-radius: 10px; font-size: 10px; font-weight: 600;">ROLE</span>' : 
                                '<span style="background: #10b981; color: white; padding: 2px 6px; border-radius: 10px; font-size: 10px; font-weight: 600;">CUSTOM</span>'
                            }
                        </div>
                        <div style="font-size: 12px; color: #6b7280; margin-top: 2px;">${perm.value}</div>
                    </div>
                    ${isCustomPerm ? `
                        <button onclick="removePermission('${perm.value}')" 
                                class="btn btn-secondary btn-sm" 
                                style="padding: 6px 12px; font-size: 12px; background: #fee2e2; border: none; border-radius: 6px; color: #dc2626; cursor: pointer; transition: all 0.2s;"
                                onmouseover="this.style.background='#fecaca'" 
                                onmouseout="this.style.background='#fee2e2'">
                            ❌ Remove
                        </button>
                    ` : `
                        <span style="font-size: 11px; color: #6b7280; font-weight: 500; padding: 4px 8px; background: #f3f4f6; border-radius: 4px;">
                            🔒 Role Permission
                        </span>
                    `}
                </div>
            `;
        });
    }
    
    grantedContainer.innerHTML = grantedHtml;
}

// Enhanced permission management functions
function addPermission(permValue) {
    const data = window.currentPermissionData;
    if (!data.customPerms.includes(permValue)) {
        data.customPerms.push(permValue);
        
        // Show visual feedback
        const button = event.target;
        const originalText = button.innerHTML;
        button.innerHTML = '✅ Added';
        button.style.background = '#10b981';
        button.disabled = true;
        
        setTimeout(() => {
            button.innerHTML = originalText;
            button.style.background = '#3b82f6';
            button.disabled = false;
        }, 1000);
        
        renderPermissionLists();
    }
}

function removePermission(permValue) {
    const data = window.currentPermissionData;
    const index = data.customPerms.indexOf(permValue);
    if (index > -1) {
        data.customPerms.splice(index, 1);
        
        // Show visual feedback
        const button = event.target;
        const originalText = button.innerHTML;
        button.innerHTML = '🗑️ Removed';
        button.style.background = '#6b7280';
        button.disabled = true;
        
        setTimeout(() => {
            renderPermissionLists();
        }, 500);
    }
}

// Enhanced save permissions with better feedback
async function savePermissions() {
    if (!currentEditingUser) return;
    
    const data = window.currentPermissionData;
    const customPerms = data.customPerms;
    
    // Show loading state
    const saveButton = document.querySelector('#permissionModal .btn-primary');
    const originalText = saveButton.innerHTML;
    saveButton.innerHTML = '⏳ Saving...';
    saveButton.disabled = true;
    
    try {
        await apiRequest(`/users/${currentEditingUser}/permissions`, {
            method: 'PUT',
            body: JSON.stringify({
                permissions: customPerms,
                action: 'set'
            })
        });
        
        // Show success state
        saveButton.innerHTML = '✅ Saved!';
        saveButton.style.background = '#10b981';
        
        setTimeout(() => {
            closePermissionModal();
            loadUsers();
        }, 1000);
        
    } catch (error) {
        // Show error state
        saveButton.innerHTML = '❌ Failed';
        saveButton.style.background = '#dc2626';
        setTimeout(() => {
            saveButton.innerHTML = originalText;
            saveButton.style.background = '';
            saveButton.disabled = false;
        }, 2000);
        
        alert('❌ Failed to update permissions: ' + error.message);
    }
}

// Render permission lists
function renderPermissionLists(searchAvailable = '', searchGranted = '') {
    const data = window.currentPermissionData;
    if (!data) return;
    
    const { allPermissions, rolePerms, customPerms } = data;
    
    // Available permissions (not granted as custom)
    const availableContainer = document.getElementById('availablePermsList');
    const available = allPermissions.filter(p => 
        !customPerms.includes(p.value) && 
        !rolePerms.includes(p.value) &&
        (p.name.toLowerCase().includes(searchAvailable.toLowerCase()) || 
         p.category.toLowerCase().includes(searchAvailable.toLowerCase()))
    );
    
    let availableHtml = '';
    let currentCategory = '';
    
    available.forEach(perm => {
        if (perm.category !== currentCategory) {
            currentCategory = perm.category;
            availableHtml += `<div style="background: #e5e7eb; padding: 8px 12px; font-weight: 600; font-size: 12px; color: #374151;">${perm.category}</div>`;
        }
        
        availableHtml += `
            <div style="padding: 10px 12px; border-bottom: 1px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 14px;">${perm.name}</span>
                <button onclick="addPermission('${perm.value}')" class="btn btn-primary btn-sm" style="padding: 4px 12px; font-size: 12px;">
                    ➕ Add
                </button>
            </div>
        `;
    });
    
    availableContainer.innerHTML = availableHtml || '<p style="padding: 20px; text-align: center; color: #6b7280;">No available permissions</p>';
    
    // Granted permissions (custom + role)
    const grantedContainer = document.getElementById('grantedPermsList');
    const granted = allPermissions.filter(p => 
        (customPerms.includes(p.value) || rolePerms.includes(p.value)) &&
        (p.name.toLowerCase().includes(searchGranted.toLowerCase()) || 
         p.category.toLowerCase().includes(searchGranted.toLowerCase()))
    );
    
    let grantedHtml = '';
    currentCategory = '';
    
    granted.forEach(perm => {
        if (perm.category !== currentCategory) {
            currentCategory = perm.category;
            grantedHtml += `<div style="background: #86efac; padding: 8px 12px; font-weight: 600; font-size: 12px; color: #166534;">${perm.category}</div>`;
        }
        
        const isRolePerm = rolePerms.includes(perm.value);
        const isCustomPerm = customPerms.includes(perm.value);
        
        grantedHtml += `
            <div style="padding: 10px 12px; border-bottom: 1px solid #86efac; display: flex; justify-content: space-between; align-items: center; ${isRolePerm ? 'opacity: 0.6;' : ''}">
                <span style="font-size: 14px;">
                    ${perm.name}
                    ${isRolePerm ? '<span style="font-size: 10px; color: #6366f1; margin-left: 8px;">(from role)</span>' : ''}
                </span>
                ${isCustomPerm ? `
                    <button onclick="removePermission('${perm.value}')" class="btn btn-secondary btn-sm" style="padding: 4px 12px; font-size: 12px; background: #fee2e2; color: #dc2626;">
                        ❌ Remove
                    </button>
                ` : '<span style="font-size: 12px; color: #6b7280;">🔒 Role perm</span>'}
            </div>
        `;
    });
    
    grantedContainer.innerHTML = grantedHtml || '<p style="padding: 20px; text-align: center; color: #6b7280;">No permissions granted</p>';
}

// Filter permission lists
function filterPermissionLists() {
    const searchAvailable = document.getElementById('permSearchAvailable')?.value || '';
    const searchGranted = document.getElementById('permSearchGranted')?.value || '';
    renderPermissionLists(searchAvailable, searchGranted);
}

// Add permission
function addPermission(permValue) {
    const data = window.currentPermissionData;
    if (!data.customPerms.includes(permValue)) {
        data.customPerms.push(permValue);
        renderPermissionLists();
    }
}

// Remove permission
function removePermission(permValue) {
    const data = window.currentPermissionData;
    const index = data.customPerms.indexOf(permValue);
    if (index > -1) {
        data.customPerms.splice(index, 1);
        renderPermissionLists();
    }
}

// Close permission modal
function closePermissionModal() {
    document.getElementById('permissionModal').style.display = 'none';
    currentEditingUser = null;
    window.currentPermissionData = null;
}

// Save permissions
async function savePermissions() {
    if (!currentEditingUser) return;
    
    const data = window.currentPermissionData;
    const customPerms = data.customPerms;
    
    try {
        await apiRequest(`/users/${currentEditingUser}/permissions`, {
            method: 'PUT',
            body: JSON.stringify({
                permissions: customPerms,
                action: 'set'
            })
        });
        
        alert(`✅ Permissions updated!\n\n📊 ${customPerms.length} custom permissions saved for ${currentEditingUser}`);
        closePermissionModal();
        await loadUsers();
    } catch (error) {
        alert('❌ Failed to update permissions: ' + error.message);
    }
}

// Change user role
async function changeUserRole(email, currentRole) {
    const roles = ['normal', 'co_admin', 'admin'];
    const roleNames = { 
        normal: '👤 Normal User', 
        co_admin: '🛡️ Co-Admin', 
        admin: '👑 Admin',
        limited: '🔒 Limited User'
    };
    
    const newRole = prompt(
        `🎭 Change role for ${email}\n\nCurrent: ${roleNames[currentRole]}\n\nEnter new role (normal, co_admin, admin):`,
        currentRole
    );
    
    if (!newRole || newRole === currentRole) return;
    if (!roles.includes(newRole)) {
        alert('❌ Invalid role. Use: normal, co_admin, or admin');
        return;
    }
    
    try {
        await apiRequest(`/users/${email}`, {
            method: 'PUT',
            body: JSON.stringify({ role: newRole })
        });
        
        alert(`✅ Role changed to ${roleNames[newRole]}`);
        await loadUsers();
    } catch (error) {
        alert('❌ Failed: ' + error.message);
    }
}

// Toggle user status
async function toggleUserStatus(email, isActive) {
    const action = isActive ? 'deactivate' : 'activate';
    if (!confirm(`⚠️ Are you sure you want to ${action} ${email}?`)) return;
    
    try {
        await apiRequest(`/users/${email}`, {
            method: 'PUT',
            body: JSON.stringify({ is_active: !isActive })
        });
        
        alert(`✅ User ${action}d successfully`);
        await loadUsers();
    } catch (error) {
        alert('❌ Failed: ' + error.message);
    }
}

// Delete user
async function deleteUser(email) {
    if (!confirm(`⚠️ Are you sure you want to DELETE ${email}?\n\n🚨 This action cannot be undone!`)) return;
    
    try {
        await apiRequest(`/users/${email}`, { method: 'DELETE' });
        alert(`✅ User ${email} deleted successfully`);
        await loadUsers();
    } catch (error) {
        alert('❌ Failed: ' + error.message);
    }
}

// Open create user modal
function openCreateUserModal() {
    document.getElementById('newUserEmail').value = '';
    document.getElementById('newUserName').value = '';
    document.getElementById('newUserPassword').value = '';
    document.getElementById('newUserRole').value = 'normal';
    document.getElementById('createUserModal').style.display = 'flex';
}

// Close create user modal
function closeCreateUserModal() {
    document.getElementById('createUserModal').style.display = 'none';
}

// Create new user
async function handleCreateUser(event) {
    event.preventDefault();
    
    const email = document.getElementById('newUserEmail').value;
    const fullName = document.getElementById('newUserName').value;
    const password = document.getElementById('newUserPassword').value;
    const role = document.getElementById('newUserRole').value;
    
    if (password.length < 8) {
        alert('❌ Password must be at least 8 characters');
        return;
    }
    
    try {
        await apiRequest('/users/create', {
            method: 'POST',
            body: JSON.stringify({
                email: email,
                full_name: fullName,
                password: password,
                role: role,
                custom_permissions: []
            })
        });
        
        alert(`✅ User ${email} created successfully!\n\n👤 Role: ${role}`);
        closeCreateUserModal();
        await loadUsers();
    } catch (error) {
        alert('❌ Failed to create user: ' + error.message);
    }
}

// Close modals on outside click
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
}

// Make functions globally available
window.openPermissionModal = openPermissionModal;
window.closePermissionModal = closePermissionModal;
window.savePermissions = savePermissions;
window.addPermission = addPermission;
window.removePermission = removePermission;
window.filterPermissionLists = filterPermissionLists;
window.changeUserRole = changeUserRole;
window.toggleUserStatus = toggleUserStatus;
window.deleteUser = deleteUser;
window.openCreateUserModal = openCreateUserModal;
window.closeCreateUserModal = closeCreateUserModal;
window.handleCreateUser = handleCreateUser;
window.filterUsers = filterUsers;