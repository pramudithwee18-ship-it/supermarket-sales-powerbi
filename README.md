# 🛒 UrbanBasket Supermarket Sales Dashboard (Power BI)

An interactive **Power BI** dashboard analysing two years (2024–2025) of retail sales for **UrbanBasket Supermarkets**, a fictional chain with 13 branches across Sri Lanka.

> All data is **simulated** (see [`src/generate_data.py`](src/generate_data.py)). The simulation follows realistic patterns: Sinhala & Tamil New Year and Christmas peaks, weekend and salary-day effects, a shift from cash to digital payments, and a new branch opening.

**Tools:** Power BI · Power Query · DAX · Data modelling (star schema) · Python (data generation)

## Dashboard

### 1. Executive Overview
![Executive Overview](images/01_overview.png)

### 2. Branch Performance
![Branch Performance](images/02_branches.png)

### 3. Products & Categories
![Products & Categories](images/03_products.png)

### 4. Customers & Payments
![Customers & Payments](images/04_customers.png)

## Key insights

_To do: fill in after building the dashboard (see GUIDE.md, Step 7)._

1. ...
2. ...
3. ...

## Data model

Star schema: `Sales` (448k rows) and `Targets` (monthly) fact tables, linked to `Date`, `Products` and `Branches` dimension tables.

![Data model](images/model.png)

## Data cleaning (Power Query)

- Removed 60 duplicate transaction lines
- Flagged 1,345 returns (negative quantities) and kept them in Net Sales
- Replaced 896 blank payment methods with "Unknown"
- Standardised inconsistent category names (trimmed spaces, fixed capitalisation)

## Key DAX measures

```DAX
Net Sales LY = CALCULATE ( [Net Sales], SAMEPERIODLASTYEAR ( 'Date'[Date] ) )
YoY Growth % = DIVIDE ( [Net Sales] - [Net Sales LY], [Net Sales LY] )
Target Achievement % = DIVIDE ( [Net Sales], [Target] )
Avg Basket Value = DIVIDE ( [Net Sales], [Transactions] )
```

## Files

```
UrbanBasket_Sales_Dashboard.pbix   Power BI report
data/                              sales, products, branches, targets (CSV)
src/generate_data.py               Generates the simulated dataset
images/                            Dashboard screenshots
GUIDE.md                           Step-by-step build guide
```

---
Built by **Pramuditha Weerathunga**
