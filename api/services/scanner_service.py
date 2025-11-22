import re
import math
from typing import Dict, List, Optional
from datetime import datetime
import base64
import logging

logger = logging.getLogger(__name__)

class SecretScannerService:
    """
    Scans text and files for leaked credentials and sensitive data
    Uses regex patterns + entropy analysis
    """
    
    # Secret detection patterns
    SECRET_PATTERNS = {
        "aws_access_key": {
            "pattern": r'(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}',
            "name": "AWS Access Key ID",
            "severity": "high"
        },
        "aws_secret_key": {
            "pattern": r'(?i)aws(.{0,20})?[\'"][0-9a-zA-Z\/+]{40}[\'"]',
            "name": "AWS Secret Access Key",
            "severity": "critical"
        },
        "github_token": {
            "pattern": r'ghp_[0-9a-zA-Z]{36}|gho_[0-9a-zA-Z]{36}|ghu_[0-9a-zA-Z]{36}|ghs_[0-9a-zA-Z]{36}|ghr_[0-9a-zA-Z]{36}',
            "name": "GitHub Personal Access Token",
            "severity": "high"
        },
        "slack_token": {
            "pattern": r'xox[baprs]-([0-9a-zA-Z]{10,48})?',
            "name": "Slack Token",
            "severity": "high"
        },
        "google_api_key": {
            "pattern": r'AIza[0-9A-Za-z\\-_]{35}',
            "name": "Google API Key",
            "severity": "high"
        },
        "stripe_key": {
            "pattern": r'(?:r|s)k_live_[0-9a-zA-Z]{24,99}',
            "name": "Stripe API Key",
            "severity": "high"
        },
        "jwt_token": {
            "pattern": r'eyJ[A-Za-z0-9-_=]+\.eyJ[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*',
            "name": "JSON Web Token (JWT)",
            "severity": "medium"
        },
        "private_key": {
            "pattern": r'-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----',
            "name": "Private Key",
            "severity": "critical"
        },
        "azure_connection_string": {
            "pattern": r'(?i)DefaultEndpointsProtocol=https;AccountName=[a-z0-9]+;AccountKey=[A-Za-z0-9+/=]{88};',
            "name": "Azure Connection String",
            "severity": "critical"
        },
        "database_url": {
            "pattern": r'(?i)(mysql|postgres|mongodb|redis):\/\/[^\s]+:[^\s]+@[^\s]+',
            "name": "Database Connection URL",
            "severity": "critical"
        },
        "api_key_generic": {
            "pattern": r'(?i)(api[_-]?key|apikey|api[_-]?secret)[\s]*[=:]+[\s]*[\'"]?([0-9a-zA-Z\-_]{20,})[\'"]?',
            "name": "Generic API Key",
            "severity": "medium"
        },
        "password_in_url": {
            "pattern": r'(?i)[a-z]{3,10}:\/\/[^:\/\s]+:([^@\/\s]{8,})@',
            "name": "Password in URL",
            "severity": "high"
        },
        "email": {
            "pattern": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "name": "Email Address",
            "severity": "low"
        },
        "ip_address": {
            "pattern": r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
            "name": "IP Address",
            "severity": "low"
        }
    }
    
    @staticmethod
    def calculate_entropy(string: str) -> float:
        """Calculate Shannon entropy of a string"""
        if not string:
            return 0.0
        
        # Count character frequency
        char_count = {}
        for char in string:
            char_count[char] = char_count.get(char, 0) + 1
        
        # Calculate entropy
        length = len(string)
        entropy = 0.0
        
        for count in char_count.values():
            probability = count / length
            if probability > 0:
                entropy -= probability * math.log2(probability)
        
        return round(entropy, 2)
    
    @staticmethod
    def is_high_entropy(string: str, min_entropy: float = 4.5) -> bool:
        """Check if string has high entropy (likely a secret)"""
        if len(string) < 16:
            return False
        
        entropy = SecretScannerService.calculate_entropy(string)
        return entropy >= min_entropy
    
    @staticmethod
    def scan_text(text: str, redact: bool = False) -> Dict:
        """Scan text for secrets"""
        findings = []
        
        for secret_type, config in SecretScannerService.SECRET_PATTERNS.items():
            pattern = config["pattern"]
            matches = re.finditer(pattern, text)
            
            for match in matches:
                secret_value = match.group(0)
                
                # Additional entropy check for generic patterns
                if secret_type in ["api_key_generic", "password_in_url"]:
                    if not SecretScannerService.is_high_entropy(secret_value):
                        continue
                
                finding = {
                    "type": secret_type,
                    "name": config["name"],
                    "severity": config["severity"],
                    "value": secret_value if not redact else f"{secret_value[:8]}...{secret_value[-4:]}",
                    "position": {
                        "start": match.start(),
                        "end": match.end()
                    },
                    "line": text[:match.start()].count('\n') + 1,
                    "entropy": SecretScannerService.calculate_entropy(secret_value)
                }
                
                findings.append(finding)
        
        # Deduplicate findings
        unique_findings = []
        seen = set()
        
        for finding in findings:
            key = (finding["type"], finding["position"]["start"])
            if key not in seen:
                seen.add(key)
                unique_findings.append(finding)
        
        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        unique_findings.sort(key=lambda x: (severity_order.get(x["severity"], 4), x["position"]["start"]))
        
        return {
            "success": True,
            "findings": unique_findings,
            "total_found": len(unique_findings),
            "severity_counts": {
                "critical": sum(1 for f in unique_findings if f["severity"] == "critical"),
                "high": sum(1 for f in unique_findings if f["severity"] == "high"),
                "medium": sum(1 for f in unique_findings if f["severity"] == "medium"),
                "low": sum(1 for f in unique_findings if f["severity"] == "low")
            }
        }
    
    @staticmethod
    def redact_secrets(text: str) -> Dict:
        """Redact all found secrets from text"""
        redacted_text = text
        findings = []
        
        for secret_type, config in SecretScannerService.SECRET_PATTERNS.items():
            pattern = config["pattern"]
            
            def redact_match(match):
                secret = match.group(0)
                findings.append({
                    "type": secret_type,
                    "name": config["name"],
                    "severity": config["severity"],
                    "original_length": len(secret)
                })
                return f"[REDACTED {config['name'].upper()}]"
            
            redacted_text = re.sub(pattern, redact_match, redacted_text)
        
        return {
            "success": True,
            "redacted_text": redacted_text,
            "redaction_count": len(findings),
            "redactions": findings
        }
    
    @staticmethod
    def scan_file(file_content: str, filename: str, redact: bool = False) -> Dict:
        """Scan file content for secrets"""
        try:
            # Try to decode base64 if needed
            try:
                decoded = base64.b64decode(file_content).decode('utf-8')
                scan_result = SecretScannerService.scan_text(decoded, redact)
            except:
                scan_result = SecretScannerService.scan_text(file_content, redact)
            
            scan_result["filename"] = filename
            scan_result["scanned_at"] = datetime.utcnow()
            
            return scan_result
            
        except Exception as e:
            logger.error(f"❌ File scan failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    async def save_scan_result(
        db,
        user_email: str,
        scan_type: str,
        result: Dict,
        filename: Optional[str] = None
    ) -> Optional[Dict]:
        """Save scan results to database"""
        try:
            scans_collection = db["secret_scans"]
            
            scan_record = {
                "user_email": user_email,
                "scan_type": scan_type,
                "filename": filename,
                "total_found": result.get("total_found", 0),
                "severity_counts": result.get("severity_counts", {}),
                "findings": result.get("findings", []),
                "scanned_at": datetime.utcnow()
            }
            
            await scans_collection.insert_one(scan_record)
            
            return scan_record
            
        except Exception as e:
            logger.error(f"❌ Failed to save scan result: {str(e)}")
            return None
    
    @staticmethod
    async def get_scan_history(db, user_email: str, limit: int = 50) -> List[Dict]:
        """Get user's scan history"""
        try:
            scans_collection = db["secret_scans"]
            
            scans = await scans_collection.find({
                "user_email": user_email
            }).sort("scanned_at", -1).limit(limit).to_list(length=limit)
            
            # Remove sensitive data from findings
            for scan in scans:
                scan["_id"] = str(scan["_id"])
                if "findings" in scan:
                    for finding in scan["findings"]:
                        if "value" in finding:
                            finding["value"] = f"{finding['value'][:8]}...{finding['value'][-4:]}"
            
            return scans
            
        except Exception as e:
            logger.error(f"❌ Failed to get scan history: {str(e)}")
            return []
    
    @staticmethod
    def generate_report(scan_result: Dict) -> str:
        """Generate a human-readable report"""
        findings = scan_result.get("findings", [])
        
        if not findings:
            return "✅ No secrets or sensitive data detected!"
        
        report = f"""
🔍 Secret Scan Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Summary:
   Total Findings: {scan_result.get('total_found', 0)}
   🔴 Critical: {scan_result.get('severity_counts', {}).get('critical', 0)}
   🟠 High: {scan_result.get('severity_counts', {}).get('high', 0)}
   🟡 Medium: {scan_result.get('severity_counts', {}).get('medium', 0)}
   🟢 Low: {scan_result.get('severity_counts', {}).get('low', 0)}

📋 Detailed Findings:
"""
        
        for i, finding in enumerate(findings, 1):
            severity_icon = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🟢"
            }.get(finding["severity"], "⚪")
            
            report += f"""
   {i}. {severity_icon} {finding['name']} ({finding['severity'].upper()})
      Line: {finding['line']}
      Position: {finding['position']['start']}-{finding['position']['end']}
      Entropy: {finding['entropy']}
      Preview: {finding['value'][:50]}...
"""
        
        report += "\n⚠️  Recommendation: Remove or rotate all exposed secrets immediately!\n"
        
        return report