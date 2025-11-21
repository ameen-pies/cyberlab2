import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from shared.config.settings import settings
import secrets
import logging

logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    def generate_mfa_code() -> str:
        """Generate a 6-digit MFA code"""
        return ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    
    @staticmethod
    async def send_mfa_code(email: str, code: str) -> bool:
        """Send MFA code via email"""
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = "Your MFA Code - CyberSec Platform"
            message["From"] = settings.EMAIL_FROM
            message["To"] = email
            
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <h2 style="color: #2c3e50; text-align: center;">🔐 CyberSec Platform</h2>
                        <p style="color: #34495e; font-size: 16px;">Your Multi-Factor Authentication code is:</p>
                        <div style="background-color: #3498db; color: white; font-size: 32px; font-weight: bold; text-align: center; padding: 20px; margin: 20px 0; border-radius: 5px; letter-spacing: 8px;">
                            {code}
                        </div>
                        <p style="color: #7f8c8d; font-size: 14px;">This code will expire in 5 minutes.</p>
                        <p style="color: #7f8c8d; font-size: 14px;">If you didn't request this code, please ignore this email.</p>
                        <hr style="border: none; border-top: 1px solid #ecf0f1; margin: 20px 0;">
                        <p style="color: #95a5a6; font-size: 12px; text-align: center;">CyberSec Platform - Secure Authentication System</p>
                    </div>
                </body>
            </html>
            """
            
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                start_tls=True
            )
            
            logger.info(f"MFA code sent successfully to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {email}: {str(e)}")
            return False
    
    @staticmethod
    async def send_verification_email(email: str, verification_link: str) -> bool:
        """Send account verification email"""
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = "Verify Your Account - CyberSec Platform"
            message["From"] = settings.EMAIL_FROM
            message["To"] = email
            
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px;">
                        <h2 style="color: #2c3e50;">Welcome to CyberSec Platform! 🎉</h2>
                        <p style="color: #34495e;">Thank you for registering. Please verify your email address:</p>
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{verification_link}" style="background-color: #3498db; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">Verify Email</a>
                        </div>
                        <p style="color: #7f8c8d; font-size: 14px;">This link will expire in 24 hours.</p>
                    </div>
                </body>
            </html>
            """
            
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                start_tls=True
            )
            
            logger.info(f"Verification email sent to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send verification email: {str(e)}")
            return False