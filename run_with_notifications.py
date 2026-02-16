"""
Competitive Intelligence Agent - Main Runner with Notifications
Runs the agent and sends notifications
"""

import os
import sys
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

def run_agent():
    """Run the main competitive intelligence agent"""
    print("🤖 Starting Competitive Intelligence Agent...")
    from competitive_intelligence_agent import CompetitiveIntelligenceAgent
    
    agent = CompetitiveIntelligenceAgent()
    digest = agent.run_analysis()
    return digest

def generate_report():
    """Generate HTML report"""
    print("\n📊 Generating HTML report...")
    import subprocess
    result = subprocess.run([sys.executable, 'generate_report.py'], capture_output=True)
    return result.returncode == 0

def send_notifications(digest_file='intelligence_data/digest_latest.json'):
    """Send email and Slack notifications"""
    notifications_sent = []
    
    # Email notification
    if all([
        os.getenv('SENDER_EMAIL'),
        os.getenv('SENDER_PASSWORD'),
        os.getenv('RECEIVER_EMAIL')
    ]):
        try:
            from email_notifier import EmailNotifier
            print("\n📧 Sending email notification...")
            
            notifier = EmailNotifier(
                sender_email=os.getenv('SENDER_EMAIL'),
                sender_password=os.getenv('SENDER_PASSWORD'),
                receiver_email=os.getenv('RECEIVER_EMAIL')
            )
            
            import glob
            digest_files = glob.glob('intelligence_data/digest_*.json')
            if digest_files:
                latest_digest = max(digest_files, key=os.path.getctime)
                html_report = 'competitive_intelligence_report.html'
                
                if notifier.send_report(latest_digest, html_report):
                    notifications_sent.append('email')
        except Exception as e:
            print(f"❌ Email notification failed: {e}")
    
    # Slack notification
    if os.getenv('SLACK_WEBHOOK_URL'):
        try:
            from slack_notifier import SlackNotifier
            print("\n💬 Sending Slack notification...")
            
            notifier = SlackNotifier(webhook_url=os.getenv('SLACK_WEBHOOK_URL'))
            
            import glob
            digest_files = glob.glob('intelligence_data/digest_*.json')
            if digest_files:
                latest_digest = max(digest_files, key=os.path.getctime)
                
                if notifier.send_summary(latest_digest):
                    notifications_sent.append('slack')
        except Exception as e:
            print(f"❌ Slack notification failed: {e}")
    
    return notifications_sent

def main():
    """Main execution flow"""
    start_time = datetime.now()
    
    print("=" * 70)
    print("🚀 COMPETITIVE INTELLIGENCE AGENT - AUTOMATED RUN")
    print("=" * 70)
    print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Step 1: Run agent
        digest = run_agent()
        
        # Step 2: Generate report
        report_success = generate_report()
        
        # Step 3: Send notifications
        if os.path.exists('.env'):
            notifications = send_notifications()
            if notifications:
                print(f"\n✅ Notifications sent via: {', '.join(notifications)}")
            else:
                print("\n⚠️  No notifications configured. Add credentials to .env file.")
        else:
            print("\n⚠️  No .env file found. Skipping notifications.")
            print("     Copy .env.template to .env and add your credentials.")
        
        # Summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "=" * 70)
        print("✅ RUN COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print(f"Duration: {duration:.2f} seconds")
        print(f"Changes detected: {digest['summary']['total_changes_detected']}")
        print(f"News mentions: {digest['summary']['news_mentions']}")
        print(f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())