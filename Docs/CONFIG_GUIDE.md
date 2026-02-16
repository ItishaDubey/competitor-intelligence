# 🎯 Flexible Config Guide

## Why This is Better

**OLD WAY (Rigid):**
```json
{
  "product_page": "...",  // What if you don't have one?
  "pricing_page": "..."   // What if pricing is on homepage?
}
```
❌ Required specific pages
❌ Didn't work for all websites
❌ Forced structure

**NEW WAY (Flexible):**
```json
{
  "pages_to_monitor": [
    { "name": "Any Page", "url": "...", "track": [...] }
  ]
}
```
✅ Monitor ANY pages
✅ Works for ANY website
✅ Your choice what to track

---

## Quick Start Examples

### Example 1: No Website Yet (Just Track Competitors)

```json
{
  "baseline": null,
  "competitors": [
    {
      "name": "Competitor",
      "pages_to_monitor": [
        {
          "name": "Their Homepage",
          "url": "https://competitor.com",
          "track": ["content", "products", "pricing"]
        }
      ]
    }
  ]
}
```

### Example 2: You Have a Homepage (Like K-Store)

```json
{
  "baseline": {
    "name": "K-Store",
    "pages_to_monitor": [
      {
        "name": "Homepage",
        "url": "https://kstore.global",
        "track": ["content", "products"]
      }
    ]
  },
  "competitors": [...]
}
```

### Example 3: Multiple Pages Per Company

```json
{
  "baseline": {...},
  "competitors": [
    {
      "name": "Amazon",
      "pages_to_monitor": [
        {
          "name": "Gift Cards",
          "url": "https://amazon.com/giftcards",
          "track": ["products", "pricing"]
        },
        {
          "name": "Digital Games",
          "url": "https://amazon.com/digital-games",
          "track": ["products", "pricing"]
        }
      ]
    }
  ]
}
```

---

## Configuration Options

### Page Object Structure

```json
{
  "name": "Descriptive Name",
  "url": "https://exact-url-to-monitor.com/page",
  "track": ["what", "to", "track"]
}
```

**Fields:**
- **name** (required) - Any name you want (e.g., "Homepage", "Products", "Pricing")
- **url** (required) - Exact URL to monitor
- **track** (required) - Array of what to extract

### Track Options

```json
"track": [
  "content",   // Track any content changes
  "products",  // Extract product listings
  "pricing"    // Extract prices
]
```

**Mix and match as needed!**

Examples:
- `["content"]` - Just track if page changes
- `["products"]` - Only extract products
- `["pricing"]` - Only extract prices  
- `["content", "products", "pricing"]` - Track everything

---

## Real-World Scenarios

### Scenario 1: SaaS Company (No Pricing Page)

```json
{
  "baseline": {
    "name": "Your SaaS",
    "pages_to_monitor": [
      {
        "name": "Features Page",
        "url": "https://yoursaas.com/features",
        "track": ["content", "products"]
      }
    ]
  },
  "competitors": [
    {
      "name": "Competitor SaaS",
      "pages_to_monitor": [
        {
          "name": "Features",
          "url": "https://competitor.com/features",
          "track": ["content"]
        },
        {
          "name": "Pricing (if they have one)",
          "url": "https://competitor.com/pricing",
          "track": ["pricing", "content"]
        }
      ]
    }
  ]
}
```

### Scenario 2: E-commerce (Multiple Product Categories)

```json
{
  "competitors": [
    {
      "name": "Amazon",
      "pages_to_monitor": [
        {
          "name": "Gaming Vouchers",
          "url": "https://amazon.com/gaming-gift-cards",
          "track": ["products", "pricing"]
        },
        {
          "name": "PlayStation Cards",
          "url": "https://amazon.com/playstation-cards",
          "track": ["products", "pricing"]
        }
      ]
    }
  ]
}
```

### Scenario 3: Content/Blog Monitoring

```json
{
  "competitors": [
    {
      "name": "Industry Leader",
      "pages_to_monitor": [
        {
          "name": "Blog",
          "url": "https://competitor.com/blog",
          "track": ["content"]
        },
        {
          "name": "News",
          "url": "https://competitor.com/news",
          "track": ["content"]
        }
      ]
    }
  ]
}
```

---

## What Gets Tracked?

### "content"
- Page text changes
- Layout modifications
- New sections added

### "products"
- Product listings
- Product titles
- Product categories
- Product count changes

### "pricing"
- All prices on the page
- Price ranges (min, max, avg)
- Currency detection (USD, EUR, INR, etc.)
- Price changes over time

---

## Tips

### ✅ DO:
- Use descriptive page names
- Start with homepage if unsure
- Track what matters to you
- Use different pages per competitor
- Remove baseline if you don't have a site

### ❌ DON'T:
- Monitor too many pages (start with 1-2 per competitor)
- Use relative URLs (always full https://)
- Track everything if you only need pricing
- Forget to update URLs if they change

---

## Common Patterns

### Pattern 1: Homepage Only
```json
"pages_to_monitor": [
  {"name": "Homepage", "url": "...", "track": ["content", "products"]}
]
```

### Pattern 2: Homepage + One Key Page
```json
"pages_to_monitor": [
  {"name": "Homepage", "url": "...", "track": ["content"]},
  {"name": "Shop", "url": "...", "track": ["products", "pricing"]}
]
```

### Pattern 3: Multiple Category Pages
```json
"pages_to_monitor": [
  {"name": "Gaming", "url": "...", "track": ["products", "pricing"]},
  {"name": "Streaming", "url": "...", "track": ["products", "pricing"]},
  {"name": "Software", "url": "...", "track": ["products", "pricing"]}
]
```

---

## Example Configs

Check the `config_examples/` folder for ready-to-use configs:

1. **1_no_baseline.json** - No baseline, just competitors
2. **2_multiple_pages.json** - Multiple pages per competitor
3. **3_homepage_only.json** - Simple homepage monitoring

Copy any example to `config.json` and customize!

---

## Your Turn!

1. **Copy config.json**
2. **Edit the baseline section** (or set to `null`)
3. **Add your competitors**
4. **Specify pages to monitor**
5. **Choose what to track**
6. **Run:** `python competitive_intelligence_agent.py`

**That's it!** No rigid structure, no required pages, just flexibility. 🚀