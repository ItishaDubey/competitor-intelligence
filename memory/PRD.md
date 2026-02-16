# Competitive Intelligence Agent - PRD

## Project Overview
A full-stack competitive intelligence platform that helps Product Managers and Business Analysts monitor competitors, track website/pricing changes, and get AI-powered strategic insights.

## Original Problem Statement
Build a Competitive Intelligence Agent that:
- Monitors 5 competitor websites/product pages for changes
- Scrapes tech news sites for mentions of competitors
- Pulls sentiment from Reddit/Twitter about competitor products
- Aggregates everything into a weekly digest with insights
- Proper UI with Human-in-the-Loop configuration

## User Personas
1. **Product Manager** - Needs to track competitor features and pricing
2. **Business Analyst** - Requires competitive market intelligence
3. **Marketing Strategist** - Monitors competitor positioning and messaging

## Core Requirements (Static)
- [x] User authentication (email/password)
- [x] CRUD for competitor configuration
- [x] Website scraping and change detection
- [x] Product and pricing extraction
- [x] AI-powered insights generation (Claude Sonnet 4.5)
- [x] Dashboard with stats overview
- [x] Reports and digest history

## What's Been Implemented
### Feb 16, 2026 - MVP
- **Backend (FastAPI + MongoDB)**
  - JWT-based authentication (register/login)
  - Competitor management CRUD API
  - Intelligence scanning engine (from original repo code)
  - AI insights generation using Claude Sonnet 4.5 via Emergent LLM Key
  - Report generation and history
  - Dashboard statistics endpoint

- **Frontend (React + Tailwind CSS)**
  - Auth pages (login/register with toggle)
  - Dashboard with stats cards and AI insights display
  - Competitors management page (add/edit/delete)
  - Reports page with detailed view
  - Light minimal professional design (Indigo/Slate palette)
  - Responsive layout with mobile navigation

## Architecture
```
/app
├── backend/
│   ├── server.py          # FastAPI application
│   ├── requirements.txt   # Python dependencies
│   └── .env               # Environment variables
├── frontend/
│   ├── src/
│   │   ├── pages/         # Page components
│   │   ├── components/ui/ # UI components
│   │   ├── api/           # API client
│   │   └── context/       # Auth context
│   ├── package.json
│   └── .env
└── design_guidelines.json
```

## Prioritized Backlog

### P0 - Critical (Done)
- [x] User registration and login
- [x] Add/edit/delete competitors
- [x] Run intelligence scans
- [x] View reports

### P1 - High Priority (Pending)
- [ ] Scheduled automated daily scans (APScheduler integration)
- [ ] Email notifications for changes
- [ ] News API integration for competitor mentions
- [ ] Social media sentiment (Reddit/Twitter API)

### P2 - Medium Priority (Future)
- [ ] Stripe subscription plans
- [ ] Team collaboration features
- [ ] Export reports to PDF
- [ ] Custom tracking rules

### P3 - Nice to Have
- [ ] Webhook notifications
- [ ] Competitor comparison charts
- [ ] Historical trend analysis

## Next Tasks
1. Configure scheduled background jobs for daily scans
2. Add email notification service
3. Integrate news API for competitor mentions
4. Add social media sentiment analysis

## Technical Notes
- External URL may require preview wake-up time
- All APIs tested and working on localhost
- Emergent LLM Key configured for Claude Sonnet 4.5
