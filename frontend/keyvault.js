// Check authentication
if (!Storage.getToken()) {
    window.location.href = 'index.html';
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    await loadStatistics();
    await loadKeys();
    await loadCertificates();
});

// Switch tabs
function switchTab(tabName) {
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

// Load statistics
async function loadStatistics() {
    try {
        const response = await apiRequest('/keyvault/statistics', {
            method: 'GET'
        });
        
        if (response.success) {
            document.getElementById('totalKeys').textContent = response.statistics.total_keys;
            document.getElementById('totalCerts').textContent = response.statistics.total_certificates;
            document.getElementById('expiringSoon').textContent = response.statistics.expiring_certificates;
        }
    } catch (error) {
        console.error('Failed to load statistics:', error);
    }
}

// ============== KEY FUNCTIONS ==============

// Generate new key
async function handleGenerateKey(event) {
    event.preventDefault();
    
    const keyName = document.getElementById('keyName').value;
    const keyType = document.getElementById('keyType').value;
    const keySize = parseInt(document.getElementById('keySize').value);
    const button = event.target.querySelector('button[type="submit"]');
    
    setLoading(button, true);
    
    try {
        const response = await apiRequest('/keyvault/keys/generate', {
            method: 'POST',
            body: JSON.stringify({
                key_name: keyName,
                key_type: keyType,
                key_size: keySize,
                metadata: {
                    created_from: 'web_ui',
                    purpose: 'user_generated'
                }
            })
        });
        
        if (response.success) {
            alert(`✅ Key "${keyName}" generated successfully!`);
            event.target.reset();
            await loadKeys();
            await loadStatistics();
        }
    } catch (error) {
        alert('❌ Failed to generate key: ' + error.message);
    } finally {
        setLoading(button, false);
    }
}

// Load keys
async function loadKeys() {
    try {
        const response = await apiRequest('/keyvault/keys', {
            method: 'GET'
        });
        
        if (response.success) {
            displayKeys(response.keys);
        }
    } catch (error) {
        console.error('Failed to load keys:', error);
        document.getElementById('keysList').innerHTML = '<p style="color: #dc2626;">Failed to load keys</p>';
    }
}

// Display keys
function displayKeys(keys) {
    const container = document.getElementById('keysList');
    
    if (keys.length === 0) {
        container.innerHTML = '<p style="color: #6b7280; padding: 20px; text-align: center;">No keys generated yet</p>';
        return;
    }
    
    let html = '<div style="display: flex; flex-direction: column; gap: 12px;">';
    
    keys.forEach(key => {
        const statusColor = key.is_enabled ? '#16a34a' : '#dc2626';
        const statusText = key.is_enabled ? 'Enabled' : 'Disabled';
        
        html += `
            <div style="border: 1px solid #e5e7eb; padding: 16px; border-radius: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <div style="font-weight: 600; color: #111827; margin-bottom: 4px;">
                            🔑 ${key.key_name}
                        </div>
                        <div style="font-size: 13px; color: #6b7280;">
                            Type: ${key.key_type} | Size: ${key.key_size} bits | Version: ${key.version}
                        </div>
                        <div style="font-size: 12px; color: #6b7280; margin-top: 4px;">
                            Created: ${new Date(key.created_at).toLocaleString()}
                        </div>
                        <span style="font-size: 12px; color: ${statusColor}; font-weight: 600;">● ${statusText}</span>
                    </div>
                    <div style="display: flex; flex-wrap: wrap; gap: 8px; justify-content: flex-end;">
                        <button onclick="viewKey('${key.key_id}')" class="btn btn-secondary btn-sm">View</button>
                        <button onclick="downloadKey('${key.key_id}', false)" class="btn btn-secondary btn-sm" title="Download Public Key">📥 Public</button>
                        <button onclick="downloadKey('${key.key_id}', true)" class="btn btn-secondary btn-sm" style="background: #fef3c7;" title="Download Private Key">📥 Private</button>
                        <button onclick="openEmailModal('key', '${key.key_id}', '${key.key_name}')" class="btn btn-secondary btn-sm" title="Send via Email">📧</button>
                        <button onclick="rotateKey('${key.key_id}')" class="btn btn-secondary btn-sm">🔄 Rotate</button>
                        <button onclick="deleteKey('${key.key_id}')" class="btn btn-secondary btn-sm" style="background: #fee2e2; color: #dc2626;">🗑️</button>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

// View key details
async function viewKey(keyId) {
    try {
        const response = await apiRequest(`/keyvault/keys/${keyId}`, {
            method: 'GET'
        });
        
        if (response.success) {
            const key = response.key;
            
            let html = `
                <div style="line-height: 1.8;">
                    <div style="margin-bottom: 16px;">
                        <strong>Key Name:</strong> ${key.key_name}
                    </div>
                    <div style="margin-bottom: 16px;">
                        <strong>Key ID:</strong> <code>${key.key_id}</code>
                    </div>
                    <div style="margin-bottom: 16px;">
                        <strong>Type:</strong> ${key.key_type}
                    </div>
                    <div style="margin-bottom: 16px;">
                        <strong>Size:</strong> ${key.key_size} bits
                    </div>
                    <div style="margin-bottom: 16px;">
                        <strong>Version:</strong> ${key.version}
                    </div>
                    <div style="margin-bottom: 16px;">
                        <strong>Status:</strong> ${key.is_enabled ? '✅ Enabled' : '❌ Disabled'}
                    </div>
                    <div style="margin-bottom: 16px;">
                        <strong>Created:</strong> ${new Date(key.created_at).toLocaleString()}
                    </div>
            `;
            
            if (key.last_rotated) {
                html += `
                    <div style="margin-bottom: 16px;">
                        <strong>Last Rotated:</strong> ${new Date(key.last_rotated).toLocaleString()}
                    </div>
                `;
            }
            
            if (key.public_key) {
                html += `
                    <div style="margin-bottom: 16px;">
                        <strong>Public Key:</strong>
                        <textarea readonly style="width: 100%; height: 150px; margin-top: 8px; font-family: monospace; font-size: 11px;">${atob(key.public_key)}</textarea>
                    </div>
                `;
            }
            
            html += `
                <div style="display: flex; gap: 10px; margin-top: 20px;">
                    <button onclick="downloadKey('${key.key_id}', false)" class="btn btn-primary">📥 Download Public Key</button>
                    <button onclick="downloadKey('${key.key_id}', true)" class="btn btn-secondary">📥 Download Private Key</button>
                </div>
            </div>`;
            
            document.getElementById('keyModalContent').innerHTML = html;
            document.getElementById('keyModal').style.display = 'flex';
        }
    } catch (error) {
        alert('Failed to load key details: ' + error.message);
    }
}

// Download key
async function downloadKey(keyId, includePrivate = false) {
    try {
        const token = Storage.getToken();
        const response = await fetch(`${API_BASE_URL}/keyvault/keys/${keyId}/download?include_private=${includePrivate}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Download failed');
        }
        
        const blob = await response.blob();
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = includePrivate ? 'private_key.pem' : 'public_key.pem';
        
        if (contentDisposition) {
            const match = contentDisposition.match(/filename=(.+)/);
            if (match) filename = match[1];
        }
        
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
    } catch (error) {
        alert('❌ Download failed: ' + error.message);
    }
}

// Rotate key
async function rotateKey(keyId) {
    if (!confirm('Are you sure you want to rotate this key? This will create a new version.')) {
        return;
    }
    
    try {
        const response = await apiRequest(`/keyvault/keys/${keyId}/rotate`, {
            method: 'POST'
        });
        
        if (response.success) {
            alert(`✅ Key rotated successfully!\nOld Version: ${response.rotation.old_version}\nNew Version: ${response.rotation.new_version}`);
            await loadKeys();
        }
    } catch (error) {
        alert('❌ Failed to rotate key: ' + error.message);
    }
}

// Delete key
async function deleteKey(keyId) {
    if (!confirm('Are you sure you want to delete this key? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await apiRequest(`/keyvault/keys/${keyId}`, {
            method: 'DELETE'
        });
        
        if (response.success) {
            alert('✅ Key deleted successfully!');
            await loadKeys();
            await loadStatistics();
        }
    } catch (error) {
        alert('❌ Failed to delete key: ' + error.message);
    }
}

// ============== CERTIFICATE FUNCTIONS ==============

// Generate certificate
async function handleGenerateCertificate(event) {
    event.preventDefault();
    
    const certName = document.getElementById('certName').value;
    const commonName = document.getElementById('commonName').value;
    const validityDays = parseInt(document.getElementById('validityDays').value);
    const button = event.target.querySelector('button[type="submit"]');
    
    setLoading(button, true);
    
    try {
        const response = await apiRequest('/keyvault/certificates/generate', {
            method: 'POST',
            body: JSON.stringify({
                cert_name: certName,
                common_name: commonName,
                validity_days: validityDays,
                metadata: {
                    created_from: 'web_ui'
                }
            })
        });
        
        if (response.success) {
            alert(`✅ Certificate "${certName}" generated successfully!`);
            event.target.reset();
            await loadCertificates();
            await loadStatistics();
        }
    } catch (error) {
        alert('❌ Failed to generate certificate: ' + error.message);
    } finally {
        setLoading(button, false);
    }
}

// Load certificates
async function loadCertificates() {
    try {
        const response = await apiRequest('/keyvault/certificates', {
            method: 'GET'
        });
        
        if (response.success) {
            displayCertificates(response.certificates);
        }
    } catch (error) {
        console.error('Failed to load certificates:', error);
        document.getElementById('certsList').innerHTML = '<p style="color: #dc2626;">Failed to load certificates</p>';
    }
}

// Display certificates
function displayCertificates(certs) {
    const container = document.getElementById('certsList');
    
    if (certs.length === 0) {
        container.innerHTML = '<p style="color: #6b7280; padding: 20px; text-align: center;">No certificates generated yet</p>';
        return;
    }
    
    let html = '<div style="display: flex; flex-direction: column; gap: 12px;">';
    
    certs.forEach(cert => {
        const now = new Date();
        const notAfter = new Date(cert.not_after);
        const daysLeft = Math.floor((notAfter - now) / (1000 * 60 * 60 * 24));
        const isExpiringSoon = daysLeft <= 30 && daysLeft >= 0;
        const isExpired = daysLeft < 0;
        
        let statusColor = '#16a34a';
        let statusText = `Valid (${daysLeft} days left)`;
        
        if (isExpired) {
            statusColor = '#dc2626';
            statusText = 'Expired';
        } else if (isExpiringSoon) {
            statusColor = '#f59e0b';
            statusText = `Expiring Soon (${daysLeft} days)`;
        }
        
        html += `
            <div style="border: 1px solid #e5e7eb; padding: 16px; border-radius: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <div style="font-weight: 600; color: #111827; margin-bottom: 4px;">
                            📜 ${cert.cert_name}
                        </div>
                        <div style="font-size: 13px; color: #6b7280;">
                            Common Name: ${cert.common_name}
                        </div>
                        <div style="font-size: 12px; color: #6b7280; margin-top: 4px;">
                            Serial: ${cert.serial_number}
                        </div>
                        <div style="font-size: 12px; color: #6b7280;">
                            Valid: ${new Date(cert.not_before).toLocaleDateString()} - ${new Date(cert.not_after).toLocaleDateString()}
                        </div>
                        <span style="font-size: 12px; color: ${statusColor}; font-weight: 600; margin-top: 8px; display: inline-block;">
                            ● ${statusText}
                        </span>
                    </div>
                    <div style="display: flex; flex-wrap: wrap; gap: 8px; justify-content: flex-end;">
                        <button onclick="validateCertificate('${cert.cert_id}')" class="btn btn-secondary btn-sm">✓ Validate</button>
                        <button onclick="viewCertificate('${cert.cert_id}')" class="btn btn-secondary btn-sm">View</button>
                        <button onclick="downloadCertificate('${cert.cert_id}', false)" class="btn btn-secondary btn-sm" title="Download Certificate">📥 Cert</button>
                        <button onclick="downloadCertificate('${cert.cert_id}', true)" class="btn btn-secondary btn-sm" style="background: #fef3c7;" title="Download with Private Key">📥 Bundle</button>
                        <button onclick="openEmailModal('cert', '${cert.cert_id}', '${cert.cert_name}')" class="btn btn-secondary btn-sm" title="Send via Email">📧</button>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

// Validate certificate
async function validateCertificate(certId) {
    try {
        const response = await apiRequest(`/keyvault/certificates/${certId}/validate`, {
            method: 'POST'
        });
        
        if (response.success) {
            const validation = response.validation;
            
            if (validation.valid) {
                alert(`✅ Certificate is valid!\n\nDays until expiry: ${validation.days_until_expiry}\nExpires: ${new Date(validation.expires_at).toLocaleString()}\n${validation.needs_renewal ? '\n⚠️ Certificate needs renewal soon!' : ''}`);
            } else {
                alert(`❌ Certificate is invalid!\n\nReason: ${validation.reason}`);
            }
        }
    } catch (error) {
        alert('Failed to validate certificate: ' + error.message);
    }
}

// View certificate
async function viewCertificate(certId) {
    try {
        const response = await apiRequest('/keyvault/certificates', {
            method: 'GET'
        });
        
        if (response.success) {
            const cert = response.certificates.find(c => c.cert_id === certId);
            
            if (cert) {
                let html = `
                    <div style="line-height: 1.8;">
                        <div style="margin-bottom: 16px;">
                            <strong>Certificate Name:</strong> ${cert.cert_name}
                        </div>
                        <div style="margin-bottom: 16px;">
                            <strong>Certificate ID:</strong> <code>${cert.cert_id}</code>
                        </div>
                        <div style="margin-bottom: 16px;">
                            <strong>Common Name:</strong> ${cert.common_name}
                        </div>
                        <div style="margin-bottom: 16px;">
                            <strong>Serial Number:</strong> ${cert.serial_number}
                        </div>
                        <div style="margin-bottom: 16px;">
                            <strong>Certificate (PEM):</strong>
                            <textarea readonly style="width: 100%; height: 200px; margin-top: 8px; font-family: monospace; font-size: 11px;">${atob(cert.certificate)}</textarea>
                        </div>
                        <div style="display: flex; gap: 10px; margin-top: 20px;">
                            <button onclick="downloadCertificate('${cert.cert_id}', false)" class="btn btn-primary">
                                📥 Download Certificate
                            </button>
                            <button onclick="downloadCertificate('${cert.cert_id}', true)" class="btn btn-secondary">
                                📥 Download Bundle (with Key)
                            </button>
                        </div>
                    </div>
                `;
                
                document.getElementById('keyModalContent').innerHTML = html;
                document.getElementById('keyModal').style.display = 'flex';
            }
        }
    } catch (error) {
        alert('Failed to load certificate: ' + error.message);
    }
}

// Download certificate (new API endpoint)
async function downloadCertificate(certId, includePrivateKey = false) {
    try {
        const token = Storage.getToken();
        const response = await fetch(`${API_BASE_URL}/keyvault/certificates/${certId}/download?include_private_key=${includePrivateKey}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Download failed');
        }
        
        const blob = await response.blob();
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = includePrivateKey ? 'certificate_bundle.pem' : 'certificate.pem';
        
        if (contentDisposition) {
            const match = contentDisposition.match(/filename=(.+)/);
            if (match) filename = match[1];
        }
        
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
    } catch (error) {
        alert('❌ Download failed: ' + error.message);
    }
}

// ============== EMAIL FUNCTIONS ==============

let currentEmailTarget = { type: null, id: null, name: null };

// Open email modal
function openEmailModal(type, id, name) {
    currentEmailTarget = { type, id, name };
    
    const title = type === 'key' ? `Send Key: ${name}` : `Send Certificate: ${name}`;
    document.getElementById('emailModalTitle').textContent = title;
    document.getElementById('emailRecipient').value = '';
    document.getElementById('emailMessage').value = '';
    document.getElementById('emailIncludePrivate').checked = false;
    document.getElementById('emailModal').style.display = 'flex';
}

// Close email modal
function closeEmailModal() {
    document.getElementById('emailModal').style.display = 'none';
    currentEmailTarget = { type: null, id: null, name: null };
}

// Send email
async function handleSendEmail(event) {
    event.preventDefault();
    
    const recipient = document.getElementById('emailRecipient').value;
    const message = document.getElementById('emailMessage').value;
    const includePrivate = document.getElementById('emailIncludePrivate').checked;
    const button = event.target.querySelector('button[type="submit"]');
    
    if (!currentEmailTarget.type || !currentEmailTarget.id) {
        alert('❌ No item selected');
        return;
    }
    
    setLoading(button, true);
    
    try {
        const endpoint = currentEmailTarget.type === 'key' 
            ? `/keyvault/keys/${currentEmailTarget.id}/send-email`
            : `/keyvault/certificates/${currentEmailTarget.id}/send-email`;
        
        const body = {
            recipient_email: recipient,
            include_private_key: includePrivate,
            message: message || null
        };
        
        const response = await apiRequest(endpoint, {
            method: 'POST',
            body: JSON.stringify(body)
        });
        
        if (response.success) {
            alert(`✅ ${currentEmailTarget.type === 'key' ? 'Key' : 'Certificate'} sent to ${recipient}!`);
            closeEmailModal();
        }
    } catch (error) {
        alert('❌ Failed to send email: ' + error.message);
    } finally {
        setLoading(button, false);
    }
}

// Close key modal
function closeKeyModal() {
    document.getElementById('keyModal').style.display = 'none';
}

// Close modals on outside click
window.onclick = function(event) {
    const keyModal = document.getElementById('keyModal');
    const emailModal = document.getElementById('emailModal');
    
    if (event.target === keyModal) {
        closeKeyModal();
    }
    if (event.target === emailModal) {
        closeEmailModal();
    }
}

// Make functions globally available
window.switchTab = switchTab;
window.handleGenerateKey = handleGenerateKey;
window.handleGenerateCertificate = handleGenerateCertificate;
window.viewKey = viewKey;
window.closeKeyModal = closeKeyModal;
window.rotateKey = rotateKey;
window.deleteKey = deleteKey;
window.downloadKey = downloadKey;
window.validateCertificate = validateCertificate;
window.viewCertificate = viewCertificate;
window.downloadCertificate = downloadCertificate;
window.openEmailModal = openEmailModal;
window.closeEmailModal = closeEmailModal;
window.handleSendEmail = handleSendEmail;