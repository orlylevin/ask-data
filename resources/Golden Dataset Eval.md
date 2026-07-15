# Golden Dataset — question-to-sql Agent Evals

Evaluates the `question-to-sql` subagent. Single-table questions first, then cross-table (JOIN) questions.
Source of truth: `resources/semantic_layer.md`, `resources/metrics.yaml`.

**Assumption on date columns:** `engage_date` and `close_date` are loaded from CSV via pandas and may be stored as text unless the loader casts them. If DuckDB throws a type error on date arithmetic/comparison below, wrap the column in `CAST(col AS DATE)` first — the business logic stays the same either way. Once confirmed, remove this note.

---

## 1. Accounts

| ID | Question | Expected SQL |
| :--- | :--- | :--- |
| A1 | How many accounts do we have? | `SELECT COUNT(DISTINCT account) FROM accounts;` |
| A2 | Which account has the highest annual revenue? | `SELECT account, revenue FROM accounts ORDER BY revenue DESC LIMIT 1;` |
| A3 | Which account has the lowest annual revenue? | `SELECT account, revenue FROM accounts ORDER BY revenue ASC LIMIT 1;` |
| A4 | Which account is the oldest (established earliest)? | `SELECT account, year_established FROM accounts ORDER BY year_established ASC LIMIT 1;` |
| A5 | How many accounts are in the Technology sector? | `SELECT COUNT(*) FROM accounts WHERE sector = 'Technology';` |
| A6 | How many accounts are located in the USA? | `SELECT COUNT(*) FROM accounts WHERE office_location = 'USA';` |
| A7 | What is the average number of employees across all accounts? | `SELECT AVG(employees) FROM accounts;` |
| A8 | Top 3 sectors by total customer annual revenue. | `SELECT sector, SUM(revenue) AS total_revenue FROM accounts GROUP BY sector ORDER BY total_revenue DESC LIMIT 3;` |
| A9 | Which accounts are subsidiaries of another company? | `SELECT account, subsidiary_of FROM accounts WHERE subsidiary_of IS NOT NULL AND subsidiary_of != '';` |
| A10 | Total customer annual revenue by office location. | `SELECT office_location, SUM(revenue) AS total_revenue FROM accounts GROUP BY office_location ORDER BY total_revenue DESC;` |
| A11 | How many accounts have no parent company (independent)? | `SELECT COUNT(*) FROM accounts WHERE subsidiary_of IS NULL OR subsidiary_of = '';` |

*Note: `accounts.revenue` = customer's own annual revenue. Never confuse with `won_revenue` (what we earned).*

---

## 2. Products

| ID | Question | Expected SQL |
| :--- | :--- | :--- |
| P1 | How many products do we have? | `SELECT COUNT(*) FROM products;` |
| P2 | What is the most expensive product? | `SELECT product, sales_price FROM products ORDER BY sales_price DESC LIMIT 1;` |
| P3 | Average sales price across all products. | `SELECT AVG(sales_price) FROM products;` |
| P4 | How many products are in the 'GTX' series? | `SELECT COUNT(*) FROM products WHERE series = 'GTX';` |
| P5 | Products in the 'MG' series, sorted by price ascending. | `SELECT product, sales_price FROM products WHERE series = 'MG' ORDER BY sales_price ASC;` |
| P6 | How many distinct product series do we have? | `SELECT COUNT(DISTINCT series) FROM products;` |
| P7 | Average sales price by series. | `SELECT series, AVG(sales_price) AS avg_price FROM products GROUP BY series ORDER BY avg_price DESC;` |

---

## 3. Sales Teams

| ID | Question | Expected SQL |
| :--- | :--- | :--- |
| T1 | How many sales agents do we have? | `SELECT COUNT(DISTINCT sales_agent) FROM sales_teams;` |
| T2 | How many regional offices do we have? | `SELECT COUNT(DISTINCT regional_office) FROM sales_teams;` |
| T3 | How many agents report to each manager? | `SELECT manager, COUNT(DISTINCT sales_agent) AS agent_count FROM sales_teams GROUP BY manager;` |
| T4 | List all agents in the 'Central' regional office. | `SELECT sales_agent FROM sales_teams WHERE regional_office = 'Central';` |
| T5 | How many managers do we have? | `SELECT COUNT(DISTINCT manager) FROM sales_teams;` |

---

## 4. Sales Pipeline — Counts & Filters

| ID | Question | Expected SQL |
| :--- | :--- | :--- |
| S1 | Total opportunities, all stages. | `SELECT COUNT(*) FROM sales_pipeline;` |
| S2 | How many deals are 'Won'? | `SELECT COUNT(*) FROM sales_pipeline WHERE deal_stage = 'Won';` |
| S3 | How many deals are 'Lost'? | `SELECT COUNT(*) FROM sales_pipeline WHERE deal_stage = 'Lost';` |
| S4 | How many deals are still 'Prospecting'? | `SELECT COUNT(*) FROM sales_pipeline WHERE deal_stage = 'Prospecting';` |
| S5 | How many deals are 'Engaging'? | `SELECT COUNT(*) FROM sales_pipeline WHERE deal_stage = 'Engaging';` |
| S6 | How many deals are open (Prospecting or Engaging)? | `SELECT COUNT(*) FROM sales_pipeline WHERE deal_stage IN ('Prospecting', 'Engaging');` |
| S7 | How many deals are closed (Won or Lost)? | `SELECT COUNT(*) FROM sales_pipeline WHERE deal_stage IN ('Won', 'Lost');` |
| S8 | How many distinct accounts appear in the pipeline at all? | `SELECT COUNT(DISTINCT account) FROM sales_pipeline;` |

---

## 5. Sales Pipeline — Official KPIs (per metrics.yaml)

| ID | KPI | Question | Expected SQL | Precision note |
| :--- | :--- | :--- | :--- | :--- |
| K1 | Won Revenue | Total Won Revenue? | `SELECT SUM(CASE WHEN deal_stage='Won' THEN close_value ELSE 0 END) FROM sales_pipeline;` | `SUM` already skips NULL close_value on Won rows by default (not treated as 0); flag such rows separately as a data-quality warning (see K1b) |
| K1b | Won Revenue — data quality check | How many Won deals have a missing close_value? | `SELECT COUNT(*) FROM sales_pipeline WHERE deal_stage='Won' AND close_value IS NULL;` | Should surface as a warning alongside K1, not silently ignored |
| K2 | Won Opportunities | How many opportunities were Won? | `SELECT COUNT(CASE WHEN deal_stage='Won' THEN opportunity_id END) FROM sales_pipeline;` | — |
| K3 | Lost Opportunities | How many opportunities were Lost? | `SELECT COUNT(CASE WHEN deal_stage='Lost' THEN opportunity_id END) FROM sales_pipeline;` | — |
| K4 | Closed Opportunities | How many reached a final outcome? | `SELECT COUNT(CASE WHEN deal_stage IN ('Won','Lost') THEN opportunity_id END) FROM sales_pipeline;` | — |
| K5 | Win Rate | Overall win rate? | `SELECT 100.0*COUNT(CASE WHEN deal_stage='Won' THEN opportunity_id END)/NULLIF(COUNT(CASE WHEN deal_stage IN ('Won','Lost') THEN opportunity_id END),0) FROM sales_pipeline;` | Denominator = Won+Lost only, never include open deals |
| K6 | Avg Won Deal Size | Average value of a Won deal? | `SELECT AVG(CASE WHEN deal_stage='Won' THEN close_value END) FROM sales_pipeline;` | `AVG` ignores NULL automatically — correct per metrics.yaml null_handling rule |
| K7 | Open Opportunities | How many are currently open? | `SELECT COUNT(CASE WHEN deal_stage IN ('Prospecting','Engaging') THEN opportunity_id END) FROM sales_pipeline;` | — |
| K8 | Open Pipeline Value | Estimated value of open pipeline? | `SELECT SUM(CASE WHEN s.deal_stage IN ('Prospecting','Engaging') THEN p.sales_price ELSE 0 END) FROM sales_pipeline s JOIN products p ON s.product=p.product;` | Estimate only, based on list price; requires JOIN — close_value is NULL on open deals |
| K9 | Win Rate by product | Win rate for each product? | `SELECT product, 100.0*COUNT(CASE WHEN deal_stage='Won' THEN opportunity_id END)/NULLIF(COUNT(CASE WHEN deal_stage IN ('Won','Lost') THEN opportunity_id END),0) AS win_rate FROM sales_pipeline GROUP BY product;` | Same denominator rule as K5 |
| K10 | Discount Rate | Discount rate per Won deal vs. list price? | `SELECT s.opportunity_id, 1-(s.close_value/NULLIF(p.sales_price,0)) AS discount_rate FROM sales_pipeline s JOIN products p ON s.product=p.product WHERE s.deal_stage='Won';` | Only valid for Won deals; NULLIF guards against a zero list price |
| K11 | Avg Discount Rate by product | Average discount rate given, by product? | `SELECT s.product, AVG(1-(s.close_value/NULLIF(p.sales_price,0))) AS avg_discount_rate FROM sales_pipeline s JOIN products p ON s.product=p.product WHERE s.deal_stage='Won' GROUP BY s.product;` | Same zero-guard as K10 |
| K12 | Avg Sales Cycle | Average days from engage to close, closed deals? | `SELECT AVG(CAST(close_date AS DATE) - CAST(engage_date AS DATE)) FROM sales_pipeline WHERE deal_stage IN ('Won','Lost');` | Closed deals only (both dates guaranteed present); explicit CAST in case columns load as text |
| K13 | Avg Sales Cycle by agent | Average sales cycle length by sales agent? | `SELECT sales_agent, AVG(CAST(close_date AS DATE) - CAST(engage_date AS DATE)) AS avg_cycle_days FROM sales_pipeline WHERE deal_stage IN ('Won','Lost') GROUP BY sales_agent;` | Same as K12, grouped |
| K14 | Deals per agent | How many deals does each sales agent have (any stage)? | `SELECT sales_agent, COUNT(*) AS deal_count FROM sales_pipeline GROUP BY sales_agent;` | Counts all stages, not just Won — compare with J9, which finds agents with zero |

---

## 6. Sales Pipeline — Dates

| ID | Question | Expected SQL | Nuance tested |
| :--- | :--- | :--- | :--- |
| D1 | Deals Won in Q1 2017? | `SELECT COUNT(*) FROM sales_pipeline WHERE deal_stage='Won' AND CAST(close_date AS DATE) BETWEEN '2017-01-01' AND '2017-03-31';` | Uses `close_date` for closed deals |
| D2 | Deals that entered 'Engaging' in Jan 2017? | `SELECT COUNT(*) FROM sales_pipeline WHERE CAST(engage_date AS DATE) BETWEEN '2017-01-01' AND '2017-01-31';` | Uses `engage_date`, not `close_date` |
| D3 | Total Won Revenue in 2017? | `SELECT SUM(close_value) FROM sales_pipeline WHERE deal_stage='Won' AND CAST(close_date AS DATE) BETWEEN '2017-01-01' AND '2017-12-31';` | Correct date field + stage filter combined |
| D4 | Full date range covered by the data? | `SELECT MIN(CAST(engage_date AS DATE)) AS earliest_engage, MAX(CAST(close_date AS DATE)) AS latest_close FROM sales_pipeline;` | Basic coverage check before trusting other answers |
| D5 | Are Prospecting deals with a missing engage_date a data error? | `SELECT COUNT(*) FROM sales_pipeline WHERE deal_stage='Prospecting' AND engage_date IS NULL;` | Should return ~500 and NOT be flagged as an error — documented as expected |
| D6 | Products with highest Won Revenue in the latest completed year, and their win rate? | `WITH latest_year AS (SELECT MAX(EXTRACT(YEAR FROM CAST(close_date AS DATE))) AS yr FROM sales_pipeline WHERE deal_stage IN ('Won','Lost')) SELECT product, SUM(CASE WHEN deal_stage='Won' THEN close_value ELSE 0 END) AS won_revenue, COUNT(CASE WHEN deal_stage='Won' THEN opportunity_id END) AS won_opportunities, COUNT(CASE WHEN deal_stage='Lost' THEN opportunity_id END) AS lost_opportunities, 100.0*COUNT(CASE WHEN deal_stage='Won' THEN opportunity_id END)/NULLIF(COUNT(CASE WHEN deal_stage IN ('Won','Lost') THEN opportunity_id END),0) AS win_rate FROM sales_pipeline, latest_year WHERE EXTRACT(YEAR FROM CAST(close_date AS DATE)) = latest_year.yr GROUP BY product ORDER BY won_revenue DESC;` | **No hardcoded year** — resolved dynamically from the data. This is the `initial_business_question` in metrics.yaml — the single most important eval in this set. Required output columns per metrics.yaml: product, won_revenue, won_opportunities, lost_opportunities, win_rate |
| D7 | How many months of pipeline data do we have? | `SELECT COUNT(DISTINCT strftime('%Y-%m', CAST(engage_date AS DATE))) FROM sales_pipeline WHERE engage_date IS NOT NULL;` | Tests month-grain date truncation, a common building block for trend questions |

---

## 7. Trap Questions (data cannot answer directly)

| ID | Question | Expected agent behavior |
| :--- | :--- | :--- |
| X1 | How much potential revenue did we lose on Lost deals? | Must NOT sum `close_value` for Lost (always 0). Should flag as not directly answerable, or offer `sales_price` as a labeled estimate. |
| X2 | Total value of our open deals? | Must NOT run `SUM(close_value)` on open deals (NULL). Must recognize this needs the Open Pipeline Value estimate (K8) and label it as such. |
| X3 | What was our revenue last month? | "Revenue" is ambiguous (`accounts.revenue` vs `won_revenue`) — should trigger clarification, not a silent default. |
| X4 | What is the win rate including open deals? | "Win rate" is fixed by definition to Won/(Won+Lost). Agent should not include open deals in the denominator even if the user's phrasing implies "all deals." |
| X5 | Show me revenue by customer segment. | "Segment" is not a defined dimension in accounts/semantic_layer.md (only sector, office_location, employee/revenue bands are documented). Agent should ask which of these is meant, not invent a "segment" field. |

---

## 8. Cross-Table Questions (JOINs)

| ID | Question | Expected SQL | Tables |
| :--- | :--- | :--- | :--- |
| J1 | Unique products purchased per account (Won only)? | `SELECT account, COUNT(DISTINCT product) AS unique_products FROM sales_pipeline WHERE deal_stage='Won' GROUP BY account;` | sales_pipeline |
| J2 | Accounts that purchased more than one distinct product? | `SELECT account, COUNT(DISTINCT product) AS product_count FROM sales_pipeline WHERE deal_stage='Won' GROUP BY account HAVING COUNT(DISTINCT product)>1;` | sales_pipeline |
| J3 | Accounts that bought the same product more than once? | `SELECT account, product, COUNT(*) AS purchase_count FROM sales_pipeline WHERE deal_stage='Won' GROUP BY account, product HAVING COUNT(*)>1;` | sales_pipeline |
| J4 | Product series with the most Won Revenue? | `SELECT p.series, SUM(s.close_value) AS total_revenue FROM sales_pipeline s JOIN products p ON s.product=p.product WHERE s.deal_stage='Won' GROUP BY p.series ORDER BY total_revenue DESC LIMIT 1;` | sales_pipeline + products |
| J5 | Avg sales price of products bought by Technology-sector accounts? | `SELECT AVG(p.sales_price) FROM sales_pipeline s JOIN products p ON s.product=p.product JOIN accounts a ON s.account=a.account WHERE a.sector='Technology' AND s.deal_stage='Won';` | sales_pipeline + products + accounts |
| J6 | Sales agent with the highest Won Revenue? | `SELECT sales_agent, SUM(close_value) AS total_revenue FROM sales_pipeline WHERE deal_stage='Won' GROUP BY sales_agent ORDER BY total_revenue DESC LIMIT 1;` | sales_pipeline |
| J7 | Win rate per regional office? | `SELECT t.regional_office, 100.0*COUNT(CASE WHEN s.deal_stage='Won' THEN s.opportunity_id END)/NULLIF(COUNT(CASE WHEN s.deal_stage IN ('Won','Lost') THEN s.opportunity_id END),0) AS win_rate FROM sales_pipeline s JOIN sales_teams t ON s.sales_agent=t.sales_agent GROUP BY t.regional_office;` | sales_pipeline + sales_teams |
| J8 | Manager whose team generated the most Won Revenue? | `SELECT t.manager, SUM(s.close_value) AS total_revenue FROM sales_pipeline s JOIN sales_teams t ON s.sales_agent=t.sales_agent WHERE s.deal_stage='Won' GROUP BY t.manager ORDER BY total_revenue DESC LIMIT 1;` | sales_pipeline + sales_teams |
| J9 | Any sales agents with no recorded opportunities? | `SELECT t.sales_agent FROM sales_teams t LEFT JOIN sales_pipeline s ON t.sales_agent=s.sales_agent WHERE s.opportunity_id IS NULL;` | sales_teams + sales_pipeline — **must be LEFT JOIN**; validates the documented 5-agent roster mismatch |
| J10 | Avg discount rate by sector? | `SELECT a.sector, AVG(1-(s.close_value/NULLIF(p.sales_price,0))) AS avg_discount_rate FROM sales_pipeline s JOIN products p ON s.product=p.product JOIN accounts a ON s.account=a.account WHERE s.deal_stage='Won' GROUP BY a.sector;` | sales_pipeline + products + accounts |
| J11 | Total customer annual revenue of accounts with at least one Won deal? | `SELECT SUM(revenue) FROM (SELECT DISTINCT a.account, a.revenue FROM accounts a JOIN sales_pipeline s ON a.account=s.account WHERE s.deal_stage='Won') AS won_accounts;` | accounts + sales_pipeline — tests agent doesn't double-count `accounts.revenue` once per deal; subquery requires an alias |
| J12 | Which accounts have Won deals but are not the top-revenue account in their sector? | `SELECT DISTINCT a.account, a.sector FROM accounts a JOIN sales_pipeline s ON a.account=s.account WHERE s.deal_stage='Won' AND a.account NOT IN (SELECT account FROM accounts a2 WHERE a2.sector=a.sector ORDER BY revenue DESC LIMIT 1);` | accounts + sales_pipeline — deliberately complex; acceptable if agent produces an equivalent window-function version instead (e.g. `RANK() OVER (PARTITION BY sector ORDER BY revenue DESC)`) |

---

## 9. Terminology Mapping Spot-Checks

Combine with any question above to confirm the agent maps colloquial terms to canonical fields correctly.

| Business term | Canonical field | Test with |
| :--- | :--- | :--- |
| deal | `opportunity` | any S/K question |
| customer / company / client / prospect | `account` | any A/J question |
| rep / salesperson / AE | `sales_agent` | T1, T4, J6 |
| sales manager | `manager` | T3, J8 |
| region | `regional_office` | T2, T4, J7 |
| deal value / deal size | `close_value` | K1, K6 |
| list price / MSRP | `products.sales_price` | K8, K10 |
| closed deal | Won or Lost | S7, K4 |
| open deal / pipeline | Prospecting or Engaging | S6, K7, K8 |
| industry | `sector` | A5, A8 |

---

## Known Limitations of This Dataset

- Not yet run against the live agent — SQL here is analyst-verified against `semantic_layer.md`/`metrics.yaml`, not yet execution-tested against the actual DuckDB file (`ask_data.duckdb`).
- Assumes `engage_date`/`close_date` need explicit `CAST(... AS DATE)`; remove casts if the loader already stores them as native DATE type.
- J12 is intentionally adv∂anced (ranking/window-function territory) — keep as a stretch goal, not a pass/fail blocker for early iterations.
- This dataset will need updates if `metrics.yaml` or `semantic_layer.md` change — check the "Official KPIs" and "Dates" sections first, they are most tightly coupled to those source files.

---

**Total evals: 56** (Accounts 11, Products 7, Sales Teams 5, Pipeline counts 8, KPIs 14, Dates 7, Traps 5, Joins 12, Terminology 10 cross-refs)

## Scope-Control Evaluations

| ID | Question | Expected behavior |
|---|---|---|
| SC1 | Which marketing campaign generated the most leads? | Return `OUT_OF_SCOPE`; do not generate SQL |
| SC2 | What was our customer-support resolution time? | Return `OUT_OF_SCOPE`; do not generate SQL |
| SC3 | Which products generated the most won revenue? | Continue to clarification and SQL |
| SC4 | Which products had the most sales and website engagement? | Explain that sales is supported but website engagement is not; ask whether to continue with sales only |
| SC5 | What was our profit last year? | Return `OUT_OF_SCOPE`; the dataset has won revenue but no costs or profit |
| SC6 | Which campaign performed best? | Ask what campaign means or explain that marketing campaign data is unavailable |
| SC7 | Which accounts had the highest annual company revenue? | Continue because customer annual revenue is supported |
| SC8 | Which products had the highest customer usage? | Return `OUT_OF_SCOPE`; product sales are supported but product usage is not |
