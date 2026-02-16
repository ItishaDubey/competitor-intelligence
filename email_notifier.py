"""
Email Notification Module for Competitive Intelligence Agent
Sends email notifications with reports
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import os
import json

class EmailNotifier:
    def __init__(self, sender_email, sender_password, receiver_email):
        """
        Initialize email notifier
        
        Args:
            sender_email: Sender's email address (e.g., your-email@gmail.com)
            sender_password: App password (for Gmail, use App Password)
            receiver_email: Receiver's email address
        """
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.receiver_email = receiver_email
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
    
    def create_summary_text(self, digest_file):
        """Create a text summary from the digest"""
        try:
            with open(digest_file, 'r') as f:
                digest = json.load(f)
            
            summary = f"""
Competitive Intelligence Report - {datetime.now().strftime('%Y-%m-%d')}

SUMMARY
-------
Changes Detected: {digest['summary']['total_changes_detected']}
News Mentions: {digest['summary']['news_mentions']}
Social Mentions Analyzed: {digest['summary']['social_mentions_analyzed']}

"""
            
            # Add insights
            if digest.get('insights'):
                summary += "KEY INSIGHTS\n------------\n"
                for insight in digest['insights']:
                    summary += f"• [{insight['priority'].upper()}] {insight['insight']}\n"
                    summary += f"  Action: {insight['action']}\n\n"
            
            # Add competitor changes
            if digest.get('competitor_changes'):
                summary += "COMPETITOR CHANGES\n------------------\n"
                for change in digest['competitor_changes']:
                    summary += f"• {change['competitor']} - {change['page']}\n"
                    summary += f"  {change['url']}\n\n"
            
            summary += "\nSee attached HTML report for full details.\n"
            
            return summary
            
        except Exception as e:
            return f"Error creating summary: {e}"
    
    def send_report(self, digest_file, html_report, subject=None):
        """
        Send email with digest and HTML report
        
        Args:
            digest_file: Path to JSON digest file
            html_report: Path to HTML report file
            subject: Email subject (optional)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.receiver_email
            msg['Subject'] = subject or f"Competitive Intelligence Report - {datetime.now().strftime('%Y-%m-%d')}"
            
            # Email body
            body = self.create_summary_text(digest_file)
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach HTML report
            if os.path.exists(html_report):
                with open(html_report, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename={os.path.basename(html_report)}'
                    )
                    msg.attach(part)
            
            # Attach JSON digest
            if os.path.exists(digest_file):
                with open(digest_file, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename={os.path.basename(digest_file)}'
                    )
                    msg.attach(part)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()
            
            print(f"✅ Email sent successfully to {self.receiver_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False

# Example usage
if __name__ == "__main__":
    # Configuration (use environment variables in production)
    SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'your-email@gmail.com')
    SENDER_PASSWORD = os.getenv('SENDER_PASSWORD', 'your-app-password')
    RECEIVER_EMAIL = os.getenv('RECEIVER_EMAIL', 'recipient@example.com')
    
    # Find latest digest
    import glob
    digest_files = glob.glob('intelligence_data/digest_*.json')
    if digest_files:
        latest_digest = max(digest_files, key=os.path.getctime)
        html_report = 'competitive_intelligence_report.html'
        
        # Send email
        notifier = EmailNotifier(SENDER_EMAIL, SENDER_PASSWORD, RECEIVER_EMAIL)
        notifier.send_report(latest_digest, html_report)
    else:
        print("No digest files found. Run the agent first.")