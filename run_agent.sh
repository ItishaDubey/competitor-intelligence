#!/bin/bash

# Competitive Intelligence Agent - Cron Runner Script
# This script runs the agent and handles logging/notifications

# Configuration
PROJECT_DIR="/path/to/your/competitive-intel-agent"  # UPDATE THIS PATH
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/agent_$(date +'%Y%m%d').log"
EMAIL_TO="your-email@example.com"  # UPDATE THIS EMAIL

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Change to project directory
cd "$PROJECT_DIR" || exit 1

log "=========================================="
log "Starting Competitive Intelligence Agent"
log "=========================================="

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    log "Activating virtual environment..."
    source venv/bin/activate
fi

# Run the agent
log "Running agent..."
if python3 competitive_intelligence_agent.py >> "$LOG_FILE" 2>&1; then
    log "✅ Agent executed successfully"
else
    log "❌ Agent failed with error code $?"
    exit 1
fi

# Generate report
log "Generating HTML report..."
if python3 generate_report.py >> "$LOG_FILE" 2>&1; then
    log "✅ Report generated successfully"
else
    log "❌ Report generation failed with error code $?"
    exit 1
fi

# Optional: Send email notification
# Uncomment and configure if you want email notifications
# if command -v mail &> /dev/null; then
#     log "Sending email notification..."
#     echo "Daily Competitive Intelligence Report is ready. Check $PROJECT_DIR for the latest report." | \
#         mail -s "Competitive Intelligence Report - $(date +'%Y-%m-%d')" "$EMAIL_TO"
#     log "✅ Email sent to $EMAIL_TO"
# fi

# Optional: Clean up old logs (keep last 30 days)
find "$LOG_DIR" -name "agent_*.log" -type f -mtime +30 -delete
log "✅ Cleaned up old logs"

log "=========================================="
log "Agent run completed"
log "=========================================="

# Exit successfully
exit 0