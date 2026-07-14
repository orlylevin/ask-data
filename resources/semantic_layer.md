# Semantic Layer — CRM Sales Opportunities

This file defines how the DuckDB tables map to business entities, dimensions, relationships, and approved analytical behavior.

## Source

Active query source:

```text
ask_data.duckdb
```

Original dataset:

```text
Kaggle CRM Sales Opportunities
```

The DuckDB database is the technical source of truth during normal Ask Data execution. Do not inspect the original CSV files unless explicitly requested.

Metric formulas are defined in:

```text
resources/metrics.yaml
```

Business synonyms and ambiguity rules are defined in:

```text
resources/business_glossary.yaml
```

---

# Synonyms and Terminology

## Entities and Fields

| Canonical term | Synonyms |
|---|---|
| opportunity | deal |
| account | customer, company, client, prospect before Won |
| sales_agent | rep, sales rep, salesperson, AE, account executive |
| manager | sales manager |
| regional_office | region |
| close_value | deal value, deal size, sale amount |
| products.sales_price | list price, MSRP, asking price |
| engage_date | engagement date, start date |
| close_date | close date, resolution date |
| sector | industry |

## Deal Stage Terminology

| Canonical value or group | Synonyms |
|---|---|
| Won | Closed Won, win, won deal |
| Lost | Closed Lost, loss, lost deal |
| Prospecting | new lead, top of funnel, not yet engaged |
| Engaging | in progress, active, working |
| Won or Lost | closed, closed deal |
| Prospecting or Engaging | open, open deal, pipeline |

Open means:

```sql
deal_stage IN ('Prospecting', 'Engaging')
```

Closed means:

```sql
deal_stage IN ('Won', 'Lost')
```

---

# Ambiguous Terms

## Revenue

Possible meanings:

1. Won sales revenue  
   Source: `sales_pipeline.close_value`  
   Filter: `deal_stage = 'Won'`

2. Customer annual revenue  
   Source: `accounts.revenue`

Clarify when the user says only `revenue`.

## Pipeline

Possible meanings:

1. The entire `sales_pipeline` fact table
2. Open opportunities only

Clarify when the intended scope is not clear.

## Deal Size

Default meaning:

```text
sales_pipeline.close_value
```

Possible alternatives:

- customer annual revenue
- employee count
- product list price

Clarify only when context does not resolve the meaning.

---

# Entities

## `accounts`

Type: dimension  
Primary key: `account`  
Grain: one row per account

| Field | Description |
|---|---|
| `account` | Company name |
| `sector` | Industry |
| `year_established` | Year founded |
| `revenue` | Annual customer revenue in millions |
| `employees` | Headcount |
| `office_location` | Headquarters country |
| `subsidiary_of` | Parent company; null when independent |

### Parent Relationship

```sql
accounts.subsidiary_of = parent_accounts.account
```

Use only when parent-company or subsidiary rollups are requested.

---

## `products`

Type: dimension  
Primary key: `product`  
Grain: one row per product

| Field | Description |
|---|---|
| `product` | Product name |
| `series` | Product line or family |
| `sales_price` | List price |

---

## `sales_teams`

Type: dimension  
Primary key: `sales_agent`  
Grain: one row per sales agent

| Field | Description |
|---|---|
| `sales_agent` | Sales representative |
| `manager` | Sales manager |
| `regional_office` | Central, East, or West region |

---

## `sales_pipeline`

Type: fact  
Primary key: `opportunity_id`  
Grain: one row per opportunity

| Field | Description |
|---|---|
| `opportunity_id` | Unique deal identifier |
| `sales_agent` | Foreign key to `sales_teams.sales_agent` |
| `product` | Foreign key to `products.product` after canonical mapping |
| `account` | Foreign key to `accounts.account` |
| `deal_stage` | Prospecting, Engaging, Won, or Lost |
| `engage_date` | Date the deal entered Engaging |
| `close_date` | Date the deal was Won or Lost |
| `close_value` | Actual won value, zero for Lost, null while open |

### Field Behavior

- `engage_date` is expected to be null for Prospecting opportunities.
- `close_date` is expected to be null for open opportunities.
- `close_value` is expected to be null for open opportunities.
- `close_value` is normally zero for Lost opportunities.
- `close_value` contains the actual sales value for Won opportunities.

---

# Relationships

## Pipeline to Sales Team

```sql
sales_pipeline.sales_agent = sales_teams.sales_agent
```

Cardinality: many-to-one  
Default join: `LEFT JOIN`

## Pipeline to Product

Apply canonical product mapping first:

```sql
CASE
    WHEN sales_pipeline.product = 'GTXPro' THEN 'GTX Pro'
    ELSE sales_pipeline.product
END
```

Then join:

```sql
canonical_product = products.product
```

Cardinality: many-to-one  
Default join: `LEFT JOIN`

## Pipeline to Account

```sql
sales_pipeline.account = accounts.account
```

Cardinality: many-to-one  
Default join: `LEFT JOIN`

## Sales Hierarchy

```text
Regional Office
    -> Manager
        -> Sales Agent
```

## Account Hierarchy

```text
Parent Company
    -> Account
```

## Product Hierarchy

```text
Series
    -> Product
```

---

# Dimensions

| Dimension | Source | Notes |
|---|---|---|
| Deal status | `sales_pipeline.deal_stage` | Open = Prospecting or Engaging; Closed = Won or Lost |
| Engagement time | `sales_pipeline.engage_date` | Month, quarter, or year of engagement |
| Close time | `sales_pipeline.close_date` | Month, quarter, or year of resolution |
| Sales cycle length | `close_date - engage_date` | Closed deals only |
| Sales agent | `sales_pipeline.sales_agent` | Direct fact dimension |
| Manager | `sales_teams.manager` | Requires sales-team join |
| Region | `sales_teams.regional_office` | Requires sales-team join |
| Account | `sales_pipeline.account` | Null values may exist |
| Sector | `accounts.sector` | Requires account join |
| Location | `accounts.office_location` | Requires account join |
| Company size | `accounts.revenue` or `accounts.employees` | Define bands in an approved rule before use |
| Product | Canonicalized `sales_pipeline.product` | Normalize before grouping |
| Series | `products.series` | Requires product join |

---

# Derived Dimensions

## Sales Cycle Length

Definition:

```sql
close_date - engage_date
```

Required conditions:

```sql
deal_stage IN ('Won', 'Lost')
AND engage_date IS NOT NULL
AND close_date IS NOT NULL
```

Grain before aggregation:

```text
one row per closed opportunity
```

---

# Canonical Values

## Product

```text
GTXPro -> GTX Pro
```

Apply before grouping, filtering, comparing, or joining.

## Deal Stage

Canonical values:

```text
Prospecting
Engaging
Won
Lost
```

Normalize case when needed.

---

# Data Coverage

Known source coverage:

```text
engage_date begins: 2016-10-20
close_date ends: 2017-12-31
```

Do not assume that the latest year is complete merely because it contains the maximum date. Validate monthly coverage in DuckDB before selecting a latest completed period.

---

# Data-Quality and Analytical Caveats

## Lost Revenue Limitation

`close_value` is zero for Lost deals.

Therefore, it must not be used to represent actual lost revenue potential.

When a lost-value estimate is requested:

- use `products.sales_price` only if the approved metric allows it
- label the result as estimated lost opportunity value

## Open Pipeline Limitation

Open opportunities have null `close_value`.

Therefore, open pipeline value cannot be calculated by summing `close_value`.

Use `products.sales_price` only through the approved estimated open pipeline metric.

## Missing Engagement Dates

`engage_date` is null for Prospecting opportunities.

This is expected behavior, not automatically a data-quality error.

## Sales Agent Coverage

`sales_teams` may contain sales agents with no opportunities in `sales_pipeline`.

When the analysis must include agents with zero opportunities:

- start from `sales_teams`
- left join `sales_pipeline`

When only agents with recorded opportunities are required:

- start from `sales_pipeline`

## Missing Accounts

Some opportunities may have a null account.

Default behavior:

- keep them in company-wide totals
- label them `Unknown Account` when grouped by account
- exclude only when explicitly requested

## Join Cardinality

Before joining dimensions, validate uniqueness of:

- `accounts.account`
- `products.product`
- `sales_teams.sales_agent`

Dimension joins must not multiply fact rows.

## Distinct Counts

Use:

```sql
COUNT(DISTINCT opportunity_id)
```

for opportunity counts after joins.

---

# Recommended Semantic View

```sql
CREATE OR REPLACE VIEW semantic_sales_pipeline AS
SELECT
    sp.opportunity_id,
    sp.sales_agent,
    CASE
        WHEN sp.product = 'GTXPro' THEN 'GTX Pro'
        ELSE sp.product
    END AS product,
    sp.account,
    sp.deal_stage,
    CAST(sp.engage_date AS DATE) AS engage_date,
    CAST(sp.close_date AS DATE) AS close_date,
    sp.close_value,
    a.sector,
    a.year_established,
    a.revenue AS account_annual_revenue,
    a.employees,
    a.office_location,
    a.subsidiary_of,
    p.series,
    p.sales_price,
    st.manager,
    st.regional_office
FROM sales_pipeline AS sp
LEFT JOIN accounts AS a
    ON sp.account = a.account
LEFT JOIN products AS p
    ON CASE
           WHEN sp.product = 'GTXPro' THEN 'GTX Pro'
           ELSE sp.product
       END = p.product
LEFT JOIN sales_teams AS st
    ON sp.sales_agent = st.sales_agent;
```

Prefer this view when it contains all fields needed by the question.

---

# Query Rules

1. Use `resources/metrics.yaml` for metric formulas.
2. Use this file for tables, relationships, dimensions, date fields, hierarchies, and canonical mappings.
3. Use DuckDB as the technical source of truth.
4. Do not inspect source CSVs during normal execution.
5. Inspect only tables relevant to the current question.
6. Do not invent joins or business rules.
7. Use explicit columns rather than unrestricted `SELECT *`.
8. Preserve the requested grain.
9. Apply canonical mappings before grouping or joining.
10. Use `LEFT JOIN` for approved fact-to-dimension relationships unless a stricter scope is explicitly requested.
11. Validate date coverage before choosing relative periods.
12. Use distinct opportunity counts after joins.
13. Label proxy-based values as estimates.
