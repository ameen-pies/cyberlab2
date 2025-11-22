from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from typing import Optional, Dict, List
from api.middleware.rbac_middleware import get_current_user
from api.services.password_service import PasswordService
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/password-checker", tags=["Password Strength Analysis"])

class PasswordCheckRequest(BaseModel):
    password: str
    check_breaches: bool = True
    custom_policy: Optional[Dict] = None

class PolicySaveRequest(BaseModel):
    policy_name: str
    policy: Dict

@router.post("/analyze")
async def analyze_password(
    request_data: PasswordCheckRequest,
    req: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Comprehensive password strength analysis
    - Entropy calculation
    - Crack time estimation
    - Policy compliance check
    - Breach database lookup (HaveIBeenPwned)
    - Improvement suggestions
    """
    logger.info(f"🔒 Password analysis request from {current_user['email']}")
    
    result = await PasswordService.analyze_password(
        password=request_data.password,
        custom_policy=request_data.custom_policy,
        check_breaches=request_data.check_breaches
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Analysis failed")
        )
    
    # Save analysis to database for analytics
    db = req.state.db
    analytics_collection = db["password_analytics"]
    
    try:
        await analytics_collection.insert_one({
            "user_email": current_user['email'],
            "password_length": len(request_data.password),
            "entropy": result["analysis"]["entropy"],
            "score": result["analysis"]["score"]["score"],
            "rating": result["analysis"]["score"]["rating"],
            "breached": result["analysis"]["breach_info"].get("breached", False),
            "analyzed_at": result["analysis"]["analyzed_at"]
        })
    except Exception as e:
        logger.warning(f"⚠️ Failed to save analytics: {str(e)}")
    
    return {
        "success": True,
        **result["analysis"]
    }

@router.post("/check-breach")
async def check_breach_only(
    request_data: PasswordCheckRequest,
    req: Request,
    current_user: dict = Depends(get_current_user)
):
    """Check if password appears in data breaches (HaveIBeenPwned)"""
    logger.info(f"🔍 Breach check request from {current_user['email']}")
    
    breach_info = await PasswordService.check_breach(request_data.password)
    
    return {
        "success": True,
        "breach_info": breach_info
    }

@router.post("/policies")
async def save_custom_policy(
    request_data: PolicySaveRequest,
    req: Request,
    current_user: dict = Depends(get_current_user)
):
    """Save a custom password policy"""
    logger.info(f"💾 Saving policy '{request_data.policy_name}' for {current_user['email']}")
    
    db = req.state.db
    
    policy = await PasswordService.save_policy(
        db=db,
        user_email=current_user['email'],
        policy_name=request_data.policy_name,
        policy=request_data.policy
    )
    
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save policy"
        )
    
    return {
        "success": True,
        "message": f"Policy '{request_data.policy_name}' saved successfully",
        "policy": {
            "policy_id": policy["policy_id"],
            "policy_name": policy["policy_name"],
            "created_at": policy["created_at"]
        }
    }

@router.get("/policies")
async def get_user_policies(
    req: Request,
    current_user: dict = Depends(get_current_user)
):
    """Get all custom policies for current user"""
    db = req.state.db
    
    policies = await PasswordService.get_user_policies(db, current_user['email'])
    
    # Remove _id from response
    for policy in policies:
        policy["_id"] = str(policy["_id"])
    
    return {
        "success": True,
        "policies": policies,
        "total": len(policies)
    }

@router.get("/policies/default")
async def get_default_policy(
    current_user: dict = Depends(get_current_user)
):
    """Get the default password policy"""
    return {
        "success": True,
        "policy": PasswordService.DEFAULT_POLICY,
        "description": {
            "min_length": "Minimum password length",
            "require_uppercase": "Require at least one uppercase letter",
            "require_lowercase": "Require at least one lowercase letter",
            "require_digits": "Require at least one digit",
            "require_special": "Require at least one special character",
            "max_repeating": "Maximum number of repeating characters",
            "block_common": "Block commonly used passwords"
        }
    }

@router.get("/analytics")
async def get_password_analytics(
    req: Request,
    current_user: dict = Depends(get_current_user)
):
    """Get password analysis statistics for current user"""
    db = req.state.db
    analytics_collection = db["password_analytics"]
    
    # Get all analyses for user
    analyses = await analytics_collection.find({
        "user_email": current_user['email']
    }).sort("analyzed_at", -1).limit(100).to_list(length=100)
    
    if not analyses:
        return {
            "success": True,
            "analytics": {
                "total_checks": 0,
                "average_score": 0,
                "breached_count": 0,
                "rating_distribution": {}
            }
        }
    
    # Calculate statistics
    total_checks = len(analyses)
    average_score = sum(a["score"] for a in analyses) / total_checks
    breached_count = sum(1 for a in analyses if a.get("breached", False))
    
    rating_dist = {}
    for analysis in analyses:
        rating = analysis.get("rating", "unknown")
        rating_dist[rating] = rating_dist.get(rating, 0) + 1
    
    return {
        "success": True,
        "analytics": {
            "total_checks": total_checks,
            "average_score": round(average_score, 2),
            "breached_count": breached_count,
            "breach_percentage": round((breached_count / total_checks) * 100, 2),
            "rating_distribution": rating_dist,
            "recent_checks": [
                {
                    "password_length": a["password_length"],
                    "entropy": a["entropy"],
                    "score": a["score"],
                    "rating": a["rating"],
                    "breached": a.get("breached", False),
                    "analyzed_at": a["analyzed_at"]
                }
                for a in analyses[:10]
            ]
        }
    }

@router.post("/batch-analyze")
async def batch_analyze_passwords(
    passwords: List[str],
    req: Request,
    current_user: dict = Depends(get_current_user)
):
    """Analyze multiple passwords at once"""
    if len(passwords) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 passwords per batch"
        )
    
    logger.info(f"📊 Batch analysis of {len(passwords)} passwords from {current_user['email']}")
    
    results = []
    
    for password in passwords:
        result = await PasswordService.analyze_password(
            password=password,
            check_breaches=True
        )
        
        if result.get("success"):
            results.append({
                "password_length": len(password),
                "score": result["analysis"]["score"]["score"],
                "rating": result["analysis"]["score"]["rating"],
                "breached": result["analysis"]["breach_info"].get("breached", False),
                "suggestions_count": len(result["analysis"]["suggestions"])
            })
    
    # Calculate batch statistics
    avg_score = sum(r["score"] for r in results) / len(results) if results else 0
    breached_count = sum(1 for r in results if r["breached"])
    
    return {
        "success": True,
        "batch_results": results,
        "summary": {
            "total_analyzed": len(results),
            "average_score": round(avg_score, 2),
            "breached_passwords": breached_count,
            "breach_rate": f"{(breached_count / len(results) * 100):.1f}%" if results else "0%"
        }
    }