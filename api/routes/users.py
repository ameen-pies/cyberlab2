from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from api.middleware.rbac_middleware import get_current_user, require_permission, require_role
from api.services.auth_service import AuthService
from api.models.user import (
    UserRole, Permission, ROLE_PERMISSIONS, 
    PERMISSION_CATEGORIES, PERMISSION_NAMES
)
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["User Management"])

# ============== Request Models ==============

class UserUpdateRequest(BaseModel):
    role: Optional[UserRole] = None
    custom_permissions: Optional[List[str]] = None
    is_active: Optional[bool] = None

class UserCreateRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: UserRole = UserRole.NORMAL
    custom_permissions: List[str] = []

class PermissionUpdateRequest(BaseModel):
    permissions: List[str]
    action: str = "set"  # "set", "add", "remove"

class UserResponse(BaseModel):
    email: str
    full_name: str
    role: str
    is_active: bool
    is_verified: bool
    mfa_enabled: bool
    custom_permissions: List[str]
    created_at: datetime
    last_login: Optional[datetime]
    created_by: Optional[str]

# ============== Helper Functions ==============

def safe_get_user_role(role_value: str) -> UserRole:
    """Safely convert role string to UserRole, defaulting to NORMAL for invalid values"""
    try:
        return UserRole(role_value)
    except ValueError:
        logger.warning(f"Invalid role value '{role_value}' found, defaulting to NORMAL")
        return UserRole.NORMAL

def get_user_effective_permissions(user: dict) -> List[str]:
    """Get all effective permissions for a user (role + custom)"""
    role = safe_get_user_role(user.get('role', 'normal'))
    role_perms = [p.value for p in ROLE_PERMISSIONS.get(role, [])]
    custom_perms = user.get('custom_permissions', [])
    return list(set(role_perms + custom_perms))

# ============== User CRUD Endpoints ==============

@router.get("/all", response_model=List[UserResponse])
async def get_all_users(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Get all users (Admin/Co-Admin only)"""
    user_role = safe_get_user_role(current_user.get('role', 'normal'))
    if user_role not in [UserRole.ADMIN, UserRole.CO_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view all users"
        )
    
    db = request.state.db
    users_collection = db["users"]
    
    users = await users_collection.find({}).to_list(length=None)
    
    user_list = []
    for user in users:
        user_list.append({
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user.get("role", "normal"),
            "is_active": user.get("is_active", True),
            "is_verified": user.get("is_verified", False),
            "mfa_enabled": user.get("mfa_enabled", True),
            "custom_permissions": user.get("custom_permissions", []),
            "created_at": user.get("created_at"),
            "last_login": user.get("last_login"),
            "created_by": user.get("created_by")
        })
    
    return user_list

@router.post("/create")
async def create_user(
    user_data: UserCreateRequest,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Create new user (Admin only)"""
    user_role = safe_get_user_role(current_user.get('role', 'normal'))
    if user_role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create users"
        )
    
    db = request.state.db
    auth_service = AuthService(db)
    
    new_user = await auth_service.create_user(
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
        role=user_data.role,
        custom_permissions=[Permission(p) for p in user_data.custom_permissions if p in [e.value for e in Permission]],
        created_by=current_user["email"]
    )
    
    if not new_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    logger.info(f"✅ Admin {current_user['email']} created user {user_data.email} with role {user_data.role}")
    
    return {
        "success": True,
        "message": f"User {user_data.email} created successfully",
        "user": {
            "email": new_user["email"],
            "role": new_user["role"],
            "permissions": get_user_effective_permissions(new_user)
        }
    }

@router.put("/{user_email}")
async def update_user(
    user_email: str,
    update_data: UserUpdateRequest,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Update user role and permissions (Admin only)"""
    user_role = safe_get_user_role(current_user.get('role', 'normal'))
    if user_role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update users"
        )
    
    if user_email == current_user["email"] and update_data.role and update_data.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot change your own admin role"
        )
    
    db = request.state.db
    users_collection = db["users"]
    
    target_user = await users_collection.find_one({"email": user_email})
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    update_dict = {"updated_at": datetime.utcnow()}
    
    if update_data.role is not None:
        update_dict["role"] = update_data.role.value
    
    if update_data.custom_permissions is not None:
        valid_perms = [p for p in update_data.custom_permissions if p in [e.value for e in Permission]]
        update_dict["custom_permissions"] = valid_perms
    
    if update_data.is_active is not None:
        update_dict["is_active"] = update_data.is_active
    
    await users_collection.update_one(
        {"email": user_email},
        {"$set": update_dict}
    )
    
    logger.info(f"✅ Admin {current_user['email']} updated user {user_email}: {update_dict}")
    
    return {
        "success": True,
        "message": f"User {user_email} updated successfully",
        "updates": update_dict
    }

@router.delete("/{user_email}")
async def delete_user(
    user_email: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Delete user (Admin only)"""
    user_role = safe_get_user_role(current_user.get('role', 'normal'))
    if user_role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete users"
        )
    
    if user_email == current_user["email"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account"
        )
    
    db = request.state.db
    users_collection = db["users"]
    
    result = await users_collection.delete_one({"email": user_email})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    logger.info(f"✅ Admin {current_user['email']} deleted user {user_email}")
    
    return {
        "success": True,
        "message": f"User {user_email} deleted successfully"
    }

# ============== Permission Management Endpoints ==============

@router.get("/{user_email}/permissions")
async def get_user_permissions(
    user_email: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Get specific user's permissions (Admin only)"""
    current_user_role = safe_get_user_role(current_user.get('role', 'normal'))
    if current_user_role != UserRole.ADMIN and user_email != current_user["email"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view other users' permissions"
        )
    
    db = request.state.db
    users_collection = db["users"]
    
    user = await users_collection.find_one({"email": user_email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    role = safe_get_user_role(user.get('role', 'normal'))
    role_perms = [p.value for p in ROLE_PERMISSIONS.get(role, [])]
    custom_perms = user.get('custom_permissions', [])
    effective_perms = list(set(role_perms + custom_perms))
    
    return {
        "success": True,
        "email": user_email,
        "role": role.value,
        "role_permissions": role_perms,
        "custom_permissions": custom_perms,
        "effective_permissions": effective_perms,
        "total_permissions": len(effective_perms)
    }

@router.put("/{user_email}/permissions")
async def update_user_permissions(
    user_email: str,
    perm_data: PermissionUpdateRequest,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Update user's custom permissions (Admin only)"""
    user_role = safe_get_user_role(current_user.get('role', 'normal'))
    if user_role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can manage permissions"
        )
    
    db = request.state.db
    users_collection = db["users"]
    
    user = await users_collection.find_one({"email": user_email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate permissions
    valid_permission_values = [p.value for p in Permission]
    valid_perms = [p for p in perm_data.permissions if p in valid_permission_values]
    
    current_perms = user.get('custom_permissions', [])
    
    if perm_data.action == "set":
        new_perms = valid_perms
    elif perm_data.action == "add":
        new_perms = list(set(current_perms + valid_perms))
    elif perm_data.action == "remove":
        new_perms = [p for p in current_perms if p not in valid_perms]
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid action. Use 'set', 'add', or 'remove'"
        )
    
    await users_collection.update_one(
        {"email": user_email},
        {"$set": {
            "custom_permissions": new_perms,
            "updated_at": datetime.utcnow()
        }}
    )
    
    logger.info(f"✅ Admin {current_user['email']} updated permissions for {user_email}: {perm_data.action} {valid_perms}")
    
    # Get new effective permissions
    role = safe_get_user_role(user.get('role', 'normal'))
    role_perms = [p.value for p in ROLE_PERMISSIONS.get(role, [])]
    effective_perms = list(set(role_perms + new_perms))
    
    return {
        "success": True,
        "message": f"Permissions updated for {user_email}",
        "action": perm_data.action,
        "custom_permissions": new_perms,
        "effective_permissions": effective_perms
    }

@router.post("/{user_email}/permissions/grant-keyvault")
async def grant_keyvault_permissions(
    user_email: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Quick action: Grant all KeyVault permissions to a user (Admin only)"""
    user_role = safe_get_user_role(current_user.get('role', 'normal'))
    if user_role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can manage permissions"
        )
    
    keyvault_perms = [
        Permission.KEYVAULT_GENERATE_KEYS.value,
        Permission.KEYVAULT_VIEW_KEYS.value,
        Permission.KEYVAULT_DOWNLOAD_KEYS.value,
        Permission.KEYVAULT_ROTATE_KEYS.value,
        Permission.KEYVAULT_DELETE_KEYS.value,
        Permission.KEYVAULT_SEND_EMAIL.value,
        Permission.KEYVAULT_GENERATE_CERTS.value,
        Permission.KEYVAULT_VIEW_CERTS.value,
        Permission.KEYVAULT_DOWNLOAD_CERTS.value,
    ]
    
    db = request.state.db
    users_collection = db["users"]
    
    user = await users_collection.find_one({"email": user_email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    current_perms = user.get('custom_permissions', [])
    new_perms = list(set(current_perms + keyvault_perms))
    
    await users_collection.update_one(
        {"email": user_email},
        {"$set": {
            "custom_permissions": new_perms,
            "updated_at": datetime.utcnow()
        }}
    )
    
    logger.info(f"✅ Admin {current_user['email']} granted KeyVault permissions to {user_email}")
    
    return {
        "success": True,
        "message": f"KeyVault permissions granted to {user_email}",
        "granted_permissions": keyvault_perms
    }

@router.post("/{user_email}/permissions/revoke-keyvault")
async def revoke_keyvault_permissions(
    user_email: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Quick action: Revoke all KeyVault permissions from a user (Admin only)"""
    user_role = safe_get_user_role(current_user.get('role', 'normal'))
    if user_role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can manage permissions"
        )
    
    keyvault_perms = [
        Permission.KEYVAULT_GENERATE_KEYS.value,
        Permission.KEYVAULT_VIEW_KEYS.value,
        Permission.KEYVAULT_DOWNLOAD_KEYS.value,
        Permission.KEYVAULT_ROTATE_KEYS.value,
        Permission.KEYVAULT_DELETE_KEYS.value,
        Permission.KEYVAULT_SEND_EMAIL.value,
        Permission.KEYVAULT_GENERATE_CERTS.value,
        Permission.KEYVAULT_VIEW_CERTS.value,
        Permission.KEYVAULT_DOWNLOAD_CERTS.value,
    ]
    
    db = request.state.db
    users_collection = db["users"]
    
    user = await users_collection.find_one({"email": user_email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    current_perms = user.get('custom_permissions', [])
    new_perms = [p for p in current_perms if p not in keyvault_perms]
    
    await users_collection.update_one(
        {"email": user_email},
        {"$set": {
            "custom_permissions": new_perms,
            "updated_at": datetime.utcnow()
        }}
    )
    
    logger.info(f"✅ Admin {current_user['email']} revoked KeyVault permissions from {user_email}")
    
    return {
        "success": True,
        "message": f"KeyVault permissions revoked from {user_email}",
        "revoked_permissions": keyvault_perms
    }

# ============== Info Endpoints ==============

@router.get("/permissions")
async def get_my_permissions(
    current_user: dict = Depends(get_current_user)
):
    """Get current user's permissions"""
    user_role = safe_get_user_role(current_user.get('role', 'normal'))
    custom_perms = current_user.get('custom_permissions', [])
    
    role_perms = ROLE_PERMISSIONS.get(user_role, [])
    all_perms = list(set([p.value for p in role_perms] + custom_perms))
    
    return {
        "email": current_user["email"],
        "role": user_role.value,
        "permissions": all_perms,
        "role_permissions": [p.value for p in role_perms],
        "custom_permissions": custom_perms
    }

@router.get("/roles")
async def get_available_roles(
    current_user: dict = Depends(get_current_user)
):
    """Get all available roles and their permissions"""
    user_role = safe_get_user_role(current_user.get('role', 'normal'))
    
    if user_role not in [UserRole.ADMIN, UserRole.CO_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view role information"
        )
    
    roles_info = {}
    for role, perms in ROLE_PERMISSIONS.items():
        roles_info[role.value] = {
            "name": role.value,
            "permissions": [p.value for p in perms],
            "permission_count": len(perms)
        }
    
    return {
        "roles": roles_info,
        "available_permissions": [p.value for p in Permission]
    }

@router.get("/permissions/categories")
async def get_permission_categories(
    current_user: dict = Depends(get_current_user)
):
    """Get all permissions organized by category (Admin only)"""
    user_role = safe_get_user_role(current_user.get('role', 'normal'))
    
    if user_role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view permission categories"
        )
    
    categories = {}
    for category, perms in PERMISSION_CATEGORIES.items():
        categories[category] = [
            {
                "value": p.value,
                "name": PERMISSION_NAMES.get(p, p.value),
                "description": f"Allows user to {PERMISSION_NAMES.get(p, p.value).lower()}"
            }
            for p in perms
        ]
    
    return {
        "success": True,
        "categories": categories,
        "total_permissions": len(Permission)
    }