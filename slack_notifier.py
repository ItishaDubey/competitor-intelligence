"""
Slack Notification Module for Competitive Intelligence Agent
Sends Slack messages with report summaries
"""

import requests
import json
from datetime import datetime
import os

class SlackNotifier:
    def __init__(self, webhook_url):
        """
        Initialize Slack notifier
        
        Args:
            webhook_url: Slack webhook URL from Incoming Webhooks app
        """
        self.webhook_url = webhook_url
    
    def send_summary(self, digest_file):
        """
        Send Slack message with digest summary
        
        Args:
            digest_file: Path to JSON digest file
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load digest
            with open(digest_file, 'r') as f:
                digest = json.load(f)
            
            # Build Slack message
            message = {
                "text": "🤖 Daily Competitive Intelligence Report",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "🤖 Competitive Intelligence Report",
                            "emoji": True
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Report Date:* {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Changes Detected:*\n{digest['summary']['total_changes_detected']}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*News Mentions:*\n{digest['summary']['news_mentions']}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Social Mentions:*\n{digest['summary']['social_mentions_analyzed']}"
                            }
                        ]
                    }
                ]
            }
            
            # Add insights
            if digest.get('insights'):
                insights_text = "*Key Insights:*\n"
                for insight in digest['insights']:
                    priority_emoji = {
                        'high': '🔴',
                        'medium': '🟡',
                        'low': '🟢'
                    }.get(insight['priority'], '⚪')
                    
                    insights_text += f"{priority_emoji} {insight['insight']}\n"
                
                message["blocks"].append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": insights_text
                    }
                })
            
            # Add competitor changes
            if digest.get('competitor_changes'):
                changes_text = "*Competitor Changes:*\n"
                for change in digest['competitor_changes'][:5]:  # Show first 5
                    changes_text += f"• {change['competitor']} - {change['page']}\n"
                
                message["blocks"].append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": changes_text
                    }
                })
            
            # Add footer
            message["blocks"].extend([
                {
                    "type": "divider"
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "📊 View full report for detailed analysis"
                        }
                    ]
                }
            ])
            
            # Send to Slack
            response = requests.post(self.webhook_url, json=message)
            
            if response.status_code == 200:
                print("✅ Slack notification sent successfully!")
                return True
            else:
                print(f"❌ Failed to send Slack notification: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending Slack notification: {e}")
            return False
    
    def send_simple_message(self, text):
        """Send a simple text message to Slack"""
        try:
            message = {"text": text}
            response = requests.post(self.webhook_url, json=message)
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending message: {e}")
            return False

# Example usage
if __name__ == "__main__":
    # Configuration (use environment variable in production)
    SLACK_WEBHOOK = os.getenv('SLACK_WEBHOOK_URL', 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL')
    
    # Find latest digest
    import glob
    digest_files = glob.glob('intelligence_data/digest_*.json')
    if digest_files:
        latest_digest = max(digest_files, key=os.path.getctime)
        
        # Send Slack notification
        notifier = SlackNotifier(SLACK_WEBHOOK)
        notifier.send_summary(latest_digest)
    else:
        print("No digest files found. Run the agent first.")