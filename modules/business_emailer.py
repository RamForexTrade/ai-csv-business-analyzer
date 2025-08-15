"""
Business Email Module for AI CSV Business Analyzer
Supports multiple email providers and templates for curated business outreach
"""

import smtplib
import ssl
import os
import json
import pandas as pd
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formataddr
import requests
from typing import List, Dict, Optional
import asyncio
import time

class BusinessEmailer:
    def __init__(self):
        self.email_config = {}
        self.templates = {}
        self.sent_emails = []
        self.failed_emails = []
        
    def configure_smtp(self, smtp_server: str, port: int, email: str, password: str, sender_name: str = None):
        """Configure SMTP settings (Gmail, Outlook, etc.)"""
        self.email_config = {
            'type': 'smtp',
            'smtp_server': smtp_server,
            'port': port,
            'email': email,
            'password': password,
            'sender_name': sender_name or email
        }
        
    def configure_sendgrid(self, api_key: str, from_email: str, sender_name: str = None):
        """Configure SendGrid API"""
        self.email_config = {
            'type': 'sendgrid',
            'api_key': api_key,
            'from_email': from_email,
            'sender_name': sender_name or from_email
        }
        
    def configure_mailgun(self, api_key: str, domain: str, from_email: str, sender_name: str = None):
        """Configure Mailgun API"""
        self.email_config = {
            'type': 'mailgun',
            'api_key': api_key,
            'domain': domain,
            'from_email': from_email,
            'sender_name': sender_name or from_email
        }
    
    def test_email_config(self):
        """Test email configuration"""
        try:
            if self.email_config['type'] == 'smtp':
                return self._test_smtp()
            elif self.email_config['type'] == 'sendgrid':
                return self._test_sendgrid()
            elif self.email_config['type'] == 'mailgun':
                return self._test_mailgun()
            else:
                return False, "No email configuration found"
        except Exception as e:
            return False, f"Email test failed: {str(e)}"
    
    def _test_smtp(self):
        """Test SMTP connection"""
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['port']) as server:
                server.starttls(context=context)
                server.login(self.email_config['email'], self.email_config['password'])
                return True, "SMTP connection successful"
        except Exception as e:
            return False, f"SMTP test failed: {str(e)}"
    
    def _test_sendgrid(self):
        """Test SendGrid API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.email_config['api_key']}",
                "Content-Type": "application/json"
            }
            
            # Test with a simple API call to verify credentials
            response = requests.get(
                "https://api.sendgrid.com/v3/user/profile",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return True, "SendGrid API connection successful"
            else:
                return False, f"SendGrid API test failed: {response.status_code}"
        except Exception as e:
            return False, f"SendGrid test failed: {str(e)}"
    
    def _test_mailgun(self):
        """Test Mailgun API"""
        try:
            response = requests.get(
                f"https://api.mailgun.net/v3/{self.email_config['domain']}/stats/total",
                auth=("api", self.email_config['api_key']),
                timeout=10
            )
            
            if response.status_code == 200:
                return True, "Mailgun API connection successful"
            else:
                return False, f"Mailgun API test failed: {response.status_code}"
        except Exception as e:
            return False, f"Mailgun test failed: {str(e)}"
    
    def create_template(self, template_name: str, subject: str, html_body: str, text_body: str = None):
        """Create email template with placeholders"""
        self.templates[template_name] = {
            'subject': subject,
            'html_body': html_body,
            'text_body': text_body or html_body  # Fallback to HTML if no text provided
        }
    
    def get_default_templates(self):
        """Get pre-built email templates"""
        templates = {
            'business_intro': {
                'name': 'Business Introduction',
                'subject': 'Partnership Opportunity - {your_company_name}',
                'html_body': '''
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #2c3e50;">Dear {business_name} Team,</h2>
                        
                        <p>I hope this email finds you well. My name is <strong>{sender_name}</strong> from <strong>{your_company_name}</strong>.</p>
                        
                        <p>We came across your business while researching wood and timber companies, and we're impressed with your work in the industry.</p>
                        
                        <h3 style="color: #34495e;">Why We're Reaching Out:</h3>
                        <ul>
                            <li>We're looking to establish partnerships with quality wood/timber suppliers</li>
                            <li>Your business profile shows expertise in: {business_description}</li>
                            <li>We believe there could be mutual benefits in working together</li>
                        </ul>
                        
                        <p><strong>Next Steps:</strong><br>
                        We'd love to schedule a brief call to discuss potential collaboration opportunities. Would you be available for a 15-minute conversation this week?</p>
                        
                        <p>Best regards,<br>
                        <strong>{sender_name}</strong><br>
                        {your_company_name}<br>
                        Phone: {your_phone}<br>
                        Email: {your_email}</p>
                        
                        <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                        <p style="font-size: 12px; color: #666;">
                            This email was sent to {recipient_email}. If you'd prefer not to receive future emails, please reply with "UNSUBSCRIBE".
                        </p>
                    </div>
                </body>
                </html>
                '''
            },
            'supplier_inquiry': {
                'name': 'Supplier Inquiry',
                'subject': 'Timber Supply Inquiry - {your_company_name}',
                'html_body': '''
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #2c3e50;">Hello {business_name},</h2>
                        
                        <p>We are <strong>{your_company_name}</strong>, and we're currently sourcing high-quality timber and wood products for our upcoming projects.</p>
                        
                        <h3 style="color: #34495e;">Our Requirements:</h3>
                        <ul>
                            <li>Product Type: {product_requirements}</li>
                            <li>Estimated Volume: {volume_requirements}</li>
                            <li>Delivery Timeline: {timeline_requirements}</li>
                            <li>Quality Standards: {quality_requirements}</li>
                        </ul>
                        
                        <p>Based on our research, your company appears to specialize in areas that align with our needs.</p>
                        
                        <p><strong>Could you please provide:</strong></p>
                        <ol>
                            <li>Product catalog or specifications</li>
                            <li>Pricing information</li>
                            <li>Minimum order quantities</li>
                            <li>Delivery capabilities</li>
                        </ol>
                        
                        <p>We're looking forward to potentially establishing a long-term business relationship.</p>
                        
                        <p>Best regards,<br>
                        <strong>{sender_name}</strong><br>
                        Procurement Manager<br>
                        {your_company_name}<br>
                        Phone: {your_phone}<br>
                        Email: {your_email}</p>
                    </div>
                </body>
                </html>
                '''
            },
            'networking': {
                'name': 'Industry Networking',
                'subject': 'Connecting Within the Timber Industry',
                'html_body': '''
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #2c3e50;">Hello {business_name} Team,</h2>
                        
                        <p>I'm <strong>{sender_name}</strong> from <strong>{your_company_name}</strong>, reaching out to connect with fellow professionals in the timber and wood industry.</p>
                        
                        <p>Your company caught our attention due to your expertise in {business_description}.</p>
                        
                        <h3 style="color: #34495e;">Industry Collaboration Opportunities:</h3>
                        <ul>
                            <li>🤝 Knowledge sharing and best practices</li>
                            <li>🌱 Sustainability initiatives collaboration</li>
                            <li>📈 Market insights and trends discussion</li>
                            <li>🔗 Potential referral partnerships</li>
                        </ul>
                        
                        <p>Would you be interested in a brief networking call to explore how our companies might support each other in the industry?</p>
                        
                        <p>Looking forward to connecting,<br>
                        <strong>{sender_name}</strong><br>
                        {your_company_name}<br>
                        {your_email} | {your_phone}</p>
                    </div>
                </body>
                </html>
                '''
            }
        }
        
        # Add templates to the instance
        for template_id, template_data in templates.items():
            self.templates[template_id] = template_data
            
        return templates
    
    def send_single_email(self, to_email: str, template_name: str, variables: Dict, attachments: List = None):
        """Send a single email using specified template"""
        try:
            if template_name not in self.templates:
                return False, f"Template '{template_name}' not found"
            
            template = self.templates[template_name]
            
            # Replace variables in template
            subject = template['subject'].format(**variables)
            html_body = template['html_body'].format(**variables)
            text_body = template.get('text_body', '').format(**variables) if template.get('text_body') else None
            
            # Send based on configured method
            if self.email_config['type'] == 'smtp':
                return self._send_smtp(to_email, subject, html_body, text_body, attachments)
            elif self.email_config['type'] == 'sendgrid':
                return self._send_sendgrid(to_email, subject, html_body, text_body, attachments)
            elif self.email_config['type'] == 'mailgun':
                return self._send_mailgun(to_email, subject, html_body, text_body, attachments)
            else:
                return False, "No email configuration found"
                
        except Exception as e:
            return False, f"Email sending failed: {str(e)}"
    
    def _send_smtp(self, to_email: str, subject: str, html_body: str, text_body: str = None, attachments: List = None):
        """Send email via SMTP"""
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = formataddr((self.email_config['sender_name'], self.email_config['email']))
            message["To"] = to_email
            
            # Add text and HTML parts
            if text_body:
                text_part = MIMEText(text_body, "plain")
                message.attach(text_part)
            
            html_part = MIMEText(html_body, "html")
            message.attach(html_part)
            
            # Add attachments if any
            if attachments:
                for attachment_path in attachments:
                    if os.path.isfile(attachment_path):
                        with open(attachment_path, "rb") as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                        
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {os.path.basename(attachment_path)}'
                        )
                        message.attach(part)
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['port']) as server:
                server.starttls(context=context)
                server.login(self.email_config['email'], self.email_config['password'])
                server.sendmail(self.email_config['email'], to_email, message.as_string())
                
            return True, "Email sent successfully"
            
        except Exception as e:
            return False, f"SMTP sending failed: {str(e)}"
    
    def _send_sendgrid(self, to_email: str, subject: str, html_body: str, text_body: str = None, attachments: List = None):
        """Send email via SendGrid API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.email_config['api_key']}",
                "Content-Type": "application/json"
            }
            
            data = {
                "personalizations": [{"to": [{"email": to_email}]}],
                "from": {
                    "email": self.email_config['from_email'],
                    "name": self.email_config['sender_name']
                },
                "subject": subject,
                "content": [
                    {"type": "text/html", "value": html_body}
                ]
            }
            
            if text_body:
                data["content"].insert(0, {"type": "text/plain", "value": text_body})
            
            # TODO: Add attachment support for SendGrid
            
            response = requests.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 202:
                return True, "Email sent successfully via SendGrid"
            else:
                return False, f"SendGrid API error: {response.status_code} - {response.text}"
                
        except Exception as e:
            return False, f"SendGrid sending failed: {str(e)}"
    
    def _send_mailgun(self, to_email: str, subject: str, html_body: str, text_body: str = None, attachments: List = None):
        """Send email via Mailgun API"""
        try:
            data = {
                "from": f"{self.email_config['sender_name']} <{self.email_config['from_email']}>",
                "to": to_email,
                "subject": subject,
                "html": html_body
            }
            
            if text_body:
                data["text"] = text_body
            
            files = []
            if attachments:
                for attachment_path in attachments:
                    if os.path.isfile(attachment_path):
                        files.append(("attachment", (os.path.basename(attachment_path), open(attachment_path, "rb"))))
            
            response = requests.post(
                f"https://api.mailgun.net/v3/{self.email_config['domain']}/messages",
                auth=("api", self.email_config['api_key']),
                data=data,
                files=files,
                timeout=30
            )
            
            # Close file handles
            for _, (_, file_handle) in files:
                file_handle.close()
            
            if response.status_code == 200:
                return True, "Email sent successfully via Mailgun"
            else:
                return False, f"Mailgun API error: {response.status_code} - {response.text}"
                
        except Exception as e:
            return False, f"Mailgun sending failed: {str(e)}"
    
    async def send_bulk_emails(self, businesses_df: pd.DataFrame, template_name: str, 
                             base_variables: Dict, delay_seconds: float = 1.0,
                             progress_callback=None, status_callback=None):
        """Send bulk emails to businesses with email addresses"""
        
        # Filter businesses with email addresses
        businesses_with_email = businesses_df[
            (businesses_df['email'].notna()) & 
            (businesses_df['email'] != '') & 
            (businesses_df['email'] != 'Not found')
        ].copy()
        
        if len(businesses_with_email) == 0:
            return {
                'total_businesses': len(businesses_df),
                'emails_to_send': 0,
                'emails_sent': 0,
                'emails_failed': 0,
                'success_rate': 0
            }
        
        total_emails = len(businesses_with_email)
        sent_count = 0
        failed_count = 0
        
        self.sent_emails = []
        self.failed_emails = []
        
        for index, business in businesses_with_email.iterrows():
            try:
                # Update progress
                if progress_callback:
                    progress_callback(sent_count + failed_count, total_emails)
                
                if status_callback:
                    status_callback(f"Sending email to {business['business_name']} ({sent_count + failed_count + 1}/{total_emails})")
                
                # Prepare variables for this business
                email_variables = base_variables.copy()
                email_variables.update({
                    'business_name': business.get('business_name', 'Valued Partner'),
                    'recipient_email': business.get('email', ''),
                    'business_description': business.get('description', 'your business activities'),
                    'business_address': business.get('address', 'your location'),
                    'business_city': business.get('city', ''),
                    'business_phone': business.get('phone', ''),
                    'business_website': business.get('website', '')
                })
                
                # Send email
                success, message = self.send_single_email(
                    business['email'], 
                    template_name, 
                    email_variables
                )
                
                # Record result
                email_record = {
                    'business_name': business['business_name'],
                    'email': business['email'],
                    'timestamp': datetime.now().isoformat(),
                    'template': template_name,
                    'message': message
                }
                
                if success:
                    sent_count += 1
                    self.sent_emails.append(email_record)
                else:
                    failed_count += 1
                    email_record['error'] = message
                    self.failed_emails.append(email_record)
                
                # Add delay to avoid rate limiting
                if delay_seconds > 0:
                    await asyncio.sleep(delay_seconds)
                    
            except Exception as e:
                failed_count += 1
                error_record = {
                    'business_name': business.get('business_name', 'Unknown'),
                    'email': business.get('email', ''),
                    'timestamp': datetime.now().isoformat(),
                    'template': template_name,
                    'error': str(e)
                }
                self.failed_emails.append(error_record)
        
        # Final summary
        summary = {
            'total_businesses': len(businesses_df),
            'emails_to_send': total_emails,
            'emails_sent': sent_count,
            'emails_failed': failed_count,
            'success_rate': (sent_count / total_emails * 100) if total_emails > 0 else 0
        }
        
        return summary
    
    def get_email_log(self):
        """Get email sending log"""
        return {
            'sent_emails': self.sent_emails,
            'failed_emails': self.failed_emails,
            'total_sent': len(self.sent_emails),
            'total_failed': len(self.failed_emails)
        }
    
    def save_email_log(self, filename: str = None):
        """Save email log to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"email_log_{timestamp}.json"
        
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'email_config_type': self.email_config.get('type', 'unknown'),
            'sent_emails': self.sent_emails,
            'failed_emails': self.failed_emails,
            'summary': {
                'total_sent': len(self.sent_emails),
                'total_failed': len(self.failed_emails),
                'success_rate': len(self.sent_emails) / (len(self.sent_emails) + len(self.failed_emails)) * 100 if (len(self.sent_emails) + len(self.failed_emails)) > 0 else 0
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        return filename

# Predefined email provider configurations
EMAIL_PROVIDERS = {
    'gmail': {
        'smtp_server': 'smtp.gmail.com',
        'port': 587,
        'instructions': 'Use your Gmail address and App Password (not regular password)'
    },
    'outlook': {
        'smtp_server': 'smtp-mail.outlook.com',
        'port': 587,
        'instructions': 'Use your Outlook address and password'
    },
    'yahoo': {
        'smtp_server': 'smtp.mail.yahoo.com',
        'port': 587,
        'instructions': 'Use your Yahoo address and App Password'
    }
}

def get_email_provider_config(provider: str):
    """Get configuration for popular email providers"""
    return EMAIL_PROVIDERS.get(provider.lower(), None)
