from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from typing import List, Optional
from api.models.user import UserRole, Permission, ROLE_PERMISSIONS
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# JWT Settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

security = HTTPBearer()


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Validate JWT token and return user with effective permissions
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        
        if email is None:
            raise credentials_exception
            
    except JWTError as e:
        logger.warning(f"❌ JWT decode error: {str(e)}")
        raise credentials_exception
    
    # Get user from database
    db = request.state.db
    users_collection = db["users"]
    
    user = await users_collection.find_one({"email": email})
    
    if user is None:
        logger.warning(f"❌ User not found: {email}")
        raise credentials_exception
    
    if not user.get("is_active", True):
        logger.warning(f"❌ User deactivated: {email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    
    # Calculate effective permissions
    user_role = UserRole(user.get("role", "normal"))
    role_permissions = [p.value for p in ROLE_PERMISSIONS.get(user_role, [])]
    custom_permissions = user.get("custom_permissions", [])
    effective_permissions = list(set(role_permissions + custom_permissions))
    
    # Build user dict with permissions
    user_data = {
        "email": user["email"],
        "full_name": user.get("full_name", ""),
        "role": user.get("role", "normal"),
        "is_active": user.get("is_active", True),
        "is_verified": user.get("is_verified", False),
        "custom_permissions": custom_permissions,
        "role_permissions": role_permissions,
        "permissions": effective_permissions,  # All effective permissions
    }
    
    logger.debug(f"✅ User authenticated: {email} | Role: {user_data['role']} | Perms: {len(effective_permissions)}")
    
    return user_data


def require_permission(permission: Permission):
    """
    Dependency to require a specific permission
    Usage: Depends(require_permission(Permission.KEYVAULT_GENERATE_KEYS))
    """
    async def permission_checker(
        current_user: dict = Depends(get_current_user)
    ) -> dict:
        user_role = current_user.get("role", "")
        user_perms = current_user.get("permissions", [])
        
        # Admin bypass
        if user_role == "admin":
            return current_user
        
        if permission.value not in user_perms:
            logger.warning(f"❌ Permission denied: {current_user['email']} lacks {permission.value}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission.value}"
            )
        
        return current_user
    
    return permission_checker


def require_any_permission(permissions: List[Permission]):
    """
    Dependency to require any of the specified permissions
    """
    async def permission_checker(
        current_user: dict = Depends(get_current_user)
    ) -> dict:
        user_role = current_user.get("role", "")
        user_perms = current_user.get("permissions", [])
        
        if user_role == "admin":
            return current_user
        
        for perm in permissions:
            if perm.value in user_perms:
                return current_user
        
        perm_names = [p.value for p in permissions]
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"One of these permissions required: {', '.join(perm_names)}"
        )
    
    return permission_checker


def require_role(roles: List[UserRole]):
    """
    Dependency to require specific role(s)
    Usage: Depends(require_role([UserRole.ADMIN, UserRole.CO_ADMIN]))
    """
    async def role_checker(
        current_user: dict = Depends(get_current_user)
    ) -> dict:
        user_role = UserRole(current_user.get("role", "normal"))
        
        if user_role not in roles:
            role_names = [r.value for r in roles]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {', '.join(role_names)}"
            )
        
        return current_user
    
    return role_checker


def has_permission(user: dict, permission: str) -> bool:
    """
    Helper function to check if user has a permission
    """
    if user.get("role") == "admin":
        return True
    return permission in user.get("permissions", [])


def has_any_permission(user: dict, permissions: List[str]) -> bool:
    """
    Helper function to check if user has any of the permissions
    """
    if user.get("role") == "admin":
        return True
    user_perms = user.get("permissions", [])
    return any(p in user_perms for p in permissions)