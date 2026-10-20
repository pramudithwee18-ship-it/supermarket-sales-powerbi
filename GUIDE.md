# Power BI Project Guide: UrbanBasket Supermarket Sales Dashboard

A step-by-step guide to building a **4-page Power BI dashboard** from the CSV files in `data/`.
Allow about 2–3 days. Do each step yourself in Power BI: the point is that you can explain every part in an interview.

> UrbanBasket Supermarkets is a **fictional** chain. All data is simulated with `src/generate_data.py`.

---

## Step 0: Install Power BI Desktop (free)

1. Open the **Microsoft Store** on Windows and search for **Power BI Desktop**, then click **Get / Install**.
2. Open it. You can close the sign-in pop-up; you don't need an account for Power BI Desktop.

---

## Step 1: Understand the data

| File | Rows | What it is | Key |
|------|------|------------|-----|
| `sales.csv` | 448k | One row per product line in a till receipt (fact table) | TransactionID + LineNo |
| `products.csv` | 66 | Product name, unit, category, department, brand | ProductID |
| `branches.csv` | 13 | Branch, district, province, format (Hypermarket / Supermarket / Express), opening date, floor area | BranchID |
| `targets.csv` | 294 | Monthly sales target for each branch | MonthStart + BranchID |

`sales.csv` columns: `TransactionID, LineNo, Date, Hour, BranchID, PaymentMethod, LoyaltyMember, ProductID, Quantity, UnitPrice, UnitCost, DiscountPct`

---

## Step 2: Load the data

1. **Home → Get data → Text/CSV** and choose `data/sales.csv`, then click **Transform Data** (not Load).
2. In Power Query, use **Home → New Source → Text/CSV** to add `products.csv`, `branches.csv` and `targets.csv`.
3. Rename the queries to `Sales`, `Products`, `Branches` and `Targets`.

---

## Step 3: Clean the data in Power Query

The data has **deliberate problems**. Finding and fixing them is part of the project; mention it in interviews.

### Sales
| Problem | Fix in Power Query |
|---------|--------------------|
| 60 duplicate rows | Select **all columns**, then **Home → Remove Rows → Remove Duplicates** |
| 896 blank `PaymentMethod` | Select the column, **Transform → Replace Values**, replace an empty value with `Unknown` |
| 1,345 returns (negative `Quantity`) | Keep them, but add a flag: **Add Column → Conditional Column** `IsReturn` = `TRUE` if `Quantity < 0`, else `FALSE` |
| Data types | `Date` = Date, `Hour` / `Quantity` / `LineNo` = Whole Number, prices = Decimal, `DiscountPct` = Percentage |

Then add two **Custom Columns** (**Add Column → Custom Column**):

```
Revenue = [Quantity] * [UnitPrice] * (1 - [DiscountPct])
Cost    = [Quantity] * [UnitCost]
```
Set both to **Decimal Number**.

### Products
| Problem | Fix |
|---------|-----|
| Some categories are in CAPITALS with an extra space (`RICE & GRAINS `) | Select `Category`, **Transform → Format → Trim**, then **Format → Capitalize Each Word** |

Check: `Category` should now have exactly **12** distinct values (click the column's filter arrow to see them).

Click **Home → Close & Apply**.

---

## Step 4: Build the data model

### 4a. Create a Date table
**Modeling → New table**, then paste:

```DAX
Date =
ADDCOLUMNS (
    CALENDAR ( DATE ( 2024, 1, 1 ), DATE ( 2025, 12, 31 ) ),
    "Year", YEAR ( [Date] ),
    "Quarter", "Q" & QUARTER ( [Date] ),
    "Month No", MONTH ( [Date] ),
    "Month", FORMAT ( [Date], "MMM" ),
    "Year Month", FORMAT ( [Date], "YYYY-MM" ),
    "Weekday No", WEEKDAY ( [Date], 2 ),
    "Weekday", FORMAT ( [Date], "ddd" ),
    "Is Weekend", IF ( WEEKDAY ( [Date], 2 ) > 5, "Weekend", "Weekday" )
)
```
- Select the table, then **Table tools → Mark as date table** and choose `Date`.
- Select the `Month` column, then **Column tools → Sort by column → Month No**. Do the same for `Weekday` → `Weekday No`.

### 4b. Relationships
Open **Model view** (the third icon on the left) and drag between columns to create these relationships:

| From (many) | To (one) |
|-------------|----------|
| `Sales[Date]` | `Date[Date]` |
| `Sales[ProductID]` | `Products[ProductID]` |
| `Sales[BranchID]` | `Branches[BranchID]` |
| `Targets[MonthStart]` | `Date[Date]` |
| `Targets[BranchID]` | `Branches[BranchID]` |

All relationships should be **one-to-many, single direction**. This layout is a **star schema**: one fact table (`Sales`) surrounded by dimension tables. `Targets` is a second fact table at month level.

> Interview tip: be ready to explain *why* a separate Date table is needed. It's required for time-intelligence functions like `SAMEPERIODLASTYEAR`, and gives you one consistent calendar for both fact tables.

---

## Step 5: Write the DAX measures

First create an empty table to hold them: **Home → Enter data**, name it `_Measures`, and click **Load**. Then right-click `_Measures`, choose **New measure**, and add each measure below. Set the format (currency LKR, %, whole number) in **Measure tools**.

### Core sales
```DAX
Net Sales = SUM ( Sales[Revenue] )

Gross Sales = CALCULATE ( SUM ( Sales[Revenue] ), Sales[IsReturn] = FALSE () )

Returns Value = - CALCULATE ( SUM ( Sales[Revenue] ), Sales[IsReturn] = TRUE () )

Total Cost = SUM ( Sales[Cost] )

Gross Profit = [Net Sales] - [Total Cost]

GP Margin % = DIVIDE ( [Gross Profit], [Net Sales] )

Discount Given = SUMX ( Sales, Sales[Quantity] * Sales[UnitPrice] * Sales[DiscountPct] )
```

### Customer behaviour
```DAX
Transactions = DISTINCTCOUNT ( Sales[TransactionID] )

Avg Basket Value = DIVIDE ( [Net Sales], [Transactions] )

Items per Basket = DIVIDE ( SUM ( Sales[Quantity] ), [Transactions] )

Loyalty Sales % =
DIVIDE ( CALCULATE ( [Net Sales], Sales[LoyaltyMember] = "Yes" ), [Net Sales] )
```

### Time intelligence
```DAX
Net Sales LY = CALCULATE ( [Net Sales], SAMEPERIODLASTYEAR ( 'Date'[Date] ) )

YoY Growth % = DIVIDE ( [Net Sales] - [Net Sales LY], [Net Sales LY] )

Sales YTD = TOTALYTD ( [Net Sales], 'Date'[Date] )

Sales 3M Moving Avg =
AVERAGEX ( DATESINPERIOD ( 'Date'[Date], MAX ( 'Date'[Date] ), -3, MONTH ), [Net Sales] )
```

### Targets and ranking
```DAX
Target = SUM ( Targets[TargetRevenue] )

Target Achievement % = DIVIDE ( [Net Sales], [Target] )

Branch Rank = RANKX ( ALL ( Branches[BranchName] ), [Net Sales] )

Sales per Sq Ft = DIVIDE ( [Net Sales], SUM ( Branches[FloorAreaSqFt] ) )
```

> Check your numbers: with no filters, **Net Sales ≈ LKR 322 M** and **Transactions = 90,922**. If yours are different, re-check the duplicate removal in Step 3.

> Targets are monthly, so show `Target` and `Target Achievement %` by **month, quarter or year**, not by day.

---

## Step 6: Build the report pages

Use one colour theme throughout: **View → Themes** (or **Browse for themes** to load a JSON file). Use a page title at the top, slicers in a column on the left, and KPI cards in a row across the top.

### Page 1: Executive Overview
| Visual | Fields |
|--------|--------|
| 5 **Card** visuals | Net Sales, Gross Profit, GP Margin %, Transactions, YoY Growth % |
| **Line chart** | X: `Date[Year Month]`; Y: Net Sales and Net Sales LY |
| **Clustered bar chart** | Y: `Products[Category]`; X: Net Sales (sorted descending) |
| **Filled map** or bar chart | `Branches[Province]` by Net Sales |
| **Slicers** | `Date[Year]`, `Branches[Format]`, `Products[Department]` |

### Page 2: Branch Performance
| Visual | Fields |
|--------|--------|
| **Matrix** | Rows: BranchName; Values: Net Sales, Target, Target Achievement %, Avg Basket Value, Branch Rank. Add **conditional formatting** (red/green) on Achievement % |
| **Clustered column chart** | BranchName by Net Sales and Target |
| **Scatter chart** | X: FloorAreaSqFt; Y: Net Sales; Details: BranchName. Which branches use their space best? |
| **Slicer** | `Date[Year Month]` (dropdown) |

### Page 3: Products & Categories
| Visual | Fields |
|--------|--------|
| **Treemap** | Group: Department, then Category; Values: Net Sales |
| **Bar chart: Top 10 products** | ProductName by Net Sales. In the **Filters pane**, set ProductName → **Top N** = 10 by Net Sales |
| **Column chart** | Category by GP Margin % |
| **Line chart** | Month by Net Sales, with Category as the legend (look for seasonal products) |
| **Card** | Discount Given, Returns Value |

### Page 4: Customers & Payments
| Visual | Fields |
|--------|--------|
| **100% stacked column chart** | X: Year Month; Y: Transactions; Legend: PaymentMethod (shows the shift away from cash) |
| **Donut chart** | LoyaltyMember by Net Sales |
| **Matrix heatmap** | Rows: `Sales[Hour]`; Columns: `Date[Weekday]`; Values: Transactions. Add a **background colour scale** with conditional formatting to find the busiest hours |
| **Cards** | Avg Basket Value, Items per Basket, Loyalty Sales % |

### Extra features (they make the project stand out)
- **Drill-through:** right-click a branch on page 1 to open a detailed page for that branch (**Drill through** in the Visualizations pane).
- **Tooltip page:** a small page that appears when you hover over a chart.
- **Bookmarks + buttons:** a navigation bar at the top of each page.
- **What-if parameter** (**Modeling → New parameter**): "What if we increase prices by X%?"

---

## Step 7: Find the insights

The data was generated with real-world patterns. Use your dashboard to answer these questions, and write the answers (with numbers) in the README:

1. Which **month** has the highest sales, and why? (Think about Sri Lankan festivals.)
2. How much did sales **grow from 2024 to 2025**? How much of that is price increases and how much is more transactions?
3. Which **branch format** has the biggest baskets? Which has the most transactions per sq ft?
4. Which **categories** sell more in the hot months (March–May)?
5. How has the **cash vs card vs mobile wallet** mix changed?
6. What are the **busiest days and hours**? How should staff rosters change?
7. Which branches **missed their targets** most often?
8. How did the **new Ratnapura branch** (opened July 2025) perform in its first months?

---

## Step 8: Publish to GitHub

1. Save the report as `UrbanBasket_Sales_Dashboard.pbix` in this folder.
2. Take a **screenshot of each page** (use **File → Export → PDF**, or Windows **Snipping Tool**) and save them in `images/` as `01_overview.png`, `02_branches.png`, `03_products.png` and `04_customers.png`.
3. Fill in the README: the screenshots, your answers from Step 7, and the DAX measures you're proud of.
4. Publish the folder with **GitHub Desktop** (**File → Add local repository → Publish**, untick *Keep private*).

Recruiters usually won't download the `.pbix`, so **the screenshots in the README are the most important part**.

---

## For your CV

> **UrbanBasket Supermarket Sales Dashboard (Power BI)**: Built a 4-page Power BI dashboard on 448k retail transactions across 13 branches. Cleaned the data in Power Query, designed a star-schema model, and wrote DAX measures for YoY growth, target achievement and basket analysis to reveal seasonal peaks, branch performance and payment trends. – Github link
