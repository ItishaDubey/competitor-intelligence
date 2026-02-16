# 🎯 Quick Automation Setup - Choose Your Path

## 📋 What You Have

Your Competitive Intelligence Agent is ready with **4 automation options** + **2 notification channels**:

```
Automation Options:
├── 🌐 GitHub Actions (Cloud, Recommended)
├── ⏰ Cron Jobs (Linux/Mac)
├── 📅 Task Scheduler (Windows)
└── 🐍 Python Scheduler (Cross-platform)

Notification Options:
├── 📧 Email (Gmail)
└── 💬 Slack
```

---

## 🚀 FASTEST PATH: Python Scheduler (5 minutes)

**Best for:** Testing, beginners, quick setup

### Step 1: Install
```bash
pip install schedule python-dotenv
```

### Step 2: Configure (Optional notifications)
```bash
cp .env.template .env
# Edit .env with your email/Slack credentials
```

### Step 3: Run
```bash
python scheduler.py
```

**Done!** Agent will run daily at 9 AM. Keep terminal open or run in background.

---

## 🌟 BEST FOR PRODUCTION: GitHub Actions (10 minutes)

**Best for:** Set-and-forget, cloud-based, free

### Step 1: Push to GitHub
```bash
git init
git add .
git commit -m "Add competitive intelligence agent"
git remote add origin https://github.com/yourusername/competitive-intel-agent.git
git push -u origin main
```

### Step 2: Enable GitHub Actions
- The workflow file is already included (`.github/workflows/daily-monitor.yml`)
- Go to your repo → Actions tab → Enable workflows
- **Done!** Runs automatically at 9 AM UTC daily

### Step 3: View Results
- Actions tab shows run history
- Download artifacts (reports) from each run
- Data automatically commits to your repo

### Add Email Notifications (Optional)
Add this step to `.github/workflows/daily-monitor.yml`:

```yaml
    - name: Send email notification
      uses: dawidd6/action-send-mail@v3
      with:
        server_address: smtp.gmail.com
        server_port: 465
        username: ${{secrets.MAIL_USERNAME}}
        password: ${{secrets.MAIL_PASSWORD}}
        subject: Daily Competitive Intelligence
        to: your-email@example.com
        from: GitHub Actions
        attachments: competitive_intelligence_report.html
```

Then add secrets in: Settings → Secrets → Actions

---

## 🖥️ LOCAL AUTOMATION

### For Linux/Mac Users: Cron

```bash
# Make script executable
chmod +x run_agent.sh

# Edit the script to set your project path
nano run_agent.sh  # Update PROJECT_DIR path

# Add to crontab
crontab -e

# Add this line (runs daily at 9 AM)
0 9 * * * /path/to/your/run_agent.sh
```

### For Windows Users: Task Scheduler

1. Edit `run_agent.bat` - update paths
2. Open Task Scheduler (Win + R → `taskschd.msc`)
3. Create Basic Task:
   - Name: "Competitive Intelligence"
   - Trigger: Daily at 9 AM
   - Action: Start program → Select `run_agent.bat`
4. Done!

---

## 📧 Email Notifications Setup

### Gmail App Password Method:

1. **Enable 2FA** on your Google account
2. **Generate App Password:**
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" → Generate
   - Copy the 16-character password
3. **Configure:**
   ```bash
   cp .env.template .env
   # Edit .env:
   SENDER_EMAIL=your-email@gmail.com
   SENDER_PASSWORD=your-app-password-here
   RECEIVER_EMAIL=recipient@example.com
   ```
4. **Test:**
   ```bash
   python email_notifier.py
   ```

---

## 💬 Slack Notifications Setup

1. **Create Slack App:**
   - Go to: https://api.slack.com/apps
   - Create New App → From scratch
   - Name it "Competitive Intel Bot"

2. **Add Incoming Webhook:**
   - Features → Incoming Webhooks → Activate
   - Add New Webhook to Workspace
   - Select your channel
   - Copy the webhook URL

3. **Configure:**
   ```bash
   # Add to .env:
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
   ```

4. **Test:**
   ```bash
   python slack_notifier.py
   ```

---

## 🔄 Running with Notifications

Use this command to run the agent with automatic notifications:

```bash
python run_with_notifications.py
```

This single command:
- ✅ Runs the competitive intelligence agent
- ✅ Generates the HTML report
- ✅ Sends email notification (if configured)
- ✅ Sends Slack notification (if configured)

---

## 📊 Recommended Setups

### **For Personal Use:**
- Python Scheduler + Email notifications
- Runs on your laptop, emails you daily

### **For Team Use:**
- GitHub Actions + Slack notifications
- Cloud-based, posts to team channel daily

### **For Enterprise:**
- Cron on dedicated server + Both email & Slack
- Reliable, scalable, professional

---

## 🐛 Troubleshooting

### Agent not running automatically?
```bash
# Check logs
tail -f logs/agent_*.log

# For cron
grep CRON /var/log/syslog

# For GitHub Actions
Check Actions tab in your repository
```

### Notifications not working?
```bash
# Test email
python email_notifier.py

# Test Slack
python slack_notifier.py

# Check .env file exists and has correct values
cat .env
```

### Python scheduler stops?
```bash
# Run in background (Linux/Mac)
nohup python scheduler.py > scheduler.log 2>&1 &

# Check if running
ps aux | grep scheduler.py
```

---

## 📈 Next Steps

1. **Start simple:** Use Python Scheduler to test
2. **Add notifications:** Configure email or Slack
3. **Go production:** Move to GitHub Actions or Cron
4. **Monitor:** Check logs and reports weekly
5. **Iterate:** Adjust schedule and add more competitors

---

## 💡 Pro Tips

- **Test manually first:** Run `python competitive_intelligence_agent.py` before automating
- **Start with weekly:** Use `0 9 * * 1` (every Monday) instead of daily
- **Monitor storage:** GitHub has artifact limits (2GB free)
- **Respect rate limits:** Don't run more than once per hour
- **Review insights:** Automation collects data, but YOU make decisions

---

**Questions?** Check AUTOMATION_SETUP.md for detailed instructions!