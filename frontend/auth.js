// Check if already logged in
if (Storage.getToken()) {
    window.location.href = 'dashboard.html';
}

// Switch between login and signup forms
function switchToSignup() {
    document.getElementById('loginForm').classList.remove('active');
    document.getElementById('signupForm').classList.add('active');
    document.getElementById('loginError').classList.remove('show');
}

function switchToLogin() {
    document.getElementById('signupForm').classList.remove('active');
    document.getElementById('loginForm').classList.add('active');
    document.getElementById('signupError').classList.remove('show');
}

// Handle Login
async function handleLogin(event) {
    event.preventDefault();
    
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    const button = event.target.querySelector('button[type="submit"]');
    
    setLoading(button, true);
    document.getElementById('loginError').classList.remove('show');
    
    try {
        const response = await apiRequest(API_CONFIG.ENDPOINTS.LOGIN, {
            method: 'POST',
            skipAuth: true,
            body: JSON.stringify({ email, password })
        });
        
        if (response.success && response.mfa_required) {
            // Store email temporarily for MFA
            sessionStorage.setItem('mfa_email', email);
            
            // Send MFA code
            await apiRequest(API_CONFIG.ENDPOINTS.MFA_SEND, {
                method: 'POST',
                skipAuth: true,
                body: JSON.stringify({ email })
            });
            
            // Redirect to MFA page
            window.location.href = 'mfa.html';
        }
    } catch (error) {
        showError('loginError', error.message || 'Login failed. Please check your credentials.');
    } finally {
        setLoading(button, false);
    }
}

// Handle Signup
async function handleSignup(event) {
    event.preventDefault();
    
    const fullName = document.getElementById('signupName').value;
    const email = document.getElementById('signupEmail').value;
    const password = document.getElementById('signupPassword').value;
    const confirmPassword = document.getElementById('signupConfirmPassword').value;
    const button = event.target.querySelector('button[type="submit"]');
    
    document.getElementById('signupError').classList.remove('show');
    
    // Validate passwords match
    if (password !== confirmPassword) {
        showError('signupError', 'Passwords do not match');
        return;
    }
    
    // Validate password strength
    if (password.length < 8) {
        showError('signupError', 'Password must be at least 8 characters long');
        return;
    }
    
    setLoading(button, true);
    
    try {
        const response = await apiRequest(API_CONFIG.ENDPOINTS.REGISTER, {
            method: 'POST',
            skipAuth: true,
            body: JSON.stringify({
                email,
                password,
                full_name: fullName
            })
        });
        
        if (response.success) {
            // Store email for auto-fill
            document.getElementById('loginEmail').value = email;
            
            // Switch to login form
            switchToLogin();
            
            // Show success message
            alert('Account created successfully! Please login.');
        }
    } catch (error) {
        showError('signupError', error.message || 'Signup failed. Email may already be registered.');
    } finally {
        setLoading(button, false);
    }
}

// Make functions globally available
window.switchToSignup = switchToSignup;
window.switchToLogin = switchToLogin;
window.handleLogin = handleLogin;
window.handleSignup = handleSignup;