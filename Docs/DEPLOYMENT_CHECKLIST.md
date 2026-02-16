# 🎯 Deployment Checklist

Use this checklist to deploy your Competitive Intelligence Agent step by step.

## ✅ Phase 1: Basic Setup (15 minutes)

- [ ] **Install Python dependencies**
  ```bash
  pip install -r requirements.txt
  ```

- [ ] **Configure competitors**
  - [ ] Edit `config.json`
  - [ ] Add 3-5 competitor websites
  - [ ] Add product/pricing page URLs
  - [ ] Add relevant keywords

- [ ] **Test manual run**
  ```bash
  python competitive_intelligence_agent.py
  ```
  - [ ] Agent runs without errors
  - [ ] Creates `intelligence_data/` folder
  - [ ] Generates digest JSON file

- [ ] **Generate report**
  ```bash
  python generate_report.py
  ```
  - [ ] Creates HTML report
  - [ ] Report opens in browser
  - [ ] Shows sample data

---

## ✅ Phase 2: Automation Setup (20 minutes)

### Choose ONE automation method:

#### Option A: GitHub Actions (Recommended)
- [ ] Create GitHub repository
- [ ] Push code to GitHub
  ```bash
  git init
  git add .
  git commit -m "Initial commit"
  git remote add origin YOUR_REPO_URL
  git push -u origin main
  ```
- [ ] Enable GitHub Actions in repo settings
- [ ] Verify `.github/workflows/daily-monitor.yml` exists
- [ ] Check Actions tab - should see workflow scheduled
- [ ] Wait for first run or trigger manually

#### Option B: Python Scheduler
- [ ] Install schedule package
  ```bash
  pip install schedule
  ```
- [ ] Edit `scheduler.py` if needed (change schedule time)
- [ ] Run scheduler
  ```bash
  python scheduler.py
  ```
- [ ] Keep terminal open or run in background
  ```bash
  nohup python scheduler.py > scheduler.log 2>&1 &
  ```

#### Option C: Cron (Linux/Mac)
- [ ] Edit `run_agent.sh`
- [ ] Update `PROJECT_DIR` path
- [ ] Make executable
  ```bash
  chmod +x run_agent.sh
  ```
- [ ] Add to crontab
  ```bash
  crontab -e
  # Add: 0 9 * * * /full/path/to/run_agent.sh
  ```
- [ ] Verify with `crontab -l`

#### Option D: Task Scheduler (Windows)
- [ ] Edit `run_agent.bat`
- [ ] Update paths
- [ ] Open Task Scheduler (taskschd.msc)
- [ ] Create Basic Task
- [ ] Set daily trigger at 9 AM
- [ ] Point to `run_agent.bat`
- [ ] Test run manually

---

## ✅ Phase 3: Notifications (Optional, 15 minutes)

### Email Notifications

- [ ] **Setup Gmail App Password**
  - [ ] Enable 2FA on Google account
  - [ ] Generate App Password at https://myaccount.google.com/apppasswords
  - [ ] Copy 16-character password

- [ ] **Configure email**
  - [ ] Copy `.env.template` to `.env`
    ```bash
    cp .env.template .env
    ```
  - [ ] Edit `.env` file
  - [ ] Add SENDER_EMAIL
  - [ ] Add SENDER_PASSWORD (app password)
  - [ ] Add RECEIVER_EMAIL

- [ ] **Test email**
  ```bash
  python email_notifier.py
  ```
  - [ ] Email received successfully
  - [ ] Attachments included
  - [ ] Summary looks correct

### Slack Notifications

- [ ] **Setup Slack App**
  - [ ] Go to https://api.slack.com/apps
  - [ ] Create New App → From scratch
  - [ ] Name: "Competitive Intel Bot"
  - [ ] Add Incoming Webhooks
  - [ ] Activate webhooks
  - [ ] Add webhook to your channel
  - [ ] Copy webhook URL

- [ ] **Configure Slack**
  - [ ] Edit `.env` file
  - [ ] Add SLACK_WEBHOOK_URL

- [ ] **Test Slack**
  ```bash
  python slack_notifier.py
  ```
  - [ ] Message posted to Slack
  - [ ] Summary displays correctly
  - [ ] Formatting looks good

---

## ✅ Phase 4: Verification (10 minutes)

- [ ] **Run full workflow**
  ```bash
  python run_with_notifications.py
  ```
  - [ ] Agent runs successfully
  - [ ] Report generated
  - [ ] Email sent (if configured)
  - [ ] Slack message sent (if configured)

- [ ] **Check automation**
  - [ ] Automation is scheduled
  - [ ] Logs are being created
  - [ ] No error messages in logs

- [ ] **Verify outputs**
  - [ ] `intelligence_data/` contains JSON files
  - [ ] `competitive_intelligence_report.html` exists
  - [ ] Historical data is being tracked

---

## ✅ Phase 5: GitHub & LinkedIn (20 minutes)

### GitHub Repository

- [ ] **Create README on GitHub**
  - [ ] Add project description
  - [ ] Add setup instructions
  - [ ] Add your demo screenshot
  - [ ] Add "Built by [Your Name]" section

- [ ] **Add to README**
  ```markdown
  # Competitive Intelligence Agent
  
  Automated monitoring of competitors with AI-powered insights.
  
  ## Features
  - Monitors competitor websites
  - Tracks changes and updates
  - Generates weekly reports
  - Email & Slack notifications
  
  ## Demo
  [Add screenshot of HTML report here]
  
  ## Setup
  See QUICKSTART.md for setup instructions.
  
  Built by [Your Name] | [LinkedIn Profile]
  ```

- [ ] **Make repository public**
- [ ] **Add topics/tags**: 
  - competitive-intelligence
  - product-management
  - automation
  - web-scraping
  - python

### LinkedIn Post

- [ ] **Choose post version** (from earlier)
  - [ ] Thought Leader version, or
  - [ ] Provocative Truth version

- [ ] **Customize post**
  - [ ] Add your GitHub repo link
  - [ ] Add personal story/context if desired
  - [ ] Add screenshot of report (optional)

- [ ] **Post timing**
  - [ ] Best times: Tue-Thu, 8-10 AM or 12-1 PM
  - [ ] Engage with comments for first 2 hours

- [ ] **After posting**
  - [ ] Pin the post to your profile
  - [ ] Share in relevant groups
  - [ ] Respond to all comments

---

## ✅ Phase 6: Maintenance (Ongoing)

### Weekly Tasks
- [ ] Review generated reports
- [ ] Check for errors in logs
- [ ] Update competitor list if needed
- [ ] Adjust monitoring frequency if needed

### Monthly Tasks
- [ ] Review historical trends
- [ ] Update config.json with new competitors
- [ ] Archive old digest files
- [ ] Check disk space usage

### As Needed
- [ ] Add new features (Reddit API, News API)
- [ ] Improve insight generation
- [ ] Add more notification channels
- [ ] Create dashboard for visualization

---

## 🎯 Success Criteria

You've successfully deployed when:

✅ Agent runs automatically without manual intervention
✅ Reports are generated and accessible
✅ Notifications are working (if configured)
✅ Historical data is accumulating
✅ GitHub repo is public and documented
✅ LinkedIn post is live with engagement

---

## 🆘 Common Issues

### "Module not found" error
```bash
pip install -r requirements.txt
```

### "Permission denied" on .sh file
```bash
chmod +x run_agent.sh
```

### Email not sending
- Check Gmail App Password (not regular password)
- Verify 2FA is enabled
- Check .env file exists and is formatted correctly

### Cron job not running
- Use absolute paths in crontab
- Check cron logs: `grep CRON /var/log/syslog`
- Verify script has execute permissions

### GitHub Actions failing
- Check Actions tab for error logs
- Verify workflow file is in `.github/workflows/`
- Check file permissions and paths

---

## 📞 Next Steps After Deployment

1. **Monitor for 1 week** - Make sure automation works consistently
2. **Share on LinkedIn** - Post about your project
3. **Engage with comments** - Build visibility
4. **Iterate** - Add features based on feedback
5. **Document learnings** - Write about your experience

---

**Remember:** This is a demonstration of AI-augmented PM work. The goal is to show you can build tools that amplify your strategic thinking, not replace it.

**Good luck! 🚀**