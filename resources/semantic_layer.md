# Semantic Layer — CRM Sales Opportunities

Source: `Database/*.csv` (accounts, products, sales_teams, sales_pipeline), based on the
[Kaggle CRM Sales Opportunities dataset](https://www.kaggle.com/datasets/innocentmfa/crm-sales-opportunities/data).

This document defines how the raw tables map to business entities, dimensions, and
metrics, so that business questions can be answered consistently.

## Synonyms / Terminology

Business questions may use any of these terms interchangeably with the canonical name.

### Entities & fields
| Canonical | Synonyms |
|---|---|
| opportunity | deal |
| account | customer, company, client, prospect (before Won) |
| sales_agent | rep, sales rep, salesperson, AE, account executive |
| manager | sales manager |
| regional_office | region |
| close_value | deal value, deal size, sale amount |
| products.sales_price | list price, MSRP, asking price |
| engage_date | engagement date, start date |
| close_date | close date, resolution date |
| sector | industry |

### Deal stage values
| Canonical `deal_stage` | Synonyms |
|---|---|
| Won | Closed Won, win, won deal |
| Lost | Closed Lost, loss, lost deal |
| Prospecting | new lead, top of funnel, not yet engaged |
| Engaging | in progress, active, working, open deal (also covers Prospecting) |
| Won or Lost | closed, closed deal |
| Prospecting or Engaging | open, open deal, pipeline (as in "in the pipeline") |

### Ambiguous terms — clarify before using
- **"Revenue"** is ambiguous between `accounts.revenue` (the customer's own annual
  revenue, $M) and `sales_pipeline.close_value` (revenue /the business earned from
  the deal). Confirm which one is meant.
- **"Pipeline"** can mean the whole `sales_pipeline` fact table, or specifically the
  open deals within it (Prospecting/Engaging). Confirm scope.
- **"Deal size"** usually means `close_value`, but could be confused with account size
  (`accounts.revenue` or `employees`). Confirm which one is meant.

## Entities

### accounts (dimension) — PK: `account`
| Field | Description |
|---|---|
| account | Company name |
| sector | Industry |
| year_established | Year founded |
| revenue | Annual revenue, $M |
| employees | Headcount |
| office_location | HQ country |
| subsidiary_of | Parent company (self-reference to `account`), blank if independent |

### products (dimension) — PK: `product`
| Field | Description |
|---|---|
| product | Product name |
| series | Product line (GTX, GTK, MG) |
| sales_price | List price |

### sales_teams (dimension) — PK: `sales_agent`
| Field | Description |
|---|---|
| sales_agent | Rep name |
| manager | Rep's manager |
| regional_office | Central / East / West |

### sales_pipeline (fact) — PK: `opportunity_id`
| Field | Description |
|---|---|
| opportunity_id | Unique deal ID |
| sales_agent | FK → sales_teams.sales_agent |
| product | FK → products.product |
| account | FK → accounts.account |
| deal_stage | Prospecting → Engaging → Won / Lost |
| engage_date | Date deal entered "Engaging" (null while Prospecting) |
| close_date | Date deal was Won or Lost (null while open) |
| close_value | Revenue from deal (0 for Lost, actual $ for Won, null while open) |

## Relationships
- `sales_pipeline.sales_agent` → `sales_teams.sales_agent` (many-to-one)
- `sales_pipeline.product` → `products.product` (many-to-one)
- `sales_pipeline.account` → `accounts.account` (many-to-one)
- `sales_teams.manager` groups agents into teams (hierarchy, not a separate table)
- `accounts.subsidiary_of` → `accounts.account` (self-referencing parent company)

## Dimensions

| Dimension | Source | Notes |
|---|---|---|
| Deal status | `deal_stage` | **Open** = Prospecting or Engaging; **Closed** = Won or Lost |
| Time (engaged) | `engage_date` | Month/quarter/year of engagement start |
| Time (closed) | `close_date` | Month/quarter/year of deal resolution |
| Sales cycle length | `close_date - engage_date` | Closed deals only |
| Sales agent / Manager / Region | `sales_teams` | Org hierarchy for pipeline attribution |
| Sector / Location / Company size | `accounts` | Segment by industry, geography, revenue/employee bands |
| Product / Series | `products` | Product-level or series-level rollups |

## Metrics

| Metric | Definition |
|---|---|
| # Opportunities | `COUNT(opportunity_id)` — overall or filtered by stage/dimension |
| Win rate | `COUNT(Won) / COUNT(Won or Lost)` — closed deals only |
| Won revenue | `SUM(close_value)` where `deal_stage = 'Won'` |
| Average deal size | `AVG(close_value)` where `deal_stage = 'Won'` |
| Average sales cycle | `AVG(close_date - engage_date)` where `deal_stage IN ('Won','Lost')` |
| Discount rate | `1 - (close_value / products.sales_price)` for Won deals |
| # Open opportunities | `COUNT(opportunity_id)` where `deal_stage IN ('Prospecting','Engaging')` |
| Revenue by segment | `SUM(close_value)` where Won, grouped by sector / region / product / series |
| Deals per agent / manager / region | `COUNT(opportunity_id)` grouped by sales org dimension |

## Caveats & data quality notes
- **Lost ≠ lost revenue potential**: `close_value` is always `0` for Lost deals, so it
  cannot be used to estimate the $ value of lost business. Use `products.sales_price`
  as a proxy if a lost-value estimate is needed.
- **No $ value for open pipeline**: Prospecting/Engaging deals have a null
  `close_value`, so "open pipeline value" cannot be summed directly from this field —
  it would need to be estimated from `products.sales_price` per open opportunity.
- **`engage_date` is null for Prospecting-stage deals** (500 rows) — expected, since
  the deal hasn't reached "Engaging" yet, not a data gap.
- **Sales agent roster mismatch**: `sales_teams` has 35 agents, but only 30 appear in
  `sales_pipeline` — 5 agents have no recorded opportunities in this dataset.
- Data covers `engage_date` 2016-10-20 through `close_date` 2017-12-31.

