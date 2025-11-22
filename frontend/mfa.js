// Check if user came from login
const userEmail = sessionStorage.getItem('mfa_email');
if (!userEmail) {
    window.location.href = 'index.html';
}

// Display user email
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('userEmail').textContent = userEmail;
    document.getElementById('digit1').focus();
});

// Handle MFA input
function handleMfaInput(input, position) {
    input.value = input.value.replace(/[^0-9]/g, '');
    
    if (input.value.length === 1 && position < 6) {
        document.getElementById(`digit${position + 1}`).focus();
    }
    
    if (position === 6 && input.value.length === 1) {
        const code = getMfaCode();
        if (code.length === 6) {
            setTimeout(() => {
                const form = document.getElementById('mfaForm');
                if (form) {
                    const submitEvent = new Event('submit', { bubbles: true, cancelable: true });
                    form.dispatchEvent(submitEvent);
                }
            }, 100);
        }
    }
}

// Handle backspace/delete
function handleMfaKeydown(event, position) {
    if (event.key === 'Backspace' || event.key === 'Delete') {
        const currentInput = document.getElementById(`digit${position}`);
        
        if (currentInput.value === '' && position > 1) {
            event.preventDefault();
            const prevInput = document.getElementById(`digit${position - 1}`);
            prevInput.value = '';
            prevInput.focus();
        }
    }
    
    if (event.key === 'ArrowLeft' && position > 1) {
        event.preventDefault();
        document.getElementById(`digit${position - 1}`).focus();
    }
    
    if (event.key === 'ArrowRight' && position < 6) {
        event.preventDefault();
        document.getElementById(`digit${position + 1}`).focus();
    }
}

// Get complete MFA code
function getMfaCode() {
    let code = '';
    for (let i = 1; i <= 6; i++) {
        code += document.getElementById(`digit${i}`).value;
    }
    return code;
}

// Clear MFA inputs
function clearMfaInputs() {
    for (let i = 1; i <= 6; i++) {
        document.getElementById(`digit${i}`).value = '';
    }
    document.getElementById('digit1').focus();
}

// Handle MFA verification
async function handleMfaVerify(event) {
    event.preventDefault();
    
    const code = getMfaCode();
    const button = event.target.querySelector('button[type="submit"]');
    
    if (code.length !== 6) {
        showError('mfaError', 'Please enter a complete 6-digit code');
        return;
    }
    
    setLoading(button, true);
    document.getElementById('mfaError').classList.remove('show');
    
    try {
        console.log('🔐 Verifying MFA code...');
        
        const response = await apiRequest(API_CONFIG.ENDPOINTS.MFA_VERIFY, {
            method: 'POST',
            skipAuth: true,
            body: JSON.stringify({
                email: userEmail,
                code: code
            })
        });
        
        console.log('✅ MFA verified, got token');
        
        if (response.access_token) {
            // ✅ Store token FIRST
            Storage.setToken(response.access_token);
            
            console.log('🔍 Fetching user permissions...');
            
            // ✅ NOW fetch user permissions with the token
            try {
                const userInfo = await apiRequest('/users/permissions', {
                    method: 'GET'
                });
                
                console.log('✅ User info received:', userInfo);
                console.log('✅ Role:', userInfo.role);
                console.log('✅ Permissions:', userInfo.permissions);
                
                // ✅ Store complete user data with ALL fields
                Storage.setUser({ 
                    email: userInfo.email,
                    full_name: userInfo.full_name || userEmail.split('@')[0],
                    role: userInfo.role,
                    permissions: userInfo.permissions
                });
                
                console.log('💾 User data stored successfully');
                console.log('💾 Stored role:', userInfo.role);
                
            } catch (permError) {
                console.error('❌ Failed to fetch permissions:', permError);
                console.error('❌ Error details:', permError.message);
                
                // ✅ Fallback: store basic user data
                Storage.setUser({ 
                    email: userEmail,
                    full_name: userEmail.split('@')[0],
                    role: 'normal',
                    permissions: []
                });
                
                console.warn('⚠️ Using fallback user data');
            }
            
            // Clear session
            sessionStorage.removeItem('mfa_email');
            
            // Show success
            showSuccess('mfaSuccess', 'Verification successful! Redirecting...');
            
            // Redirect to dashboard
            setTimeout(() => {
                window.location.href = 'dashboard.html';
            }, 1000);
        }
    } catch (error) {
        console.error('❌ MFA verification failed:', error);
        showError('mfaError', error.message || 'Invalid or expired code. Please try again.');
        clearMfaInputs();
    } finally {
        setLoading(button, false);
    }
}

// Resend MFA code
async function resendMfaCode() {
    const resendBtn = event.target;
    const originalText = resendBtn.textContent;
    resendBtn.textContent = 'Sending...';
    resendBtn.style.pointerEvents = 'none';
    
    try {
        await apiRequest(API_CONFIG.ENDPOINTS.MFA_SEND, {
            method: 'POST',
            skipAuth: true,
            body: JSON.stringify({ email: userEmail })
        });
        
        showSuccess('mfaSuccess', 'New code sent to your email!');
        clearMfaInputs();
        
        let countdown = 30;
        resendBtn.textContent = `Resend (${countdown}s)`;
        
        const interval = setInterval(() => {
            countdown--;
            if (countdown > 0) {
                resendBtn.textContent = `Resend (${countdown}s)`;
            } else {
                clearInterval(interval);
                resendBtn.textContent = originalText;
                resendBtn.style.pointerEvents = 'auto';
            }
        }, 1000);
        
    } catch (error) {
        showError('mfaError', 'Failed to resend code. Please try again.');
        resendBtn.textContent = originalText;
        resendBtn.style.pointerEvents = 'auto';
    }
}

// Make functions globally available
window.handleMfaInput = handleMfaInput;
window.handleMfaKeydown = handleMfaKeydown;
window.handleMfaVerify = handleMfaVerify;
window.resendMfaCode = resendMfaCode;