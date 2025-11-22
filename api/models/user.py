from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserRole(str, Enum):
    ADMIN = "admin"
    CO_ADMIN = "co_admin"
    NORMAL = "normal"
    LIMITED = "limited"  # Added to handle the existing role in your database


class Permission(str, Enum):
    # Encryption permissions
    ENCRYPT_TEXT = "encrypt_text"
    ENCRYPT_FILE = "encrypt_file"
    DECRYPT_TEXT = "decrypt_text"
    DECRYPT_FILE = "decrypt_file"
    
    # KeyVault permissions
    KEYVAULT_GENERATE_KEYS = "keyvault_generate_keys"
    KEYVAULT_VIEW_KEYS = "keyvault_view_keys"
    KEYVAULT_DOWNLOAD_KEYS = "keyvault_download_keys"
    KEYVAULT_ROTATE_KEYS = "keyvault_rotate_keys"
    KEYVAULT_DELETE_KEYS = "keyvault_delete_keys"
    KEYVAULT_SEND_EMAIL = "keyvault_send_email"
    KEYVAULT_GENERATE_CERTS = "keyvault_generate_certs"
    KEYVAULT_VIEW_CERTS = "keyvault_view_certs"
    KEYVAULT_DOWNLOAD_CERTS = "keyvault_download_certs"
    
    # Password checker permissions
    PASSWORD_CHECK = "password_check"
    PASSWORD_BREACH_CHECK = "password_breach_check"
    PASSWORD_POLICY_MANAGE = "password_policy_manage"
    
    # Secret scanner permissions
    SCANNER_TEXT = "scanner_text"
    SCANNER_FILE = "scanner_file"
    SCANNER_GITHUB = "scanner_github"
    
    # User management permissions
    VIEW_USERS = "view_users"
    CREATE_USERS = "create_users"
    UPDATE_USERS = "update_users"
    DELETE_USERS = "delete_users"
    MANAGE_PERMISSIONS = "manage_permissions"


# Role-based default permissions
ROLE_PERMISSIONS = {
    UserRole.ADMIN: list(Permission),  # All permissions
    UserRole.CO_ADMIN: [
        # Encryption
        Permission.ENCRYPT_TEXT,
        Permission.ENCRYPT_FILE,
        Permission.DECRYPT_TEXT,
        Permission.DECRYPT_FILE,
        # KeyVault (all)
        Permission.KEYVAULT_GENERATE_KEYS,
        Permission.KEYVAULT_VIEW_KEYS,
        Permission.KEYVAULT_DOWNLOAD_KEYS,
        Permission.KEYVAULT_ROTATE_KEYS,
        Permission.KEYVAULT_DELETE_KEYS,
        Permission.KEYVAULT_SEND_EMAIL,
        Permission.KEYVAULT_GENERATE_CERTS,
        Permission.KEYVAULT_VIEW_CERTS,
        Permission.KEYVAULT_DOWNLOAD_CERTS,
        # Password checker
        Permission.PASSWORD_CHECK,
        Permission.PASSWORD_BREACH_CHECK,
        Permission.PASSWORD_POLICY_MANAGE,
        # Scanner
        Permission.SCANNER_TEXT,
        Permission.SCANNER_FILE,
        Permission.SCANNER_GITHUB,
        # Limited user management
        Permission.VIEW_USERS,
    ],
    UserRole.NORMAL: [
        # Basic encryption
        Permission.ENCRYPT_TEXT,
        Permission.DECRYPT_TEXT,
        # Basic KeyVault (view only)
        Permission.KEYVAULT_VIEW_KEYS,
        Permission.KEYVAULT_VIEW_CERTS,
        # Password checker
        Permission.PASSWORD_CHECK,
        Permission.PASSWORD_BREACH_CHECK,
        # Basic scanner
        Permission.SCANNER_TEXT,
    ],
    UserRole.LIMITED: [  # Added limited role permissions
        # Very basic permissions only
        Permission.ENCRYPT_TEXT,
        Permission.DECRYPT_TEXT,
        Permission.PASSWORD_CHECK,
    ]
}


# Permission categories for UI display
PERMISSION_CATEGORIES = {
    "Encryption Service": [
        Permission.ENCRYPT_TEXT,
        Permission.ENCRYPT_FILE,
        Permission.DECRYPT_TEXT,
        Permission.DECRYPT_FILE,
    ],
    "KeyVault - Keys": [
        Permission.KEYVAULT_GENERATE_KEYS,
        Permission.KEYVAULT_VIEW_KEYS,
        Permission.KEYVAULT_DOWNLOAD_KEYS,
        Permission.KEYVAULT_ROTATE_KEYS,
        Permission.KEYVAULT_DELETE_KEYS,
        Permission.KEYVAULT_SEND_EMAIL,
    ],
    "KeyVault - Certificates": [
        Permission.KEYVAULT_GENERATE_CERTS,
        Permission.KEYVAULT_VIEW_CERTS,
        Permission.KEYVAULT_DOWNLOAD_CERTS,
    ],
    "Password Checker": [
        Permission.PASSWORD_CHECK,
        Permission.PASSWORD_BREACH_CHECK,
        Permission.PASSWORD_POLICY_MANAGE,
    ],
    "Secret Scanner": [
        Permission.SCANNER_TEXT,
        Permission.SCANNER_FILE,
        Permission.SCANNER_GITHUB,
    ],
    "User Management": [
        Permission.VIEW_USERS,
        Permission.CREATE_USERS,
        Permission.UPDATE_USERS,
        Permission.DELETE_USERS,
        Permission.MANAGE_PERMISSIONS,
    ]
}


# Human-readable permission names
PERMISSION_NAMES = {
    Permission.ENCRYPT_TEXT: "Encrypt Text",
    Permission.ENCRYPT_FILE: "Encrypt Files",
    Permission.DECRYPT_TEXT: "Decrypt Text",
    Permission.DECRYPT_FILE: "Decrypt Files",
    Permission.KEYVAULT_GENERATE_KEYS: "Generate Keys",
    Permission.KEYVAULT_VIEW_KEYS: "View Keys",
    Permission.KEYVAULT_DOWNLOAD_KEYS: "Download Keys",
    Permission.KEYVAULT_ROTATE_KEYS: "Rotate Keys",
    Permission.KEYVAULT_DELETE_KEYS: "Delete Keys",
    Permission.KEYVAULT_SEND_EMAIL: "Send Keys via Email",
    Permission.KEYVAULT_GENERATE_CERTS: "Generate Certificates",
    Permission.KEYVAULT_VIEW_CERTS: "View Certificates",
    Permission.KEYVAULT_DOWNLOAD_CERTS: "Download Certificates",
    Permission.PASSWORD_CHECK: "Check Password Strength",
    Permission.PASSWORD_BREACH_CHECK: "Check Breach Database",
    Permission.PASSWORD_POLICY_MANAGE: "Manage Password Policies",
    Permission.SCANNER_TEXT: "Scan Text for Secrets",
    Permission.SCANNER_FILE: "Scan Files for Secrets",
    Permission.SCANNER_GITHUB: "Scan GitHub URLs",
    Permission.VIEW_USERS: "View Users",
    Permission.CREATE_USERS: "Create Users",
    Permission.UPDATE_USERS: "Update Users",
    Permission.DELETE_USERS: "Delete Users",
    Permission.MANAGE_PERMISSIONS: "Manage User Permissions",
}


class User(BaseModel):
    email: EmailStr
    full_name: str
    hashed_password: str
    role: UserRole = UserRole.NORMAL
    custom_permissions: List[str] = []  # Additional permissions beyond role
    is_active: bool = True
    is_verified: bool = False
    mfa_enabled: bool = True
    mfa_secret: Optional[str] = None
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    last_login: Optional[datetime] = None
    created_by: Optional[str] = None
    
    class Config:
        use_enum_values = True