// Check authentication
if (!Storage.getToken()) {
    window.location.href = 'index.html';
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    await loadStatistics();
});

// Switch tabs
function switchTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab content
    document.getElementById(`${tabName}Tab`).classList.add('active');
    
    // Add active class to clicked tab button
    event.target.classList.add('active');
}

// Load statistics
async function loadStatistics() {
    try {
        // For now, use mock data since API might not be implemented
        console.log('Loading statistics...');
        
        // Mock statistics data
        const mockStats = {
            total_scans: 1,
            total_secrets_found: 0,
            severity_breakdown: {
                critical: 0,
                high: 0,
                medium: 0,
                low: 0
            }
        };
        
        document.getElementById('totalScans').textContent = mockStats.total_scans;
        document.getElementById('totalSecrets').textContent = mockStats.total_secrets_found;
        
    } catch (error) {
        console.error('Failed to load statistics:', error);
        // Set default values
        document.getElementById('totalScans').textContent = '0';
        document.getElementById('totalSecrets').textContent = '0';
    }
}

// Scan text
async function handleTextScan(event) {
    event.preventDefault();
    console.log('Starting text scan...');
    
    const text = document.getElementById('textInput').value;
    const button = event.target.querySelector('button[type="submit"]');
    
    if (!text.trim()) {
        alert('Please enter some text to scan');
        return;
    }
    
    // Store original button text
    const originalText = button.innerHTML;
    button.setAttribute('data-original-text', originalText);
    setLoading(button, true);
    
    try {
        // Mock scan response for now
        console.log('Scanning text:', text.substring(0, 100) + '...');
        
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        // Mock response based on common patterns
        const mockResponse = generateMockScanResponse(text);
        
        displayScanResults(mockResponse, 'textResults');
        await loadStatistics();
        
    } catch (error) {
        console.error('Scan failed:', error);
        alert('❌ Scan failed: ' + (error.message || 'Unknown error'));
    } finally {
        setLoading(button, false);
    }
}

// Scan file
async function handleFileScan(event) {
    event.preventDefault();
    console.log('Starting file scan...');
    
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    const button = event.target.querySelector('button[type="submit"]');
    
    if (!file) {
        alert('Please select a file');
        return;
    }
    
    // Store original button text
    const originalText = button.innerHTML;
    button.setAttribute('data-original-text', originalText);
    setLoading(button, true);
    
    try {
        console.log('Scanning file:', file.name);
        
        // Read file content
        const fileContent = await readFileAsText(file);
        
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Mock response based on file content
        const mockResponse = generateMockScanResponse(fileContent);
        mockResponse.filename = file.name;
        
        displayScanResults(mockResponse, 'fileResults');
        await loadStatistics();
        
        // Reset file input
        fileInput.value = '';
        
    } catch (error) {
        console.error('File scan failed:', error);
        alert('❌ File scan failed: ' + (error.message || 'Unknown error'));
    } finally {
        setLoading(button, false);
    }
}

// Helper function to read file as text
function readFileAsText(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = e => resolve(e.target.result);
        reader.onerror = e => reject(new Error('Failed to read file'));
        reader.readAsText(file);
    });
}

// Generate mock scan response based on content
function generateMockScanResponse(content) {
    const findings = [];
    
    // Check for common secret patterns - ALL patterns now have 'g' flag for matchAll
    const patterns = [
        {
            name: "AWS Access Key",
            regex: /AKIA[0-9A-Z]{16}/g,
            severity: "critical"
        },
        {
            name: "AWS Secret Key",
            regex: /[A-Za-z0-9/+=]{40}/g,
            severity: "critical"
        },
        {
            name: "API Key",
            regex: /(api[_-]?key|apikey)[\s]*=[\s]*['"]([^'"]+)['"]/gi,
            severity: "high"
        },
        {
            name: "Password in code",
            regex: /(password|pwd|pass)[\s]*=[\s]*['"]([^'"]+)['"]/gi,
            severity: "high"
        },
        {
            name: "Private Key",
            regex: /-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----/g,
            severity: "critical"
        },
        {
            name: "JWT Token",
            regex: /eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9._-]*/g,
            severity: "medium"
        },
        {
            name: "Email Address",
            regex: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g,
            severity: "low"
        },
        {
            name: "IP Address",
            regex: /\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b/g,
            severity: "low"
        }
    ];
    
    const lines = content.split('\n');
    
    lines.forEach((line, index) => {
        patterns.forEach(pattern => {
            try {
                const matches = [...line.matchAll(pattern.regex)];
                matches.forEach(match => {
                    findings.push({
                        name: pattern.name,
                        value: match[0].substring(0, 50) + (match[0].length > 50 ? '...' : ''),
                        severity: pattern.severity,
                        line: index + 1,
                        position: {
                            start: match.index + 1,
                            end: match.index + match[0].length + 1
                        },
                        entropy: Math.random() * 8 + 2 // Random entropy between 2-10
                    });
                });
            } catch (error) {
                console.warn(`Error processing pattern ${pattern.name}:`, error);
            }
        });
    });
    
    // Calculate severity counts
    const severityCounts = {
        critical: findings.filter(f => f.severity === 'critical').length,
        high: findings.filter(f => f.severity === 'high').length,
        medium: findings.filter(f => f.severity === 'medium').length,
        low: findings.filter(f => f.severity === 'low').length
    };
    
    const totalFound = findings.length;
    
    // Generate report
    const report = `Secret Scanner Report
Generated: ${new Date().toISOString()}
Total Findings: ${totalFound}

Severity Breakdown:
- Critical: ${severityCounts.critical}
- High: ${severityCounts.high}
- Medium: ${severityCounts.medium}
- Low: ${severityCounts.low}

Findings:
${findings.map(f => `[${f.severity.toUpperCase()}] ${f.name} at line ${f.line}: ${f.value}`).join('\n')}
`;
    
    return {
        success: true,
        total_found: totalFound,
        severity_counts: severityCounts,
        findings: findings,
        report: report
    };
}

// Display scan results
function displayScanResults(data, containerId) {
    const container = document.getElementById(containerId);
    
    const totalFound = data.total_found || 0;
    const severityCounts = data.severity_counts || { critical: 0, high: 0, medium: 0, low: 0 };
    
    let html = `
        <div class="form-card" style="margin-top: 24px; border-left: 4px solid ${totalFound > 0 ? '#dc2626' : '#16a34a'};">
            <h3>🔍 Scan Results</h3>
            
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 20px 0;">
                <div style="text-align: center;">
                    <div style="font-size: 32px; font-weight: bold; color: ${totalFound > 0 ? '#dc2626' : '#16a34a'};">
                        ${totalFound}
                    </div>
                    <div style="font-size: 13px; color: #6b7280;">Total Found</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 32px; font-weight: bold; color: #dc2626;">
                        ${severityCounts.critical || 0}
                    </div>
                    <div style="font-size: 13px; color: #6b7280;">🔴 Critical</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 32px; font-weight: bold; color: #f97316;">
                        ${severityCounts.high || 0}
                    </div>
                    <div style="font-size: 13px; color: #6b7280;">🟠 High</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 32px; font-weight: bold; color: #f59e0b;">
                        ${severityCounts.medium || 0}
                    </div>
                    <div style="font-size: 13px; color: #6b7280;">🟡 Medium</div>
                </div>
            </div>
    `;
    
    if (totalFound === 0) {
        html += `
            <div style="background: #dcfce7; padding: 20px; border-radius: 8px; text-align: center;">
                <div style="font-size: 24px; margin-bottom: 8px;">✅</div>
                <div style="color: #16a34a; font-weight: 600;">No Secrets Detected!</div>
                <div style="color: #15803d; margin-top: 4px;">Your code appears to be clean.</div>
            </div>
        `;
    } else {
        html += `
            <div style="background: #fee2e2; padding: 16px; border-radius: 8px; margin-bottom: 20px;">
                <div style="color: #dc2626; font-weight: 600; margin-bottom: 4px;">
                    ⚠️ SECRETS DETECTED!
                </div>
                <div style="color: #991b1b;">
                    Found ${totalFound} exposed ${totalFound === 1 ? 'secret' : 'secrets'}. Review and rotate all compromised credentials immediately!
                </div>
            </div>
            
            <div style="margin-top: 20px;">
                <h4 style="color: #111827; margin-bottom: 16px;">Detailed Findings</h4>
                <div style="display: flex; flex-direction: column; gap: 12px;">
        `;
        
        data.findings.forEach((finding, index) => {
            const severityColors = {
                'critical': '#dc2626',
                'high': '#f97316',
                'medium': '#f59e0b',
                'low': '#16a34a'
            };
            
            const severityIcons = {
                'critical': '🔴',
                'high': '🟠',
                'medium': '🟡',
                'low': '🟢'
            };
            
            const color = severityColors[finding.severity] || '#6b7280';
            const icon = severityIcons[finding.severity] || '⚪';
            
            html += `
                <div style="border: 2px solid ${color}; padding: 16px; border-radius: 8px; background: white;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                        <div style="flex: 1;">
                            <div style="font-weight: 600; color: ${color}; margin-bottom: 4px;">
                                ${icon} ${finding.name}
                            </div>
                            <div style="font-size: 13px; color: #6b7280;">
                                Severity: <strong style="color: ${color};">${finding.severity.toUpperCase()}</strong> | 
                                Line: ${finding.line} | 
                                Position: ${finding.position.start}-${finding.position.end} |
                                Entropy: ${finding.entropy?.toFixed(2) || 'N/A'}
                            </div>
                        </div>
                    </div>
                    <div style="background: #f9fafb; padding: 12px; border-radius: 4px; margin-top: 12px;">
                        <div style="font-size: 12px; color: #6b7280; margin-bottom: 4px;">Detected Value:</div>
                        <code style="font-family: monospace; font-size: 13px; color: #111827; word-break: break-all;">
                            ${finding.value}
                        </code>
                    </div>
                    <div style="margin-top: 12px; padding: 12px; background: #fef3c7; border-radius: 4px;">
                        <div style="color: #92400e; font-size: 13px;">
                            <strong>⚠️ Action Required:</strong> Rotate this ${finding.name} immediately and never commit secrets to code.
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div></div>';
    }
    
    // Show report
    if (data.report) {
        html += `
            <div style="margin-top: 24px;">
                <h4 style="color: #111827; margin-bottom: 12px;">📋 Text Report</h4>
                <textarea readonly style="width: 100%; height: 200px; font-family: monospace; font-size: 12px; padding: 12px; border: 1px solid #e5e7eb; border-radius: 8px; background: #f9fafb;">${data.report}</textarea>
            </div>
        `;
    }
    
    html += '</div>';
    container.innerHTML = html;
    
    // Scroll to results
    container.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Set loading state for buttons
function setLoading(button, isLoading) {
    if (isLoading) {
        button.disabled = true;
        button.innerHTML = '⏳ Scanning...';
        button.style.opacity = '0.7';
    } else {
        button.disabled = false;
        const originalText = button.getAttribute('data-original-text') || 'Scan';
        button.innerHTML = originalText;
        button.style.opacity = '1';
    }
}

// Make functions globally available
window.switchTab = switchTab;
window.handleTextScan = handleTextScan;
window.handleFileScan = handleFileScan;