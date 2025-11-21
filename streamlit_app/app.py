import streamlit as st
from utils.api_client import APIClient  # ✅ Correct

st.set_page_config(
    page_title="CyberSec Platform",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

def init_session_state():
    """Initialize session state variables"""
    if 'api_client' not in st.session_state:
        st.session_state.api_client = APIClient()
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    if 'awaiting_mfa' not in st.session_state:
        st.session_state.awaiting_mfa = False

def main():
    init_session_state()
    
    st.markdown("""
        <style>
        .main-header {
            font-size: 3rem;
            font-weight: bold;
            text-align: center;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 2rem;
        }
        .subtitle {
            text-align: center;
            color: #666;
            font-size: 1.2rem;
            margin-bottom: 3rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    if not st.session_state.authenticated:
        st.markdown('<h1 class="main-header">🔐 CyberSec Platform</h1>', unsafe_allow_html=True)
        st.markdown('<p class="subtitle">Enterprise-Grade Security Simulation Suite</p>', unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])
        
        with tab1:
            login_page()
        
        with tab2:
            register_page()
    else:
        dashboard_page()

def register_page():
    """Registration page"""
    st.header("Create Account")
    
    with st.form("register_form"):
        full_name = st.text_input("Full Name", placeholder="John Doe")
        email = st.text_input("Email", placeholder="john@example.com")
        password = st.text_input("Password", type="password", placeholder="Min. 8 characters")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        submit = st.form_submit_button("Create Account", use_container_width=True)
        
        if submit:
            if not all([full_name, email, password, confirm_password]):
                st.error("Please fill in all fields")
            elif password != confirm_password:
                st.error("Passwords do not match")
            elif len(password) < 8:
                st.error("Password must be at least 8 characters")
            else:
                with st.spinner("Creating account..."):
                    response, status = st.session_state.api_client.register(
                        email=email,
                        password=password,
                        full_name=full_name
                    )
                    
                    if status == 201:
                        st.success("✅ Account created! Please login.")
                    else:
                        st.error(f"❌ {response.get('detail', 'Registration failed')}")

def login_page():
    """Login page"""
    if not st.session_state.awaiting_mfa:
        st.header("Sign In")
        
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="your@email.com")
            password = st.text_input("Password", type="password")
            
            submit = st.form_submit_button("Login", use_container_width=True)
            
            if submit:
                if not email or not password:
                    st.error("Please enter email and password")
                else:
                    with st.spinner("Authenticating..."):
                        response, status = st.session_state.api_client.login(email, password)
                        
                        if status == 200 and response.get("success"):
                            st.session_state.user_email = email
                            st.session_state.awaiting_mfa = True
                            
                            mfa_response, mfa_status = st.session_state.api_client.send_mfa_code(email)
                            
                            if mfa_status == 200:
                                st.success("✅ Credentials verified! Check your email for MFA code.")
                                st.rerun()
                            else:
                                st.error("Failed to send MFA code")
                        else:
                            st.error(f"❌ {response.get('detail', 'Login failed')}")
    else:
        mfa_verification_page()

def mfa_verification_page():
    """MFA verification page"""
    st.header("🔐 Multi-Factor Authentication")
    st.info(f"📧 A 6-digit code has been sent to **{st.session_state.user_email}**")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        code = st.text_input(
            "Enter MFA Code",
            max_chars=6,
            placeholder="000000",
            key="mfa_code_input"
        )
    
    with col2:
        if st.button("Resend Code", use_container_width=True):
            with st.spinner("Sending..."):
                response, status = st.session_state.api_client.send_mfa_code(
                    st.session_state.user_email
                )
                if status == 200:
                    st.success("✅ Code sent!")
                else:
                    st.error("Failed to resend")
    
    col_submit, col_cancel = st.columns(2)
    
    with col_submit:
        if st.button("Verify & Login", type="primary", use_container_width=True):
            if len(code) == 6 and code.isdigit():
                with st.spinner("Verifying..."):
                    response, status = st.session_state.api_client.verify_mfa_code(
                        st.session_state.user_email,
                        code
                    )
                    
                    if status == 200:
                        token = response.get("access_token")
                        st.session_state.api_client.set_token(token)
                        st.session_state.authenticated = True
                        st.session_state.awaiting_mfa = False
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid or expired code")
            else:
                st.error("Please enter a valid 6-digit code")
    
    with col_cancel:
        if st.button("Cancel", use_container_width=True):
            st.session_state.awaiting_mfa = False
            st.session_state.user_email = None
            st.rerun()

def dashboard_page():
    """Main dashboard"""
    st.sidebar.title("🔐 CyberSec Hub")
    st.sidebar.write(f"👤 **{st.session_state.user_email}**")
    st.sidebar.divider()
    
    page = st.sidebar.radio(
        "Navigation",
        ["🏠 Dashboard", "🔒 Encryption Simulator", "📊 Security Metrics"],
        label_visibility="collapsed"
    )
    
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user_email = None
        st.session_state.api_client.set_token(None)
        st.rerun()
    
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "🔒 Encryption Simulator":
        show_encryption_simulator()
    elif page == "📊 Security Metrics":
        show_security_metrics()

def show_dashboard():
    """Dashboard home"""
    st.title("🏠 Security Operations Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Active Sessions", "1", "0%")
    with col2:
        st.metric("Security Score", "98%", "+2%")
    with col3:
        st.metric("Threats Blocked", "0", "0")
    
    st.divider()
    
    st.subheader("🎯 Available Simulations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container():
            st.markdown("""
            ### 🔒 Encryption Simulator
            Learn about data encryption in transit and at rest.
            - AES-256 encryption
            - Key management
            - Real-time demonstrations
            """)
            if st.button("Launch Simulator", key="enc_sim"):
                st.session_state.current_page = "encryption"
                st.rerun()
    
    with col2:
        with st.container():
            st.markdown("""
            ### 🛡️ Coming Soon
            More security simulations in development:
            - Network Security Scanner
            - Vulnerability Assessment
            - Penetration Testing Lab
            """)

def show_encryption_simulator():
    """Encryption simulation page"""
    st.title("🔒 Encryption Simulator")
    
    tab1, tab2, tab3 = st.tabs(["🚀 In Transit", "💾 At Rest", "🔄 Full Lifecycle"])
    
    with tab1:
        encryption_in_transit()
    
    with tab2:
        encryption_at_rest()
    
    with tab3:
        encryption_lifecycle()

def encryption_in_transit():
    """In transit encryption simulation"""
    st.header("Encryption In Transit (TLS/SSL Simulation)")
    st.info("This simulates how data is encrypted when transmitted over networks")
    
    data = st.text_area("Enter data to encrypt:", placeholder="Secret message here...")
    password = st.text_input("Transport Password:", type="password", placeholder="Secure password")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔐 Encrypt", use_container_width=True):
            if data and password:
                with st.spinner("Encrypting..."):
                    response, status = st.session_state.api_client.encrypt_in_transit(data, password)
                    
                    if status == 200:
                        st.session_state.transit_result = response
                        st.success("✅ Data encrypted successfully!")
                        
                        with st.expander("📋 Encryption Details", expanded=True):
                            st.code(response.get("encrypted_data"), language="text")
                            st.write(f"**Method:** {response.get('method')}")
                            st.write(f"**Salt:** {response.get('salt')}")
                            st.caption(response.get("use_case"))
                    else:
                        st.error("Encryption failed")
            else:
                st.warning("Please enter data and password")
    
    with col2:
        if st.button("🔓 Decrypt", use_container_width=True):
            if hasattr(st.session_state, 'transit_result'):
                encrypted = st.session_state.transit_result.get("encrypted_data")
                salt = st.session_state.transit_result.get("salt")
                
                with st.spinner("Decrypting..."):
                    response, status = st.session_state.api_client.decrypt_in_transit(
                        encrypted, password, salt
                    )
                    
                    if status == 200:
                        st.success("✅ Data decrypted successfully!")
                        st.code(response.get("decrypted_data"), language="text")
                    else:
                        st.error("❌ Decryption failed - check password")
            else:
                st.warning("Please encrypt data first")

def encryption_at_rest():
    """At rest encryption simulation"""
    st.header("Encryption At Rest (Database/Storage)")
    st.info("This simulates how data is encrypted when stored in databases or files")
    
    data = st.text_area("Enter data to store securely:", placeholder="Sensitive data...")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔐 Encrypt & Store", use_container_width=True):
            if data:
                with st.spinner("Encrypting..."):
                    response, status = st.session_state.api_client.encrypt_at_rest(data)
                    
                    if status == 200:
                        st.session_state.rest_result = response
                        st.success("✅ Data encrypted and stored!")
                        
                        with st.expander("📋 Storage Details", expanded=True):
                            st.code(response.get("encrypted_data")[:100] + "...", language="text")
                            st.write(f"**Method:** {response.get('method')}")
                            st.caption(response.get("use_case"))
                            st.warning("🔑 Key stored securely (in production, use KMS)")
                    else:
                        st.error("Encryption failed")
            else:
                st.warning("Please enter data")
    
    with col2:
        if st.button("🔓 Retrieve & Decrypt", use_container_width=True):
            if hasattr(st.session_state, 'rest_result'):
                encrypted = st.session_state.rest_result.get("encrypted_data")
                key = st.session_state.rest_result.get("key")
                
                with st.spinner("Retrieving and decrypting..."):
                    response, status = st.session_state.api_client.decrypt_at_rest(encrypted, key)
                    
                    if status == 200:
                        st.success("✅ Data retrieved and decrypted!")
                        st.code(response.get("decrypted_data"), language="text")
                    else:
                        st.error("Decryption failed")
            else:
                st.warning("Please encrypt data first")

def encryption_lifecycle():
    """Full encryption lifecycle demo"""
    st.header("🔄 Complete Encryption Lifecycle")
    st.info("See how data is encrypted at rest, then encrypted again for transit")
    
    data = st.text_area("Enter sample data:", placeholder="Your data here...")
    
    if st.button("🚀 Run Full Lifecycle Demo", use_container_width=True):
        if data:
            with st.spinner("Running encryption lifecycle..."):
                response, status = st.session_state.api_client.encryption_lifecycle(data)
                
                if status == 200:
                    st.success("✅ Lifecycle completed!")
                    
                    stages = response.get("stages", {})
                    explanation = response.get("explanation", {})
                    
                    st.subheader("Stage 1: Encryption At Rest")
                    with st.expander("View Details"):
                        st.json(stages.get("1_at_rest_encryption"))
                    st.caption(f"💡 {explanation.get('at_rest')}")
                    
                    st.divider()
                    
                    st.subheader("Stage 2: Retrieval & Decryption")
                    with st.expander("View Details"):
                        st.json(stages.get("2_at_rest_decryption"))
                    
                    st.divider()
                    
                    st.subheader("Stage 3: Encryption In Transit")
                    with st.expander("View Details"):
                        st.json(stages.get("3_in_transit_encryption"))
                    st.caption(f"💡 {explanation.get('in_transit')}")
                    
                    st.divider()
                    
                    st.info(f"🏭 **Production Note:** {explanation.get('real_world')}")
                else:
                    st.error("Lifecycle demo failed")
        else:
            st.warning("Please enter data")

def show_security_metrics():
    """Security metrics dashboard"""
    st.title("📊 Security Metrics")
    st.info("Coming soon: Real-time security analytics and threat intelligence")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Encryption Operations", "0", "Today")
        st.metric("Average Response Time", "< 100ms", "-5ms")
    
    with col2:
        st.metric("System Uptime", "99.9%", "+0.1%")
        st.metric("Security Events", "0", "Last 24h")

if __name__ == "__main__":
    main()