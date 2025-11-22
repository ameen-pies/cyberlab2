// Check authentication
if (!Storage.getToken()) {
    window.location.href = 'index.html';
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    await loadStatistics();
    await loadPolicies();
    await loadAnalytics();
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
    
    if (tabName === 'analytics') {
        loadAnalytics();
    }
}

// Toggle password visibility
function togglePasswordVisibility() {
    const input = document.getElementById('passwordInput');
    input.type = input.type === 'password' ? 'text' : 'password';
}

// Load statistics
async function loadStatistics() {
    try {
        const response = await apiRequest('/password-checker/analytics', {
            method: 'GET'
        });
        
        if (response.success) {
            const analytics = response.analytics;
            document.getElementById('totalChecks').textContent = analytics.total_checks;
            document.getElementById('avgScore').textContent = analytics.average_score;
            document.getElementById('breachedCount').textContent = analytics.breached_count;
        }
    } catch (error) {
        console.error('Failed to load statistics:', error);
    }
}

// Analyze password
async function handlePasswordAnalyze(event) {
    event.preventDefault();
    
    const password = document.getElementById('passwordInput').value;
    const checkBreaches = document.getElementById('checkBreaches').checked;
    const button = event.target.querySelector('button[type="submit"]');
    
    setLoading(button, true);
    
    try {
        const response = await apiRequest('/password-checker/analyze', {
            method: 'POST',
            body: JSON.stringify({
                password: password,
                check_breaches: checkBreaches
            })
        });
        
        if (response.success) {
            displayResults(response);
            await loadStatistics();
        }
    } catch (error) {
        alert('❌ Analysis failed: ' + error.message);
    } finally {
        setLoading(button, false);
    }
}

// Display results
function displayResults(data) {
    const container = document.getElementById('resultsContainer');
    container.style.display = 'block';
    
    // Score
    const score = data.score.score;
    const rating = data.score.rating;
    const color = data.score.color;
    
    document.getElementById('scoreValue').textContent = score;
    document.getElementById('scoreValue').style.color = color;
    document.getElementById('scoreRating').textContent = rating.replace('_', ' ').toUpperCase();
    document.getElementById('scoreRating').style.color = color;
    document.getElementById('scoreBar').style.width = `${score}%`;
    document.getElementById('scoreBar').style.background = color;
    
    // Entropy
    document.getElementById('entropyValue').textContent = data.entropy.toFixed(2);
    
    // Crack time
    document.getElementById('crackValue').textContent = data.crack_time.value;
    document.getElementById('crackUnit').textContent = data.crack_time.unit;
    
    // Length
    document.getElementById('lengthValue').textContent = data.length;
    
    // Policy checks
    const policyChecks = data.policy_checks;
    let policyHtml = '<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;">';
    
    const policyLabels = {
        length: 'Minimum Length',
        uppercase: 'Uppercase Letters',
        lowercase: 'Lowercase Letters',
        digits: 'Digits',
        special: 'Special Characters',
        repeating: 'No Repeating',
        common: 'Not Common Password'
    };
    
    for (const [key, passed] of Object.entries(policyChecks)) {
        const icon = passed ? '✅' : '❌';
        const textColor = passed ? '#16a34a' : '#dc2626';
        
        policyHtml += `
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 20px;">${icon}</span>
                <span style="color: ${textColor}; font-weight: 500;">${policyLabels[key]}</span>
            </div>
        `;
    }
    
    policyHtml += '</div>';
    document.getElementById('policyChecks').innerHTML = policyHtml;
    
    // Breach info
    const breachInfo = data.breach_info;
    const breachCard = document.getElementById('breachCard');
    
    if (breachInfo.checked) {
        breachCard.style.display = 'block';
        
        if (breachInfo.breached) {
            document.getElementById('breachInfo').innerHTML = `
                <div style="background: #fee2e2; padding: 16px; border-radius: 8px; border-left: 4px solid #dc2626;">
                    <div style="color: #dc2626; font-weight: 600; margin-bottom: 8px;">
                        ⚠️ PASSWORD COMPROMISED!
                    </div>
                    <div style="color: #991b1b;">
                        This password has been found in <strong>${breachInfo.count.toLocaleString()}</strong> data breaches.
                        <br><br>
                        <strong>Action Required:</strong> Do NOT use this password. It is publicly known and extremely vulnerable.
                    </div>
                </div>
            `;
        } else {
            document.getElementById('breachInfo').innerHTML = `
                <div style="background: #dcfce7; padding: 16px; border-radius: 8px; border-left: 4px solid #16a34a;">
                    <div style="color: #16a34a; font-weight: 600; margin-bottom: 8px;">
                        ✅ No Breaches Found
                    </div>
                    <div style="color: #15803d;">
                        This password has not been found in known data breaches.
                    </div>
                </div>
            `;
        }
    } else {
        breachCard.style.display = 'none';
    }
    
    // Suggestions
    const suggestions = data.suggestions;
    let suggestionsHtml = '';
    
    if (suggestions.length === 0) {
        suggestionsHtml = '<li style="color: #16a34a;">✅ Your password meets all requirements! Great job!</li>';
    } else {
        suggestions.forEach(suggestion => {
            suggestionsHtml += `<li>${suggestion}</li>`;
        });
    }
    
    document.getElementById('suggestionsList').innerHTML = suggestionsHtml;
    
    // Scroll to results
    container.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Save custom policy
async function handleSavePolicy(event) {
    event.preventDefault();
    
    const policyName = document.getElementById('policyName').value;
    const button = event.target.querySelector('button[type="submit"]');
    
    const policy = {
        min_length: parseInt(document.getElementById('policyMinLength').value),
        require_uppercase: document.getElementById('policyUppercase').checked,
        require_lowercase: document.getElementById('policyLowercase').checked,
        require_digits: document.getElementById('policyDigits').checked,
        require_special: document.getElementById('policySpecial').checked,
        max_repeating: parseInt(document.getElementById('policyMaxRepeat').value),
        block_common: document.getElementById('policyBlockCommon').checked
    };
    
    setLoading(button, true);
    
    try {
        const response = await apiRequest('/password-checker/policies', {
            method: 'POST',
            body: JSON.stringify({
                policy_name: policyName,
                policy: policy
            })
        });
        
        if (response.success) {
            alert(`✅ Policy "${policyName}" saved successfully!`);
            event.target.reset();
            await loadPolicies();
        }
    } catch (error) {
        alert('❌ Failed to save policy: ' + error.message);
    } finally {
        setLoading(button, false);
    }
}

// Load policies
async function loadPolicies() {
    try {
        const response = await apiRequest('/password-checker/policies', {
            method: 'GET'
        });
        
        if (response.success) {
            displayPolicies(response.policies);
        }
    } catch (error) {
        console.error('Failed to load policies:', error);
    }
}

// Display policies
function displayPolicies(policies) {
    const container = document.getElementById('policiesList');
    
    if (policies.length === 0) {
        container.innerHTML = '<p style="color: #6b7280; padding: 20px; text-align: center;">No custom policies created yet</p>';
        return;
    }
    
    let html = '<div style="display: flex; flex-direction: column; gap: 12px;">';
    
    policies.forEach(policy => {
        html += `
            <div style="border: 1px solid #e5e7eb; padding: 16px; border-radius: 8px;">
                <div style="font-weight: 600; color: #111827; margin-bottom: 8px;">
                    📋 ${policy.policy_name}
                </div>
                <div style="font-size: 13px; color: #6b7280;">
                    Min Length: ${policy.policy.min_length} | 
                    Uppercase: ${policy.policy.require_uppercase ? '✅' : '❌'} | 
                    Lowercase: ${policy.policy.require_lowercase ? '✅' : '❌'} | 
                    Digits: ${policy.policy.require_digits ? '✅' : '❌'} | 
                    Special: ${policy.policy.require_special ? '✅' : '❌'}
                </div>
                <div style="font-size: 12px; color: #6b7280; margin-top: 4px;">
                    Created: ${new Date(policy.created_at).toLocaleString()}
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

// Load analytics
async function loadAnalytics() {
    try {
        const response = await apiRequest('/password-checker/analytics', {
            method: 'GET'
        });
        
        if (response.success) {
            displayAnalytics(response.analytics);
        }
    } catch (error) {
        console.error('Failed to load analytics:', error);
    }
}

// Display analytics
function displayAnalytics(analytics) {
    const container = document.getElementById('analyticsContent');
    
    if (analytics.total_checks === 0) {
        container.innerHTML = '<p style="color: #6b7280; padding: 20px; text-align: center;">No password checks yet. Analyze some passwords to see statistics!</p>';
        return;
    }
    
    let html = `
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin: 20px 0;">
            <div>
                <div style="font-size: 14px; color: #6b7280; margin-bottom: 4px;">Total Checks</div>
                <div style="font-size: 32px; font-weight: bold; color: #111827;">${analytics.total_checks}</div>
            </div>
            <div>
                <div style="font-size: 14px; color: #6b7280; margin-bottom: 4px;">Average Score</div>
                <div style="font-size: 32px; font-weight: bold; color: #111827;">${analytics.average_score}/100</div>
            </div>
            <div>
                <div style="font-size: 14px; color: #6b7280; margin-bottom: 4px;">Breached Passwords</div>
                <div style="font-size: 32px; font-weight: bold; color: #dc2626;">${analytics.breached_count}</div>
            </div>
            <div>
                <div style="font-size: 14px; color: #6b7280; margin-bottom: 4px;">Breach Rate</div>
                <div style="font-size: 32px; font-weight: bold; color: #dc2626;">${analytics.breach_percentage}%</div>
            </div>
        </div>
        
        <div style="margin-top: 30px;">
            <h4 style="color: #111827; margin-bottom: 16px;">Rating Distribution</h4>
            <div style="display: flex; flex-direction: column; gap: 12px;">
    `;
    
    const ratingColors = {
        'very_strong': '#16a34a',
        'strong': '#65a30d',
        'fair': '#f59e0b',
        'weak': '#f97316',
        'very_weak': '#dc2626'
    };
    
    const ratingLabels = {
        'very_strong': 'Very Strong',
        'strong': 'Strong',
        'fair': 'Fair',
        'weak': 'Weak',
        'very_weak': 'Very Weak'
    };
    
    for (const [rating, count] of Object.entries(analytics.rating_distribution)) {
        const percentage = (count / analytics.total_checks * 100).toFixed(1);
        const color = ratingColors[rating] || '#6b7280';
        
        html += `
            <div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span style="color: #374151;">${ratingLabels[rating]}</span>
                    <span style="color: #6b7280;">${count} (${percentage}%)</span>
                </div>
                <div style="width: 100%; height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden;">
                    <div style="width: ${percentage}%; height: 100%; background: ${color}; transition: width 0.3s ease;"></div>
                </div>
            </div>
        `;
    }
    
    html += '</div></div>';
    container.innerHTML = html;
    
    // Recent checks
    displayRecentChecks(analytics.recent_checks);
}

// Display recent checks
function displayRecentChecks(checks) {
    const container = document.getElementById('recentChecks');
    
    if (!checks || checks.length === 0) {
        container.innerHTML = '<p style="color: #6b7280; padding: 20px; text-align: center;">No recent checks</p>';
        return;
    }
    
    let html = '<div style="display: flex; flex-direction: column; gap: 12px;">';
    
    checks.forEach(check => {
        const ratingColors = {
            'very_strong': '#16a34a',
            'strong': '#65a30d',
            'fair': '#f59e0b',
            'weak': '#f97316',
            'very_weak': '#dc2626'
        };
        
        const color = ratingColors[check.rating] || '#6b7280';
        
        html += `
            <div style="border: 1px solid #e5e7eb; padding: 16px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="font-weight: 600; color: ${color};">
                        Score: ${check.score}/100 (${check.rating.replace('_', ' ').toUpperCase()})
                    </div>
                    <div style="font-size: 13px; color: #6b7280; margin-top: 4px;">
                        Length: ${check.password_length} | Entropy: ${check.entropy} bits
                        ${check.breached ? ' | 🚨 <span style="color: #dc2626; font-weight: 600;">BREACHED</span>' : ''}
                    </div>
                    <div style="font-size: 12px; color: #6b7280; margin-top: 4px;">
                        ${new Date(check.analyzed_at).toLocaleString()}
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

// Make functions globally available
window.switchTab = switchTab;
window.togglePasswordVisibility = togglePasswordVisibility;
window.handlePasswordAnalyze = handlePasswordAnalyze;
window.handleSavePolicy = handleSavePolicy;