from nicegui import ui, app
import requests
from typing import Optional
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from shared.config.settings import settings

API_BASE_URL = settings.API_BASE_URL

# Global state
class AppState:
    def __init__(self):
        self.authenticated = False
        self.user_email = None
        self.awaiting_mfa = False
        self.token = None
        self.transit_result = None
        self.rest_result = None

state = AppState()

# API Client functions
def api_call(method, endpoint, json_data=None, auth=False):
    headers = {"Content-Type": "application/json"}
    if auth and state.token:
        headers["Authorization"] = f"Bearer {state.token}"
    
    try:
        if method == "POST":
            response = requests.post(f"{API_BASE_URL}{endpoint}", json=json_data, headers=headers)
        else:
            response = requests.get(f"{API_BASE_URL}{endpoint}", headers=headers)
        return response.json(), response.status_code
    except Exception as e:
        return {"error": str(e)}, 500

# Pages
def main_page():
    ui.colors(primary='#667eea', secondary='#764ba2', accent='#00BFA5')
    
    with ui.header().classes('items-center justify-between'):
        ui.label('🔐 CyberSec Platform').classes('text-h5 text-white')
        if state.authenticated:
            ui.label(f'👤 {state.user_email}').classes('text-white')
            ui.button('Logout', on_click=logout).props('flat color=white')
    
    if not state.authenticated:
        show_auth_page()
    else:
        show_dashboard()

def show_auth_page():
    with ui.column().classes('absolute-center w-96 gap-4'):
        ui.label('🔐 CyberSec Platform').classes('text-h3 text-center')
        ui.label('Enterprise-Grade Security Simulation Suite').classes('text-subtitle1 text-center text-grey-7')
        
        with ui.tabs().classes('w-full') as tabs:
            login_tab = ui.tab('Login')
            register_tab = ui.tab('Register')
        
        with ui.tab_panels(tabs, value=login_tab).classes('w-full'):
            with ui.tab_panel(login_tab):
                show_login_form()
            
            with ui.tab_panel(register_tab):
                show_register_form()

def show_login_form():
    if state.awaiting_mfa:
        show_mfa_form()
        return
    
    with ui.card().classes('w-full p-4'):
        ui.label('Sign In').classes('text-h6')
        
        email = ui.input('Email', placeholder='your@email.com').classes('w-full')
        password = ui.input('Password', password=True).classes('w-full')
        
        async def handle_login():
            if not email.value or not password.value:
                ui.notify('Please enter email and password', type='negative')
                return
            
            ui.notify('Authenticating...', type='info')
            response, status = api_call('POST', '/auth/login', {
                'email': email.value,
                'password': password.value
            })
            
            if status == 200 and response.get('success'):
                state.user_email = email.value
                state.awaiting_mfa = True
                
                # Send MFA code
                mfa_response, mfa_status = api_call('POST', '/auth/mfa/send', {'email': email.value})
                
                if mfa_status == 200:
                    ui.notify('✅ Check your email for MFA code!', type='positive')
                    ui.navigate.reload()
                else:
                    ui.notify('Failed to send MFA code', type='negative')
            else:
                ui.notify(f"❌ {response.get('detail', 'Login failed')}", type='negative')
        
        ui.button('Login', on_click=handle_login).classes('w-full').props('color=primary')

def show_register_form():
    with ui.card().classes('w-full p-4'):
        ui.label('Create Account').classes('text-h6')
        
        full_name = ui.input('Full Name', placeholder='John Doe').classes('w-full')
        email = ui.input('Email', placeholder='john@example.com').classes('w-full')
        password = ui.input('Password', password=True, placeholder='Min. 8 characters').classes('w-full')
        confirm_password = ui.input('Confirm Password', password=True).classes('w-full')
        
        async def handle_register():
            if not all([full_name.value, email.value, password.value, confirm_password.value]):
                ui.notify('Please fill in all fields', type='negative')
                return
            
            if password.value != confirm_password.value:
                ui.notify('Passwords do not match', type='negative')
                return
            
            if len(password.value) < 8:
                ui.notify('Password must be at least 8 characters', type='negative')
                return
            
            ui.notify('Creating account...', type='info')
            response, status = api_call('POST', '/auth/register', {
                'email': email.value,
                'password': password.value,
                'full_name': full_name.value
            })
            
            if status == 201:
                ui.notify('✅ Account created! Please login.', type='positive')
            else:
                ui.notify(f"❌ {response.get('detail', 'Registration failed')}", type='negative')
        
        ui.button('Create Account', on_click=handle_register).classes('w-full').props('color=primary')

def show_mfa_form():
    with ui.card().classes('w-full p-4'):
        ui.label('🔐 Multi-Factor Authentication').classes('text-h6')
        ui.label(f'📧 A 6-digit code has been sent to {state.user_email}').classes('text-grey-7')
        
        code = ui.input('Enter MFA Code', placeholder='000000').props('maxlength=6').classes('w-full')
        
        with ui.row().classes('w-full gap-2'):
            async def verify_code():
                if len(code.value) != 6 or not code.value.isdigit():
                    ui.notify('Please enter a valid 6-digit code', type='negative')
                    return
                
                ui.notify('Verifying...', type='info')
                response, status = api_call('POST', '/auth/mfa/verify', {
                    'email': state.user_email,
                    'code': code.value
                })
                
                if status == 200:
                    state.token = response.get('access_token')
                    state.authenticated = True
                    state.awaiting_mfa = False
                    ui.notify('✅ Login successful!', type='positive')
                    ui.navigate.reload()
                else:
                    ui.notify('❌ Invalid or expired code', type='negative')
            
            async def resend_code():
                response, status = api_call('POST', '/auth/mfa/send', {'email': state.user_email})
                if status == 200:
                    ui.notify('✅ Code sent!', type='positive')
                else:
                    ui.notify('Failed to resend', type='negative')
            
            ui.button('Verify & Login', on_click=verify_code).classes('flex-grow').props('color=primary')
            ui.button('Resend', on_click=resend_code).props('flat')
        
        def cancel():
            state.awaiting_mfa = False
            state.user_email = None
            ui.navigate.reload()
        
        ui.button('Cancel', on_click=cancel).classes('w-full').props('flat')

def show_dashboard():
    with ui.left_drawer(top_corner=True, bottom_corner=True).classes('bg-grey-2'):
        ui.label('🔐 CyberSec Hub').classes('text-h6 q-pa-md')
        
        with ui.column().classes('gap-2 q-pa-md'):
            ui.button('🏠 Dashboard', on_click=lambda: show_dashboard_home()).props('flat align=left').classes('w-full')
            ui.button('🔒 Encryption Simulator', on_click=lambda: show_encryption_simulator()).props('flat align=left').classes('w-full')
            ui.button('📊 Security Metrics', on_click=lambda: show_security_metrics()).props('flat align=left').classes('w-full')
    
    with ui.column().classes('w-full p-8 gap-4'):
        show_dashboard_home()

def show_dashboard_home():
    ui.clear()
    
    with ui.column().classes('w-full p-8 gap-4'):
        ui.label('🏠 Security Operations Dashboard').classes('text-h4')
        
        with ui.row().classes('w-full gap-4'):
            with ui.card().classes('flex-1 p-4'):
                ui.label('Active Sessions').classes('text-grey-7')
                ui.label('1').classes('text-h4')
            
            with ui.card().classes('flex-1 p-4'):
                ui.label('Security Score').classes('text-grey-7')
                ui.label('98%').classes('text-h4 text-green')
            
            with ui.card().classes('flex-1 p-4'):
                ui.label('Threats Blocked').classes('text-grey-7')
                ui.label('0').classes('text-h4')
        
        ui.separator()
        
        ui.label('🎯 Available Simulations').classes('text-h5')
        
        with ui.row().classes('w-full gap-4'):
            with ui.card().classes('flex-1 p-4'):
                ui.label('🔒 Encryption Simulator').classes('text-h6')
                ui.markdown('''
                Learn about data encryption in transit and at rest.
                - AES-256 encryption
                - Key management
                - Real-time demonstrations
                ''')
                ui.button('Launch Simulator', on_click=lambda: show_encryption_simulator()).props('color=primary')
            
            with ui.card().classes('flex-1 p-4'):
                ui.label('🛡️ Coming Soon').classes('text-h6')
                ui.markdown('''
                More security simulations in development:
                - Network Security Scanner
                - Vulnerability Assessment
                - Penetration Testing Lab
                ''')

def show_encryption_simulator():
    ui.clear()
    
    with ui.column().classes('w-full p-8 gap-4'):
        ui.label('🔒 Encryption Simulator').classes('text-h4')
        
        with ui.tabs() as tabs:
            in_transit_tab = ui.tab('🚀 In Transit')
            at_rest_tab = ui.tab('💾 At Rest')
            lifecycle_tab = ui.tab('🔄 Full Lifecycle')
        
        with ui.tab_panels(tabs, value=in_transit_tab):
            with ui.tab_panel(in_transit_tab):
                show_encryption_in_transit()
            
            with ui.tab_panel(at_rest_tab):
                show_encryption_at_rest()
            
            with ui.tab_panel(lifecycle_tab):
                show_encryption_lifecycle()

def show_encryption_in_transit():
    with ui.card().classes('w-full p-4'):
        ui.label('Encryption In Transit (TLS/SSL Simulation)').classes('text-h6')
        ui.label('This simulates how data is encrypted when transmitted over networks').classes('text-grey-7')
        
        data = ui.textarea('Enter data to encrypt:', placeholder='Secret message here...').classes('w-full')
        password = ui.input('Transport Password:', password=True, placeholder='Secure password').classes('w-full')
        
        result_container = ui.column().classes('w-full')
        
        with ui.row().classes('w-full gap-2'):
            async def encrypt():
                if not data.value or not password.value:
                    ui.notify('Please enter data and password', type='warning')
                    return
                
                ui.notify('Encrypting...', type='info')
                response, status = api_call('POST', '/simulations/encrypt/in-transit', {
                    'data': data.value,
                    'password': password.value
                }, auth=True)
                
                if status == 200:
                    state.transit_result = response
                    ui.notify('✅ Data encrypted successfully!', type='positive')
                    
                    with result_container:
                        result_container.clear()
                        with ui.expansion('📋 Encryption Details', value=True).classes('w-full'):
                            ui.code(response.get('encrypted_data')).classes('w-full')
                            ui.label(f"Method: {response.get('method')}")
                            ui.label(f"Salt: {response.get('salt')}")
                            ui.label(response.get('use_case')).classes('text-grey-7')
                else:
                    ui.notify('Encryption failed', type='negative')
            
            async def decrypt():
                if not state.transit_result:
                    ui.notify('Please encrypt data first', type='warning')
                    return
                
                encrypted = state.transit_result.get('encrypted_data')
                salt = state.transit_result.get('salt')
                
                ui.notify('Decrypting...', type='info')
                response, status = api_call('POST', '/simulations/decrypt/in-transit', {
                    'encrypted_data': encrypted,
                    'password': password.value,
                    'salt': salt
                }, auth=True)
                
                if status == 200:
                    ui.notify('✅ Data decrypted successfully!', type='positive')
                    
                    with result_container:
                        result_container.clear()
                        ui.code(response.get('decrypted_data')).classes('w-full')
                else:
                    ui.notify('❌ Decryption failed - check password', type='negative')
            
            ui.button('🔐 Encrypt', on_click=encrypt).props('color=primary')
            ui.button('🔓 Decrypt', on_click=decrypt).props('color=secondary')

def show_encryption_at_rest():
    with ui.card().classes('w-full p-4'):
        ui.label('Encryption At Rest (Database/Storage)').classes('text-h6')
        ui.label('This simulates how data is encrypted when stored in databases or files').classes('text-grey-7')
        
        data = ui.textarea('Enter data to store securely:', placeholder='Sensitive data...').classes('w-full')
        
        result_container = ui.column().classes('w-full')
        
        with ui.row().classes('w-full gap-2'):
            async def encrypt():
                if not data.value:
                    ui.notify('Please enter data', type='warning')
                    return
                
                ui.notify('Encrypting...', type='info')
                response, status = api_call('POST', '/simulations/encrypt/at-rest', {
                    'data': data.value
                }, auth=True)
                
                if status == 200:
                    state.rest_result = response
                    ui.notify('✅ Data encrypted and stored!', type='positive')
                    
                    with result_container:
                        result_container.clear()
                        with ui.expansion('📋 Storage Details', value=True).classes('w-full'):
                            ui.code(response.get('encrypted_data')[:100] + '...').classes('w-full')
                            ui.label(f"Method: {response.get('method')}")
                            ui.label(response.get('use_case')).classes('text-grey-7')
                            ui.label('🔑 Key stored securely (in production, use KMS)').classes('text-warning')
                else:
                    ui.notify('Encryption failed', type='negative')
            
            async def decrypt():
                if not state.rest_result:
                    ui.notify('Please encrypt data first', type='warning')
                    return
                
                encrypted = state.rest_result.get('encrypted_data')
                key = state.rest_result.get('key')
                
                ui.notify('Retrieving and decrypting...', type='info')
                response, status = api_call('POST', '/simulations/decrypt/at-rest', {
                    'encrypted_data': encrypted,
                    'key': key
                }, auth=True)
                
                if status == 200:
                    ui.notify('✅ Data retrieved and decrypted!', type='positive')
                    
                    with result_container:
                        result_container.clear()
                        ui.code(response.get('decrypted_data')).classes('w-full')
                else:
                    ui.notify('Decryption failed', type='negative')
            
            ui.button('🔐 Encrypt & Store', on_click=encrypt).props('color=primary')
            ui.button('🔓 Retrieve & Decrypt', on_click=decrypt).props('color=secondary')

def show_encryption_lifecycle():
    with ui.card().classes('w-full p-4'):
        ui.label('🔄 Complete Encryption Lifecycle').classes('text-h6')
        ui.label('See how data is encrypted at rest, then encrypted again for transit').classes('text-grey-7')
        
        data = ui.textarea('Enter sample data:', placeholder='Your data here...').classes('w-full')
        
        result_container = ui.column().classes('w-full')
        
        async def run_lifecycle():
            if not data.value:
                ui.notify('Please enter data', type='warning')
                return
            
            ui.notify('Running encryption lifecycle...', type='info')
            response, status = api_call('POST', '/simulations/encrypt/lifecycle', {
                'data': data.value
            }, auth=True)
            
            if status == 200:
                ui.notify('✅ Lifecycle completed!', type='positive')
                
                stages = response.get('stages', {})
                explanation = response.get('explanation', {})
                
                with result_container:
                    result_container.clear()
                    
                    ui.label('Stage 1: Encryption At Rest').classes('text-h6')
                    with ui.expansion('View Details').classes('w-full'):
                        ui.json_editor({'content': {'json': stages.get('1_at_rest_encryption')}})
                    ui.label(f"💡 {explanation.get('at_rest')}").classes('text-grey-7')
                    
                    ui.separator()
                    
                    ui.label('Stage 2: Retrieval & Decryption').classes('text-h6')
                    with ui.expansion('View Details').classes('w-full'):
                        ui.json_editor({'content': {'json': stages.get('2_at_rest_decryption')}})
                    
                    ui.separator()
                    
                    ui.label('Stage 3: Encryption In Transit').classes('text-h6')
                    with ui.expansion('View Details').classes('w-full'):
                        ui.json_editor({'content': {'json': stages.get('3_in_transit_encryption')}})
                    ui.label(f"💡 {explanation.get('in_transit')}").classes('text-grey-7')
                    
                    ui.separator()
                    
                    ui.label(f"🏭 Production Note: {explanation.get('real_world')}").classes('text-info')
            else:
                ui.notify('Lifecycle demo failed', type='negative')
        
        ui.button('🚀 Run Full Lifecycle Demo', on_click=run_lifecycle).classes('w-full').props('color=primary')

def show_security_metrics():
    ui.clear()
    
    with ui.column().classes('w-full p-8 gap-4'):
        ui.label('📊 Security Metrics').classes('text-h4')
        ui.label('Coming soon: Real-time security analytics and threat intelligence').classes('text-info')
        
        with ui.row().classes('w-full gap-4'):
            with ui.card().classes('flex-1 p-4'):
                ui.label('Encryption Operations').classes('text-grey-7')
                ui.label('0').classes('text-h4')
                ui.label('Today').classes('text-grey-6')
            
            with ui.card().classes('flex-1 p-4'):
                ui.label('Average Response Time').classes('text-grey-7')
                ui.label('< 100ms').classes('text-h4')
                ui.label('-5ms').classes('text-green')
            
            with ui.card().classes('flex-1 p-4'):
                ui.label('System Uptime').classes('text-grey-7')
                ui.label('99.9%').classes('text-h4')
                ui.label('+0.1%').classes('text-green')
            
            with ui.card().classes('flex-1 p-4'):
                ui.label('Security Events').classes('text-grey-7')
                ui.label('0').classes('text-h4')
                ui.label('Last 24h').classes('text-grey-6')

def logout():
    state.authenticated = False
    state.user_email = None
    state.token = None
    state.awaiting_mfa = False
    ui.notify('Logged out', type='info')
    ui.navigate.reload()

# Run the app
@ui.page('/')
def index():
    main_page()

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title='CyberSec Platform',
        port=8501,
        reload=True,
        show=True
    )