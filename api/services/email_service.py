import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
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
            message["Subject"] = "Your MFA Code - CyberLab Platform"
            message["From"] = settings.EMAIL_FROM
            message["To"] = email
            
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <h2 style="color: #2c3e50; text-align: center;">🔐 CyberLab Platform</h2>
                        <p style="color: #34495e; font-size: 16px;">Your Multi-Factor Authentication code is:</p>
                        <div style="background-color: #3498db; color: white; font-size: 32px; font-weight: bold; text-align: center; padding: 20px; margin: 20px 0; border-radius: 5px; letter-spacing: 8px;">
                            {code}
                        </div>
                        <p style="color: #7f8c8d; font-size: 14px;">This code will expire in 5 minutes.</p>
                        <p style="color: #7f8c8d; font-size: 14px;">If you didn't request this code, please ignore this email.</p>
                        <hr style="border: none; border-top: 1px solid #ecf0f1; margin: 20px 0;">
                        <p style="color: #95a5a6; font-size: 12px; text-align: center;">CyberLab Platform - Secure Authentication System</p>
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
    async def send_encrypted_data(
        recipient_email: str,
        encrypted_data: str,
        encryption_type: str,
        sender_email: str,
        salt: str = None,
        key: str = None,
        additional_info: dict = None
    ) -> bool:
        """Send encrypted text data via email"""
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = f"🔒 Encrypted Data - {encryption_type.upper()}"
            message["From"] = settings.EMAIL_FROM
            message["To"] = recipient_email
            
            # Determine what decryption info to show
            decryption_info = ""
            if salt:
                decryption_info = f"""
                <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <strong style="color: #856404;">🔑 Decryption Information:</strong><br>
                    <strong>Salt:</strong> <code style="background: #f8f9fa; padding: 5px; display: block; margin-top: 5px; word-break: break-all;">{salt}</code>
                    <p style="margin-top: 10px; color: #856404; font-size: 13px;">
                        ⚠️ You need BOTH the password AND the salt above to decrypt this data.
                    </p>
                </div>
                """
            elif key:
                decryption_info = f"""
                <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <strong style="color: #856404;">🔑 Decryption Key:</strong><br>
                    <code style="background: #f8f9fa; padding: 5px; display: block; margin-top: 5px; word-break: break-all;">{key}</code>
                    <p style="margin-top: 10px; color: #856404; font-size: 13px;">
                        ⚠️ Keep this key secure! You need it to decrypt the data.
                    </p>
                </div>
                """
            
            additional_info_html = ""
            if additional_info:
                additional_info_html = f"""
                <div style="background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <strong style="color: #004085;">ℹ️ Encryption Process:</strong><br>
                    <ul style="color: #004085; font-size: 13px; line-height: 1.6;">
                        <li>{additional_info.get('at_rest', '')}</li>
                        <li>{additional_info.get('in_transit', '')}</li>
                        <li>{additional_info.get('real_world', '')}</li>
                    </ul>
                </div>
                """
            
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
                    <div style="max-width: 700px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <h2 style="color: #2c3e50; text-align: center;">🔒 CyberLab Platform</h2>
                        <h3 style="color: #34495e;">Encrypted Data Received</h3>
                        
                        <p style="color: #555; font-size: 15px;">
                            <strong>{sender_email}</strong> has sent you encrypted data using <strong>{encryption_type}</strong> encryption.
                        </p>
                        
                        <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                            <strong style="color: #495057;">📦 Encrypted Content:</strong><br>
                            <textarea readonly style="width: 100%; height: 120px; margin-top: 10px; padding: 10px; font-family: 'Courier New', monospace; font-size: 12px; border: 1px solid #dee2e6; border-radius: 4px; resize: vertical;">{encrypted_data[:500]}{"..." if len(encrypted_data) > 500 else ""}</textarea>
                            <p style="color: #6c757d; font-size: 12px; margin-top: 5px;">
                                Total length: {len(encrypted_data)} characters
                            </p>
                        </div>
                        
                        {decryption_info}
                        {additional_info_html}
                        
                        <div style="background: #d1ecf1; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <strong style="color: #0c5460;">💡 How to Decrypt:</strong>
                            <ol style="color: #0c5460; font-size: 13px; line-height: 1.6; margin-top: 10px;">
                                <li>Log in to the CyberLab Platform</li>
                                <li>Go to the Encryption Service section</li>
                                <li>Select the appropriate decryption method</li>
                                <li>Paste the encrypted data and decryption information above</li>
                            </ol>
                        </div>
                        
                        <hr style="border: none; border-top: 1px solid #ecf0f1; margin: 20px 0;">
                        <p style="color: #95a5a6; font-size: 12px; text-align: center;">
                            CyberLab Platform - Secure Data Encryption & Transmission<br>
                            This is an automated message. Do not reply to this email.
                        </p>
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
            
            logger.info(f"Encrypted data sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send encrypted data to {recipient_email}: {str(e)}")
            return False
    
    @staticmethod
    async def send_encrypted_file(
        recipient_email: str,
        encrypted_data: str,
        filename: str,
        encryption_type: str,
        sender_email: str,
        salt: str = None,
        key: str = None,
        additional_info: dict = None
    ) -> bool:
        """Send encrypted file data via email with attachment"""
        try:
            message = MIMEMultipart("mixed")
            message["Subject"] = f"🔒 Encrypted File: {filename}"
            message["From"] = settings.EMAIL_FROM
            message["To"] = recipient_email
            
            # Determine what decryption info to show
            decryption_credentials = ""
            if salt:
                decryption_credentials = f"""
                <div style="background: #fff3cd; padding: 20px; border-radius: 8px; margin: 20px 0; border: 2px solid #f59e0b;">
                    <h3 style="color: #92400e; margin-top: 0;">🔑 DECRYPTION CREDENTIALS</h3>
                    <div style="background: white; padding: 15px; border-radius: 6px; margin: 10px 0;">
                        <p style="margin: 0 0 10px 0; color: #78350f;"><strong>Password:</strong> (You should have this separately)</p>
                        <p style="margin: 0; color: #78350f;"><strong>Salt:</strong></p>
                        <code style="background: #fef3c7; padding: 10px; display: block; margin-top: 5px; word-break: break-all; border-radius: 4px; color: #78350f; font-size: 13px;">{salt}</code>
                    </div>
                    <p style="color: #92400e; font-size: 14px; margin: 15px 0 0 0; font-weight: bold;">
                        ⚠️ SAVE THESE CREDENTIALS! You need BOTH the password AND salt to decrypt.
                    </p>
                </div>
                """
            elif key:
                decryption_credentials = f"""
                <div style="background: #fff3cd; padding: 20px; border-radius: 8px; margin: 20px 0; border: 2px solid #f59e0b;">
                    <h3 style="color: #92400e; margin-top: 0;">🔑 DECRYPTION KEY</h3>
                    <div style="background: white; padding: 15px; border-radius: 6px; margin: 10px 0;">
                        <code style="background: #fef3c7; padding: 10px; display: block; word-break: break-all; border-radius: 4px; color: #78350f; font-size: 13px;">{key}</code>
                    </div>
                    <p style="color: #92400e; font-size: 14px; margin: 15px 0 0 0; font-weight: bold;">
                        ⚠️ SAVE THIS KEY! You need it to decrypt the file.
                    </p>
                </div>
                """
            
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
                    <div style="max-width: 700px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <h2 style="color: #2c3e50; text-align: center; margin-bottom: 10px;">🔒 CyberLab Platform</h2>
                        <h3 style="color: #34495e; text-align: center; margin-top: 0;">Encrypted File Received</h3>
                        
                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <p style="color: white; font-size: 16px; margin: 0; text-align: center;">
                                <strong>{sender_email}</strong> sent you an encrypted file
                            </p>
                        </div>
                        
                        <div style="background: #e8f5e9; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #4caf50;">
                            <h4 style="color: #2e7d32; margin-top: 0;">📎 File Information</h4>
                            <table style="width: 100%; color: #2e7d32;">
                                <tr>
                                    <td style="padding: 5px 0;"><strong>Original Filename:</strong></td>
                                    <td style="padding: 5px 0;">{filename}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 5px 0;"><strong>Encrypted File:</strong></td>
                                    <td style="padding: 5px 0;">{filename}.enc</td>
                                </tr>
                                <tr>
                                    <td style="padding: 5px 0;"><strong>Encryption Method:</strong></td>
                                    <td style="padding: 5px 0;">{encryption_type.upper()}</td>
                                </tr>
                            </table>
                        </div>
                        
                        <div style="background: #e3f2fd; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #2196f3;">
                            <h4 style="color: #1565c0; margin-top: 0;">📥 Attachment</h4>
                            <p style="color: #1565c0; margin: 10px 0;">
                                The encrypted file <strong>{filename}.enc</strong> is attached to this email.
                            </p>
                            <p style="color: #1565c0; margin: 10px 0; font-size: 14px;">
                                Download the attachment before proceeding with decryption.
                            </p>
                        </div>
                        
                        {decryption_credentials}
                        
                        <div style="background: #f3e5f5; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #9c27b0;">
                            <h4 style="color: #6a1b9a; margin-top: 0;">💡 Decryption Steps</h4>
                            <ol style="color: #6a1b9a; line-height: 1.8; padding-left: 20px;">
                                <li><strong>Download</strong> the attached <code>{filename}.enc</code> file</li>
                                <li><strong>Save</strong> the decryption credentials shown above</li>
                                <li><strong>Go to</strong> CyberLab Platform → Encryption Service</li>
                                <li><strong>Select</strong> the appropriate file decryption tab</li>
                                <li><strong>Upload</strong> the .enc file</li>
                                <li><strong>Enter</strong> the password/key and salt</li>
                                <li><strong>Download</strong> your decrypted file!</li>
                            </ol>
                        </div>
                        
                        <hr style="border: none; border-top: 1px solid #ecf0f1; margin: 30px 0;">
                        <p style="color: #95a5a6; font-size: 12px; text-align: center; margin: 0;">
                            CyberLab Platform - Secure File Encryption & Transmission<br>
                            This is an automated message. Do not reply to this email.
                        </p>
                    </div>
                </body>
            </html>
            """
            
            # Attach HTML content
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Attach the encrypted file
            attachment = MIMEBase('application', 'octet-stream')
            attachment.set_payload(encrypted_data.encode('utf-8'))
            encoders.encode_base64(attachment)
            attachment.add_header(
                'Content-Disposition',
                f'attachment; filename="{filename}.enc"'
            )
            message.attach(attachment)
            
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                start_tls=True
            )
            
            logger.info(f"✅ Encrypted file sent successfully to {recipient_email} with attachment {filename}.enc")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send encrypted file to {recipient_email}: {str(e)}")
            return False