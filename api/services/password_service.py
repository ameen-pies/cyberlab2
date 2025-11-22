import math
import re
import hashlib
import aiohttp
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PasswordService:
    """
    Advanced password strength checker with breach detection
    Uses HaveIBeenPwned API with k-anonymity for privacy
    """
    
    # Password policy defaults
    DEFAULT_POLICY = {
        "min_length": 8,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_digits": True,
        "require_special": True,
        "max_repeating": 3,
        "block_common": True
    }
    
    # Common weak passwords (subset)
    COMMON_PASSWORDS = {
        "password", "123456", "123456789", "12345678", "12345", "1234567",
        "password1", "qwerty", "abc123", "monkey", "dragon", "letmein",
        "welcome", "admin", "password123", "iloveyou"
    }
    
    @staticmethod
    def calculate_entropy(password: str) -> float:
        """Calculate password entropy (bits)"""
        charset_size = 0
        
        if re.search(r'[a-z]', password):
            charset_size += 26
        if re.search(r'[A-Z]', password):
            charset_size += 26
        if re.search(r'\d', password):
            charset_size += 10
        if re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
            charset_size += 32
        
        if charset_size == 0:
            return 0.0
        
        entropy = len(password) * math.log2(charset_size)
        return round(entropy, 2)
    
    @staticmethod
    def estimate_crack_time(entropy: float) -> Dict[str, str]:
        """Estimate time to crack password based on entropy"""
        # Assume 10 billion guesses per second (modern GPU)
        guesses_per_second = 10_000_000_000
        
        # Calculate total possible combinations
        combinations = 2 ** entropy
        
        # Time in seconds
        seconds = combinations / guesses_per_second
        
        # Convert to human-readable format
        if seconds < 1:
            return {"value": "< 1", "unit": "second", "rating": "very_weak"}
        elif seconds < 60:
            return {"value": str(int(seconds)), "unit": "seconds", "rating": "very_weak"}
        elif seconds < 3600:
            return {"value": str(int(seconds / 60)), "unit": "minutes", "rating": "weak"}
        elif seconds < 86400:
            return {"value": str(int(seconds / 3600)), "unit": "hours", "rating": "weak"}
        elif seconds < 31536000:
            return {"value": str(int(seconds / 86400)), "unit": "days", "rating": "fair"}
        elif seconds < 31536000 * 100:
            return {"value": str(int(seconds / 31536000)), "unit": "years", "rating": "good"}
        elif seconds < 31536000 * 1000:
            return {"value": str(int(seconds / 31536000)), "unit": "years", "rating": "strong"}
        else:
            return {"value": "∞", "unit": "centuries+", "rating": "very_strong"}
    
    @staticmethod
    def check_policy(password: str, policy: Optional[Dict] = None) -> Dict:
        """Check password against policy requirements"""
        policy = policy or PasswordService.DEFAULT_POLICY
        
        checks = {
            "length": len(password) >= policy.get("min_length", 8),
            "uppercase": not policy.get("require_uppercase") or bool(re.search(r'[A-Z]', password)),
            "lowercase": not policy.get("require_lowercase") or bool(re.search(r'[a-z]', password)),
            "digits": not policy.get("require_digits") or bool(re.search(r'\d', password)),
            "special": not policy.get("require_special") or bool(re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password)),
            "repeating": True,
            "common": True
        }
        
        # Check for repeating characters
        max_repeat = policy.get("max_repeating", 3)
        for i in range(len(password) - max_repeat + 1):
            if len(set(password[i:i+max_repeat])) == 1:
                checks["repeating"] = False
                break
        
        # Check against common passwords
        if policy.get("block_common") and password.lower() in PasswordService.COMMON_PASSWORDS:
            checks["common"] = False
        
        return checks
    
    @staticmethod
    async def check_breach(password: str) -> Dict:
        """
        Check if password appears in data breaches using HaveIBeenPwned API
        Uses k-anonymity model for privacy (only sends first 5 chars of hash)
        """
        try:
            # Hash the password with SHA-1
            sha1_hash = hashlib.sha1(password.encode()).hexdigest().upper()
            
            # Send only first 5 characters (k-anonymity)
            prefix = sha1_hash[:5]
            suffix = sha1_hash[5:]
            
            url = f"https://api.pwnedpasswords.com/range/{prefix}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status != 200:
                        logger.warning(f"⚠️ HIBP API returned status {response.status}")
                        return {
                            "breached": False,
                            "count": 0,
                            "checked": False,
                            "error": "API unavailable"
                        }
                    
                    text = await response.text()
                    
                    # Parse response
                    for line in text.splitlines():
                        hash_suffix, count = line.split(':')
                        if hash_suffix == suffix:
                            return {
                                "breached": True,
                                "count": int(count),
                                "checked": True,
                                "severity": "critical" if int(count) > 1000 else "high"
                            }
                    
                    return {
                        "breached": False,
                        "count": 0,
                        "checked": True
                    }
                    
        except Exception as e:
            logger.error(f"❌ Breach check failed: {str(e)}")
            return {
                "breached": False,
                "count": 0,
                "checked": False,
                "error": str(e)
            }
    
    @staticmethod
    def get_suggestions(password: str, policy_checks: Dict) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []
        
        if not policy_checks["length"]:
            suggestions.append("Increase password length to at least 8 characters")
        
        if not policy_checks["uppercase"]:
            suggestions.append("Add uppercase letters (A-Z)")
        
        if not policy_checks["lowercase"]:
            suggestions.append("Add lowercase letters (a-z)")
        
        if not policy_checks["digits"]:
            suggestions.append("Add numbers (0-9)")
        
        if not policy_checks["special"]:
            suggestions.append("Add special characters (!@#$%^&*)")
        
        if not policy_checks["repeating"]:
            suggestions.append("Avoid repeating characters (e.g., 'aaa', '111')")
        
        if not policy_checks["common"]:
            suggestions.append("This is a commonly used password - choose something more unique")
        
        # Additional suggestions
        if len(password) < 12:
            suggestions.append("Consider using at least 12 characters for better security")
        
        if re.search(r'(123|abc|qwerty)', password.lower()):
            suggestions.append("Avoid sequential patterns like '123' or 'abc'")
        
        return suggestions
    
    @staticmethod
    def calculate_score(
        entropy: float,
        policy_checks: Dict,
        breach_info: Dict
    ) -> Dict:
        """Calculate overall password strength score (0-100)"""
        score = 0
        
        # Entropy contribution (0-40 points)
        if entropy >= 80:
            score += 40
        elif entropy >= 60:
            score += 30
        elif entropy >= 40:
            score += 20
        elif entropy >= 20:
            score += 10
        
        # Policy compliance (0-40 points)
        passed_checks = sum(1 for v in policy_checks.values() if v)
        total_checks = len(policy_checks)
        score += int((passed_checks / total_checks) * 40)
        
        # Breach penalty (-50 points if breached)
        if breach_info.get("breached"):
            count = breach_info.get("count", 0)
            if count > 1000:
                score -= 50
            elif count > 100:
                score -= 30
            else:
                score -= 20
        
        # Ensure score is between 0-100
        score = max(0, min(100, score))
        
        # Determine strength rating
        if score >= 80:
            rating = "very_strong"
            color = "#16a34a"
        elif score >= 60:
            rating = "strong"
            color = "#65a30d"
        elif score >= 40:
            rating = "fair"
            color = "#f59e0b"
        elif score >= 20:
            rating = "weak"
            color = "#f97316"
        else:
            rating = "very_weak"
            color = "#dc2626"
        
        return {
            "score": score,
            "rating": rating,
            "color": color
        }
    
    @staticmethod
    async def analyze_password(
        password: str,
        custom_policy: Optional[Dict] = None,
        check_breaches: bool = True
    ) -> Dict:
        """Comprehensive password analysis"""
        try:
            # Calculate entropy
            entropy = PasswordService.calculate_entropy(password)
            
            # Estimate crack time
            crack_time = PasswordService.estimate_crack_time(entropy)
            
            # Check policy compliance
            policy_checks = PasswordService.check_policy(password, custom_policy)
            
            # Check breaches (if enabled)
            breach_info = {"breached": False, "count": 0, "checked": False}
            if check_breaches:
                breach_info = await PasswordService.check_breach(password)
            
            # Calculate overall score
            score_info = PasswordService.calculate_score(
                entropy,
                policy_checks,
                breach_info
            )
            
            # Generate suggestions
            suggestions = PasswordService.get_suggestions(password, policy_checks)
            
            return {
                "success": True,
                "analysis": {
                    "entropy": entropy,
                    "crack_time": crack_time,
                    "score": score_info,
                    "policy_checks": policy_checks,
                    "breach_info": breach_info,
                    "suggestions": suggestions,
                    "length": len(password),
                    "analyzed_at": datetime.utcnow()
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Password analysis failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    async def save_policy(
        db,
        user_email: str,
        policy_name: str,
        policy: Dict
    ) -> Optional[Dict]:
        """Save a custom password policy"""
        try:
            policies_collection = db["password_policies"]
            
            policy_id = f"policy_{user_email}_{policy_name}"
            
            policy_record = {
                "policy_id": policy_id,
                "user_email": user_email,
                "policy_name": policy_name,
                "policy": policy,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            await policies_collection.replace_one(
                {"policy_id": policy_id},
                policy_record,
                upsert=True
            )
            
            return policy_record
            
        except Exception as e:
            logger.error(f"❌ Failed to save policy: {str(e)}")
            return None
    
    @staticmethod
    async def get_user_policies(db, user_email: str) -> List[Dict]:
        """Get all custom policies for a user"""
        try:
            policies_collection = db["password_policies"]
            
            policies = await policies_collection.find({
                "user_email": user_email
            }).to_list(length=None)
            
            return policies
            
        except Exception as e:
            logger.error(f"❌ Failed to get policies: {str(e)}")
            return []