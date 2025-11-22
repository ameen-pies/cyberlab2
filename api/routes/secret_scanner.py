from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File
from pydantic import BaseModel
from typing import Optional
from api.middleware.rbac_middleware import get_current_user
from api.services.scanner_service import SecretScannerService
import base64
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/secret-scanner", tags=["Secret Detection & Sanitization"])

class TextScanRequest(BaseModel):
    text: str
    redact: bool = False

class RedactRequest(BaseModel):
    text: str

@router.post("/scan/text")
async def scan_text(
    request_data: TextScanRequest,
    req: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Scan text for exposed secrets and credentials
    - API Keys (AWS, Google, Stripe, GitHub, etc.)
    - Database connection strings
    - Private keys
    - JWT tokens
    - Passwords in URLs
    """
    logger.info(f"🕵️ Text scan request from {current_user['email']}")
    
    result = SecretScannerService.scan_text(
        text=request_data.text,
        redact=request_data.redact
    )
    
    # Save scan result to database
    db = req.state.db
    await SecretScannerService.save_scan_result(
        db=db,
        user_email=current_user['email'],
        scan_type="text",
        result=result
    )
    
    # Generate report
    report = SecretScannerService.generate_report(result)
    
    return {
        **result,
        "report": report
    }

@router.post("/scan/file")
async def scan_file(
    file: UploadFile = File(...),
    redact: bool = False,
    req: Request = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Scan uploaded file for exposed secrets
    Supports: .txt, .py, .js, .json, .env, .yml, .yaml, .config, etc.
    """
    logger.info(f"🕵️ File scan request from {current_user['email']}: {file.filename}")
    
    # Read file content
    content = await file.read()
    
    try:
        # Try to decode as text
        text_content = content.decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be text-based (UTF-8 encoded)"
        )
    
    result = SecretScannerService.scan_file(
        file_content=text_content,
        filename=file.filename,
        redact=redact
    )
    
    # Save scan result
    db = req.state.db
    await SecretScannerService.save_scan_result(
        db=db,
        user_email=current_user['email'],
        scan_type="file",
        result=result,
        filename=file.filename
    )
    
    # Generate report
    report = SecretScannerService.generate_report(result)
    
    return {
        **result,
        "report": report
    }

@router.post("/redact")
async def redact_secrets(
    request_data: RedactRequest,
    req: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Redact all found secrets from text
    Returns sanitized text with secrets replaced by [REDACTED] markers
    """
    logger.info(f"🔒 Redaction request from {current_user['email']}")
    
    result = SecretScannerService.redact_secrets(request_data.text)
    
    return result

@router.get("/history")
async def get_scan_history(
    limit: int = 50,
    req: Request = None,
    current_user: dict = Depends(get_current_user)
):
    """Get scan history for current user"""
    db = req.state.db
    
    history = await SecretScannerService.get_scan_history(
        db=db,
        user_email=current_user['email'],
        limit=limit
    )
    
    return {
        "success": True,
        "scans": history,
        "total": len(history)
    }

@router.get("/patterns")
async def get_detection_patterns(
    current_user: dict = Depends(get_current_user)
):
    """Get list of all secret patterns that are detected"""
    patterns = []
    
    for pattern_id, config in SecretScannerService.SECRET_PATTERNS.items():
        patterns.append({
            "id": pattern_id,
            "name": config["name"],
            "severity": config["severity"],
            "description": f"Detects {config['name']}"
        })
    
    # Sort by severity
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    patterns.sort(key=lambda x: severity_order.get(x["severity"], 4))
    
    return {
        "success": True,
        "patterns": patterns,
        "total": len(patterns)
    }

@router.get("/statistics")
async def get_scanner_statistics(
    req: Request,
    current_user: dict = Depends(get_current_user)
):
    """Get scanning statistics for current user"""
    db = req.state.db
    scans_collection = db["secret_scans"]
    
    # Get all scans for user
    scans = await scans_collection.find({
        "user_email": current_user['email']
    }).to_list(length=None)
    
    if not scans:
        return {
            "success": True,
            "statistics": {
                "total_scans": 0,
                "total_secrets_found": 0,
                "scans_by_type": {},
                "severity_breakdown": {}
            }
        }
    
    # Calculate statistics
    total_scans = len(scans)
    total_secrets = sum(scan.get("total_found", 0) for scan in scans)
    
    scans_by_type = {}
    for scan in scans:
        scan_type = scan.get("scan_type", "unknown")
        scans_by_type[scan_type] = scans_by_type.get(scan_type, 0) + 1
    
    # Aggregate severity counts
    severity_totals = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for scan in scans:
        severity_counts = scan.get("severity_counts", {})
        for severity, count in severity_counts.items():
            severity_totals[severity] = severity_totals.get(severity, 0) + count
    
    # Get most recent scans
    recent_scans = sorted(scans, key=lambda x: x.get("scanned_at"), reverse=True)[:10]
    
    return {
        "success": True,
        "statistics": {
            "total_scans": total_scans,
            "total_secrets_found": total_secrets,
            "scans_by_type": scans_by_type,
            "severity_breakdown": severity_totals,
            "recent_scans": [
                {
                    "scan_type": s.get("scan_type"),
                    "filename": s.get("filename"),
                    "total_found": s.get("total_found", 0),
                    "scanned_at": s.get("scanned_at")
                }
                for s in recent_scans
            ]
        }
    }

@router.post("/scan/github-url")
async def scan_github_file(
    github_url: str,
    req: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Scan a public GitHub file for secrets
    Example: https://github.com/user/repo/blob/main/config.py
    """
    import aiohttp
    
    logger.info(f"🕵️ GitHub scan request from {current_user['email']}: {github_url}")
    
    # Convert GitHub URL to raw URL
    if "github.com" in github_url and "/blob/" in github_url:
        raw_url = github_url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid GitHub URL. Must be a direct file link."
        )
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(raw_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to fetch GitHub file: {response.status}"
                    )
                
                content = await response.text()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch GitHub file: {str(e)}"
        )
    
    result = SecretScannerService.scan_text(content, redact=False)
    
    # Save scan result
    db = req.state.db
    await SecretScannerService.save_scan_result(
        db=db,
        user_email=current_user['email'],
        scan_type="github",
        result=result,
        filename=github_url
    )
    
    report = SecretScannerService.generate_report(result)
    
    return {
        **result,
        "github_url": github_url,
        "report": report
    }