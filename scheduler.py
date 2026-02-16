"""
Python Scheduler for Competitive Intelligence Agent
Cross-platform scheduler that runs the agent at specified times
"""

import schedule
import time
import subprocess
from datetime import datetime
import sys
import os

class AgentScheduler:
    def __init__(self):
        self.log_file = "scheduler.log"
        
    def log(self, message):
        """Log message to console and file"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        with open(self.log_file, 'a') as f:
            f.write(log_message + '\n')
    
    def run_agent(self):
        """Run the competitive intelligence agent"""
        self.log("=" * 60)
        self.log("Starting Competitive Intelligence Agent")
        self.log("=" * 60)
        
        try:
            # Run agent
            self.log("Running agent...")
            result = subprocess.run(
                [sys.executable, 'competitive_intelligence_agent.py'],
                capture_output=True,
                text=True,
                check=True
            )
            self.log("✅ Agent executed successfully")
            
            # Generate report
            self.log("Generating HTML report...")
            result = subprocess.run(
                [sys.executable, 'generate_report.py'],
                capture_output=True,
                text=True,
                check=True
            )
            self.log("✅ Report generated successfully")
            
            self.log("=" * 60)
            self.log("Agent run completed successfully")
            self.log("=" * 60)
            
            return True
            
        except subprocess.CalledProcessError as e:
            self.log(f"❌ Error running agent: {e}")
            self.log(f"Output: {e.output}")
            self.log(f"Error: {e.stderr}")
            return False
        except Exception as e:
            self.log(f"❌ Unexpected error: {e}")
            return False
    
    def send_notification(self, success):
        """Send notification about agent run (optional)"""
        # Implement email/Slack notification here if needed
        pass

def main():
    scheduler = AgentScheduler()
    
    # Configure your schedule here
    # Examples:
    
    # Daily at 9 AM
    schedule.every().day.at("09:00").do(scheduler.run_agent)
    
    # Weekly on Monday at 9 AM
    # schedule.every().monday.at("09:00").do(scheduler.run_agent)
    
    # Every 6 hours
    # schedule.every(6).hours.do(scheduler.run_agent)
    
    # Every hour
    # schedule.every().hour.do(scheduler.run_agent)
    
    # Multiple times per day
    # schedule.every().day.at("09:00").do(scheduler.run_agent)
    # schedule.every().day.at("18:00").do(scheduler.run_agent)
    
    scheduler.log("🤖 Competitive Intelligence Agent Scheduler Started")
    scheduler.log(f"Next run scheduled for: {schedule.next_run()}")
    scheduler.log("Press Ctrl+C to stop")
    scheduler.log("")
    
    # Optional: Run once at startup
    # scheduler.log("Running initial check...")
    # scheduler.run_agent()
    
    # Keep the script running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        scheduler.log("\n⚠️  Scheduler stopped by user")
        sys.exit(0)

if __name__ == "__main__":
    main()