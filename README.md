# 🤖 Competitive Intelligence Agent

> Automated competitor monitoring with AI-powered insights for Product Managers

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An intelligent agent that monitors competitors, detects changes, and generates actionable insights—cutting research time from days to hours.

![Competitive Intelligence Agent Demo](https://via.placeholder.com/800x400/667eea/ffffff?text=Add+Your+Screenshot+Here)

## ✨ Features

- 🔍 **Automated Monitoring** - Tracks 3-5 competitor websites for product/pricing changes
- 📊 **Change Detection** - Uses content hashing to identify updates across pages
- 📰 **News Aggregation** - Framework for tracking competitor mentions in tech news
- 💬 **Sentiment Analysis** - Ready for Reddit/Twitter API integration
- 📈 **Weekly Digests** - Generates comprehensive reports with actionable insights
- 🔔 **Notifications** - Email and Slack integration for instant alerts
- 🤖 **GitHub Actions** - Fully automated cloud execution (no server needed!)

## 🎯 Why This Matters

This project demonstrates **AI-augmented Product Management**—showing how PMs can leverage automation to:
- Free up time for strategic thinking
- Make data-driven competitive decisions
- Stay ahead of market trends
- Build technical PM skills (Python, APIs, automation)

**The agent doesn't replace PM judgment—it amplifies it.**

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR-USERNAME/competitive-intel-agent.git
   cd competitive-intel-agent
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure competitors**
   
   Edit `config.json` to add your competitors:
   ```json
   {
     "competitors": [
       {
         "name": "Competitor Name",
         "website": "https://competitor.com",
         "product_page": "https://competitor.com/products",
         "pricing_page": "https://competitor.com/pricing"
       }
     ]
   }
   ```

4. **Run the agent**
   ```bash
   python competitive_intelligence_agent.py
   ```

5. **View the report**
   ```bash
   python generate_report.py
   # Opens competitive_intelligence_report.html
   ```

That's it! Your first intelligence report is ready.

## 🔄 Automation Options

### Option 1: GitHub Actions (Recommended)

**Runs in the cloud, completely free, no local setup needed!**

1. Fork/clone this repository to your GitHub account
2. GitHub Actions is already configured (`.github/workflows/daily-monitor.yml`)
3. It will automatically run daily at 9 AM UTC
4. View results in the "Actions" tab of your repository
5. Download reports from the artifacts section

**That's it!** Set and forget. ✨

### Option 2: Python Scheduler (Local)

Run on your machine while it's on:

```bash
pip install schedule
python scheduler.py
```

### Option 3: Cron (Linux/Mac) or Task Scheduler (Windows)

See [AUTOMATION_SETUP.md](AUTOMATION_SETUP.md) for detailed instructions.

## 📧 Notifications Setup (Optional)

### Email Notifications

1. Copy the environment template:
   ```bash
   cp .env.template .env
   ```

2. Edit `.env` with your Gmail credentials:
   ```
   SENDER_EMAIL=your-email@gmail.com
   SENDER_PASSWORD=your-app-password
   RECEIVER_EMAIL=recipient@example.com
   ```

3. Run with notifications:
   ```bash
   python run_with_notifications.py
   ```

**Gmail Setup:** [Get App Password](https://myaccount.google.com/apppasswords) (requires 2FA)

### Slack Notifications

1. Create a Slack webhook at [api.slack.com/apps](https://api.slack.com/apps)
2. Add to `.env`:
   ```
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
   ```
3. Test: `python slack_notifier.py`

## 📁 Project Structure

```
competitive-intel-agent/
├── competitive_intelligence_agent.py  # Main agent
├── generate_report.py                 # HTML report generator
├── config.json                        # Competitor configuration
├── requirements.txt                   # Python dependencies
│
├── .github/workflows/
│   └── daily-monitor.yml             # GitHub Actions automation
│
├── email_notifier.py                 # Email notifications
├── slack_notifier.py                 # Slack notifications
├── scheduler.py                      # Python scheduler
├── run_with_notifications.py         # Integrated runner
│
├── intelligence_data/                # Generated reports (gitignored)
│   └── digest_*.json
│
└── docs/
    ├── QUICKSTART.md                # 5-minute setup
    ├── AUTOMATION_SETUP.md          # Detailed automation guide
    └── DEPLOYMENT_CHECKLIST.md      # Step-by-step checklist
```

## 🛠️ Extending the Agent

### Add Real Reddit Analysis

1. Get Reddit API credentials from [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
2. Add to `.env`
3. Update `analyze_reddit_sentiment()` in the main agent

### Add News API Integration

1. Sign up at [newsapi.org](https://newsapi.org)
2. Integrate with `search_news_mentions()`

### Add More Competitors

Just edit `config.json` - no code changes needed!

## 📊 Example Output

The agent generates two outputs:

1. **JSON Digest** - Structured data with all findings
2. **HTML Report** - Beautiful, interactive report with insights

### Sample Insights:
- ✅ Competitor A updated pricing page (detected via content hash)
- ✅ Competitor B mentioned in 3 news articles this week
- ✅ Reddit sentiment trending negative for Competitor C
- ⚡ Action: Review our pricing strategy against new competitor plans

## 🎓 Use Cases for PMs

- **Competitive Positioning** - Track feature launches and pricing changes in real-time
- **Market Intelligence** - Identify trends before they become mainstream
- **Product Strategy** - Understand competitor roadmaps through their updates
- **Stakeholder Updates** - Automated weekly competitive reports for leadership
- **Feature Prioritization** - Data-driven decisions on what to build next

## 🤝 Contributing

This is a demonstration project, but suggestions are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

MIT License - feel free to use and modify for your own projects!

## 🙋‍♂️ About

**Built by:** [Your Name]  
**Connect:** [Your LinkedIn URL]  
**Purpose:** Demonstrating how Product Managers can leverage AI and automation to amplify their strategic work

---

### 💡 The Philosophy

In the age of AI, Product Managers won't be replaced—but PMs who don't learn to leverage AI tools will be.

This project shows that AI augmentation is about:
- **Automation** of repetitive research tasks
- **Amplification** of human strategic thinking
- **Acceleration** of decision-making cycles

The agent handles data collection. You handle the insights, strategy, and decisions.

---

**⭐ If you found this useful, please star the repo!**

**Questions?** Open an issue or reach out on [LinkedIn](YOUR_LINKEDIN_URL)

---

<sub>Made with ❤️ by a PM who believes in building, not just talking about AI.</sub>