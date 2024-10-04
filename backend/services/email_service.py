import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader
from flask import current_app


class EmailService:
    def __init__(self):
        self.template_env = Environment(
            loader=FileSystemLoader('templates')
        )

    def send_email(self, to_email, subject, template_name, template_data):
        """Send an email using the specified template and data."""
        try:
            # Get template and render it with data
            template = self.template_env.get_template(template_name)
            html_content = template.render(**template_data)

            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = current_app.config['MAIL_DEFAULT_SENDER']
            msg['To'] = to_email

            # Add HTML content
            msg.attach(MIMEText(html_content, 'html'))

            # Create SMTP connection
            with smtplib.SMTP(current_app.config['MAIL_SERVER'],
                              current_app.config['MAIL_PORT']) as server:
                if current_app.config['MAIL_USE_TLS']:
                    server.starttls()

                server.login(
                    current_app.config['MAIL_USERNAME'],
                    current_app.config['MAIL_PASSWORD']
                )

                server.send_message(msg)

            return True
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False

    def send_verification_email(self, user_email, user_name, verification_token):
        """Send verification email to user."""
        verification_url = f"{current_app.config['FRONTEND_URL']}/verify-email?token={verification_token}"

        return self.send_email(
            to_email=user_email,
            subject="Verify Your Email",
            template_name="verification_email.html",
            template_data={
                "name": user_name,
                "verification_url": verification_url
            }
        )

    def send_password_reset_email(self, user_email, user_name, reset_token):
        """Send password reset email to user."""
        reset_url = f"{current_app.config['FRONTEND_URL']}/reset-password?token={reset_token}"

        return self.send_email(
            to_email=user_email,
            subject="Reset Your Password",
            template_name="reset_password_email.html",
            template_data={
                "name": user_name,
                "reset_url": reset_url
            }
        )
