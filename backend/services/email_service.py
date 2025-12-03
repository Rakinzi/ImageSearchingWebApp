
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Optional, Any
from jinja2 import Environment, FileSystemLoader, Template
from flask import current_app
import os

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = None
        self.template_env = None
        self._initialize_templates()
    
    def _initialize_templates(self):
        try:
            templates_dir = os.path.join(os.path.dirname(__file__), '..', 'templates', 'emails')
            if os.path.exists(templates_dir):
                self.template_env = Environment(
                    loader=FileSystemLoader(templates_dir),
                    autoescape=True
                )
            else:
                logger.warning(f"Email templates directory not found: {templates_dir}")
                self.template_env = Environment(loader=FileSystemLoader('.'))
        except Exception as e:
            logger.error(f"Failed to initialize email templates: {str(e)}")
            self.template_env = Environment(loader=FileSystemLoader('.'))
    
    def _get_smtp_connection(self):
        try:
            server = smtplib.SMTP(
                current_app.config['MAIL_SERVER'],
                current_app.config['MAIL_PORT']
            )
            
            if current_app.config.get('MAIL_USE_TLS', True):
                server.starttls()
            
            if current_app.config.get('MAIL_USERNAME') and current_app.config.get('MAIL_PASSWORD'):
                server.login(
                    current_app.config['MAIL_USERNAME'],
                    current_app.config['MAIL_PASSWORD']
                )
            
            return server
        except Exception as e:
            logger.error(f"Failed to establish SMTP connection: {str(e)}")
            raise Exception(f"SMTP connection failed: {str(e)}")
    
    def send_email(self, to_email: str, subject: str, 
                   html_content: str = None, text_content: str = None,
                   attachments: List[Dict[str, Any]] = None,
                   cc_emails: List[str] = None, 
                   bcc_emails: List[str] = None) -> bool:
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = current_app.config.get('MAIL_DEFAULT_SENDER')
            msg['To'] = to_email
            
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
            
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            if html_content:
                html_part = MIMEText(html_content, 'html', 'utf-8')
                msg.attach(html_part)
            
            if attachments:
                for attachment in attachments:
                    self._add_attachment(msg, attachment)
            
            recipients = [to_email]
            if cc_emails:
                recipients.extend(cc_emails)
            if bcc_emails:
                recipients.extend(bcc_emails)
            
            with self._get_smtp_connection() as server:
                server.send_message(msg, to_addrs=recipients)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def _add_attachment(self, msg: MIMEMultipart, attachment: Dict[str, Any]):
        try:
            filename = attachment.get('filename', 'attachment')
            content = attachment.get('content')
            content_type = attachment.get('content_type', 'application/octet-stream')
            
            if isinstance(content, str):
                content = content.encode('utf-8')
            
            part = MIMEBase(*content_type.split('/', 1))
            part.set_payload(content)
            encoders.encode_base64(part)
            
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            
            msg.attach(part)
            
        except Exception as e:
            logger.error(f"Failed to add attachment {attachment.get('filename', 'unknown')}: {str(e)}")
    
    def send_template_email(self, to_email: str, subject: str, 
                          template_name: str, template_data: Dict[str, Any],
                          attachments: List[Dict[str, Any]] = None) -> bool:
        try:
            if self.template_env:
                try:
                    template = self.template_env.get_template(template_name)
                    html_content = template.render(**template_data)
                except Exception as template_error:
                    logger.warning(f"Template rendering failed: {str(template_error)}")
                    html_content = self._get_fallback_template(template_name, template_data)
            else:
                html_content = self._get_fallback_template(template_name, template_data)
            
            return self.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                attachments=attachments
            )
            
        except Exception as e:
            logger.error(f"Template email sending failed: {str(e)}")
            return False
    
    def _get_fallback_template(self, template_name: str, data: Dict[str, Any]) -> str:
        fallback_templates = {
            'verification_email.html': self._verification_email_fallback,
            'reset_password_email.html': self._reset_password_email_fallback,
            'welcome_email.html': self._welcome_email_fallback,
            'processing_complete.html': self._processing_complete_fallback,
            'processing_failed.html': self._processing_failed_fallback
        }
        
        template_func = fallback_templates.get(template_name, self._generic_fallback)
        return template_func(data)
    
    def _verification_email_fallback(self, data: Dict[str, Any]) -> str:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Verify Your Email</title>
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                     margin: 0; padding: 40px 20px;
                     background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
            <div style="max-width: 600px; margin: 0 auto; background: white;
                        border-radius: 16px; overflow: hidden;
                        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                           padding: 40px 30px; text-align: center;">
                    <div style="font-size: 48px; margin-bottom: 10px;">🔍</div>
                    <h1 style="color: white; font-size: 28px; margin: 0;
                               text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);">Image Search</h1>
                    <p style="color: rgba(255, 255, 255, 0.9); font-size: 16px; margin-top: 8px;">
                        AI-Powered Visual Discovery
                    </p>
                </div>
                <div style="padding: 50px 40px;">
                    <h2 style="color: #1a1a1a; font-size: 24px; margin-bottom: 20px;">
                        Hello {data.get('name', 'User')}! 👋
                    </h2>
                    <p style="color: #4a5568; line-height: 1.8; margin-bottom: 30px;">
                        Welcome to <strong>Image Search</strong>! Please verify your email address to unlock
                        the full power of our AI-driven image search platform.
                    </p>
                    <div style="text-align: center; margin: 40px 0;">
                        <a href="{data.get('verification_url', '#')}"
                           style="display: inline-block;
                                  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                  color: white; padding: 18px 45px; text-decoration: none;
                                  border-radius: 50px; font-weight: 600; font-size: 16px;
                                  box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
                                  text-transform: uppercase; letter-spacing: 0.5px;">
                            Verify Email Address
                        </a>
                    </div>
                    <p style="color: #4a5568; font-size: 14px; margin: 10px 0;">
                        Or copy and paste this link:
                    </p>
                    <div style="background: linear-gradient(135deg, rgba(102, 126, 234, 0.05), rgba(118, 75, 162, 0.05));
                               border: 1px solid rgba(102, 126, 234, 0.2); padding: 15px;
                               border-radius: 8px; word-break: break-all; color: #667eea;
                               font-size: 13px; font-family: monospace;">
                        {data.get('verification_url', '#')}
                    </div>
                    <div style="background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(251, 191, 36, 0.1));
                               border-left: 4px solid #f59e0b; padding: 20px;
                               border-radius: 8px; margin: 30px 0;">
                        <div style="font-size: 24px; margin-bottom: 8px;">⏰</div>
                        <p style="color: #92400e; font-size: 14px; margin: 0; line-height: 1.6;">
                            <strong style="color: #78350f;">Important:</strong> This link expires in 24 hours.
                            If you didn't create an account, safely ignore this email.
                        </p>
                    </div>
                </div>
                <div style="background: #f7fafc; padding: 30px; text-align: center;
                           border-top: 1px solid #e2e8f0;">
                    <p style="color: #718096; font-size: 13px; margin: 0;">
                        &copy; 2025 Image Search. All rights reserved.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _reset_password_email_fallback(self, data: Dict[str, Any]) -> str:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Reset Your Password</title>
        </head>
        <body style="font-family: Arial, sans-serif; margin: 40px;">
            <div style="max-width: 600px; margin: 0 auto;">
                <h2 style="color: #333;">Reset Your Password</h2>
                <p>Hello {data.get('name', 'User')},</p>
                <p>We received a request to reset your password. Click the button below to create a new password:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{data.get('reset_url', '#')}" 
                       style="background-color: #28a745; color: white; padding: 12px 24px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Reset Password
                    </a>
                </div>
                <p>If the button doesn't work, copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #666;">
                    {data.get('reset_url', '#')}
                </p>
                <p style="color: #666; font-size: 14px; margin-top: 30px;">
                    This reset link will expire in 1 hour. If you didn't request a password reset, 
                    please ignore this email.
                </p>
            </div>
        </body>
        </html>
        """
    
    def _welcome_email_fallback(self, data: Dict[str, Any]) -> str:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Welcome to Image Search</title>
        </head>
        <body style="font-family: Arial, sans-serif; margin: 40px;">
            <div style="max-width: 600px; margin: 0 auto;">
                <h2 style="color: #333;">Welcome to Image Search!</h2>
                <p>Hello {data.get('name', 'User')},</p>
                <p>Welcome to Image Search! Your account has been successfully verified and you can now start using our platform.</p>
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #495057;">Getting Started:</h3>
                    <ul style="color: #6c757d;">
                        <li>Upload your first images</li>
                        <li>Use our AI-powered search to find images by description</li>
                        <li>Organize faces with automatic face detection</li>
                        <li>Explore advanced features in your dashboard</li>
                    </ul>
                </div>
                <p>If you have any questions, please don't hesitate to contact our support team.</p>
                <p>Happy searching!</p>
            </div>
        </body>
        </html>
        """
    
    def _processing_complete_fallback(self, data: Dict[str, Any]) -> str:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Processing Complete</title>
        </head>
        <body style="font-family: Arial, sans-serif; margin: 40px;">
            <div style="max-width: 600px; margin: 0 auto;">
                <h2 style="color: #28a745;">Processing Complete!</h2>
                <p>Hello {data.get('name', 'User')},</p>
                <p>Your image processing has been completed successfully.</p>
                <div style="background-color: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <strong>Processing Summary:</strong><br>
                    Images processed: {data.get('images_processed', 0)}<br>
                    Faces detected: {data.get('faces_detected', 0)}<br>
                    Processing time: {data.get('processing_time', 'N/A')}
                </div>
                <p>You can now search and explore your processed images in your dashboard.</p>
            </div>
        </body>
        </html>
        """
    
    def _processing_failed_fallback(self, data: Dict[str, Any]) -> str:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Processing Failed</title>
        </head>
        <body style="font-family: Arial, sans-serif; margin: 40px;">
            <div style="max-width: 600px; margin: 0 auto;">
                <h2 style="color: #dc3545;">Processing Failed</h2>
                <p>Hello {data.get('name', 'User')},</p>
                <p>Unfortunately, there was an issue processing some of your images.</p>
                <div style="background-color: #f8d7da; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <strong>Error Details:</strong><br>
                    Failed images: {data.get('failed_count', 0)}<br>
                    Error message: {data.get('error_message', 'Unknown error')}
                </div>
                <p>Please try uploading your images again or contact support if the problem persists.</p>
            </div>
        </body>
        </html>
        """
    
    def _generic_fallback(self, data: Dict[str, Any]) -> str:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Image Search Notification</title>
        </head>
        <body style="font-family: Arial, sans-serif; margin: 40px;">
            <div style="max-width: 600px; margin: 0 auto;">
                <h2 style="color: #333;">Image Search Notification</h2>
                <p>Hello {data.get('name', 'User')},</p>
                <p>{data.get('message', 'You have a new notification from Image Search.')}</p>
            </div>
        </body>
        </html>
        """
    
    def send_verification_email(self, user_email: str, user_name: str, 
                              verification_token: str) -> bool:
        verification_url = f"{current_app.config['FRONTEND_URL']}/verify-email?token={verification_token}"
        
        return self.send_template_email(
            to_email=user_email,
            subject="Verify Your Email - Image Search",
            template_name="verification_email.html",
            template_data={
                "name": user_name,
                "verification_url": verification_url
            }
        )
    
    def send_password_reset_email(self, user_email: str, user_name: str, 
                                reset_token: str) -> bool:
        reset_url = f"{current_app.config['FRONTEND_URL']}/reset-password?token={reset_token}"
        
        return self.send_template_email(
            to_email=user_email,
            subject="Reset Your Password - Image Search",
            template_name="reset_password_email.html",
            template_data={
                "name": user_name,
                "reset_url": reset_url
            }
        )
    
    def send_welcome_email(self, user_email: str, user_name: str) -> bool:
        return self.send_template_email(
            to_email=user_email,
            subject="Welcome to Image Search!",
            template_name="welcome_email.html",
            template_data={
                "name": user_name
            }
        )
    
    def send_processing_complete_email(self, user_email: str, user_name: str,
                                     processing_results: Dict[str, Any]) -> bool:
        return self.send_template_email(
            to_email=user_email,
            subject="Image Processing Complete - Image Search",
            template_name="processing_complete.html",
            template_data={
                "name": user_name,
                "images_processed": processing_results.get('images_processed', 0),
                "faces_detected": processing_results.get('faces_detected', 0),
                "processing_time": processing_results.get('processing_time', 'N/A')
            }
        )
    
    def send_processing_failed_email(self, user_email: str, user_name: str,
                                   error_details: Dict[str, Any]) -> bool:
        return self.send_template_email(
            to_email=user_email,
            subject="Image Processing Failed - Image Search",
            template_name="processing_failed.html",
            template_data={
                "name": user_name,
                "failed_count": error_details.get('failed_count', 0),
                "error_message": error_details.get('error_message', 'Unknown error')
            }
        )
    
    def send_bulk_email(self, recipients: List[Dict[str, str]], 
                       subject: str, template_name: str,
                       common_data: Dict[str, Any] = None) -> Dict[str, Any]:
        results = {
            'successful': [],
            'failed': [],
            'total_sent': 0,
            'total_failed': 0
        }
        
        common_data = common_data or {}
        
        for recipient in recipients:
            try:
                email = recipient.get('email')
                name = recipient.get('name', 'User')
                
                if not email:
                    results['failed'].append({
                        'email': 'unknown',
                        'error': 'No email address provided'
                    })
                    continue
                
                template_data = {**common_data, 'name': name}
                template_data.update(recipient.get('custom_data', {}))
                
                if self.send_template_email(email, subject, template_name, template_data):
                    results['successful'].append(email)
                    results['total_sent'] += 1
                else:
                    results['failed'].append({
                        'email': email,
                        'error': 'Failed to send email'
                    })
                    results['total_failed'] += 1
                    
            except Exception as e:
                results['failed'].append({
                    'email': recipient.get('email', 'unknown'),
                    'error': str(e)
                })
                results['total_failed'] += 1
        
        return results
    
    def test_email_configuration(self) -> Dict[str, Any]:
        try:
            required_config = ['MAIL_SERVER', 'MAIL_PORT', 'MAIL_DEFAULT_SENDER']
            missing_config = [
                key for key in required_config 
                if not current_app.config.get(key)
            ]
            
            if missing_config:
                return {
                    'healthy': False,
                    'error': f'Missing configuration: {", ".join(missing_config)}'
                }
            
            try:
                with self._get_smtp_connection() as server:
                    server.noop()
                
                return {
                    'healthy': True,
                    'smtp_server': current_app.config['MAIL_SERVER'],
                    'smtp_port': current_app.config['MAIL_PORT'],
                    'sender': current_app.config['MAIL_DEFAULT_SENDER'],
                    'tls_enabled': current_app.config.get('MAIL_USE_TLS', True),
                    'authentication': bool(current_app.config.get('MAIL_USERNAME'))
                }
                
            except Exception as smtp_error:
                return {
                    'healthy': False,
                    'error': f'SMTP connection failed: {str(smtp_error)}'
                }
                
        except Exception as e:
            logger.error(f"Email configuration test failed: {str(e)}")
            return {
                'healthy': False,
                'error': str(e)
            }
    
    def health_check(self) -> Dict[str, Any]:
        return self.test_email_configuration()