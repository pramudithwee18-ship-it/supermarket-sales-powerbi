"""Generate a simulated retail dataset for a fictional Sri Lankan supermarket
chain ("UrbanBasket Supermarkets"), Jan 2024 - Dec 2025.

All data is SIMULATED for a portfolio project. It does not describe any real company.

Patterns built in, so the dashboard has real insights to find:
  * Sinhala & Tamil New Year (April) is the biggest month; December (Christmas) is second
  * Weekends are busier; salary days (25th - 5th) have bigger baskets
  * Beverages and ice cream sell more in the hot months (Mar - May)
  * Hypermarkets have bigger baskets; Express stores have more, smaller baskets
  * Card and mobile-wallet payments grow over time, cash declines
  * About 8% year-on-year growth; one new branch opens in mid-2025

Deliberate data-quality issues (to clean in Power Query):
  * duplicate transaction lines, returns (negative quantity),
  * blank payment methods, extra spaces / inconsistent case in category names

Usage:  python src/generate_data.py
Output: data/*.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(7)
OUT = Path(__file__).resolve().parents[1] / "data"
OUT.mkdir(exist_ok=True)
START, END = "2024-01-01", "2025-12-31"

# ---------------------------------------------------------------- Products
# category: (department, margin, [(product, unit, price LKR), ...], hot-season boost)
CATALOG = {
    "Rice & Grains": ("Grocery", 0.10, [("Samba Rice", "5 kg", 1450), ("Nadu Rice", "5 kg", 1180),
                      ("Red Raw Rice", "5 kg", 1320), ("Basmati Rice", "1 kg", 690), ("Dhal (Mysore)", "1 kg", 340),
                      ("Green Gram", "500 g", 420), ("Chickpeas", "500 g", 380)], 1.0),
    "Cooking Essentials": ("Grocery", 0.12, [("Coconut Oil", "1 L", 780), ("Vegetable Oil", "1 L", 690),
                           ("White Sugar", "1 kg", 280), ("Wheat Flour", "1 kg", 230), ("Salt", "1 kg", 120),
                           ("Chilli Powder", "250 g", 480), ("Curry Powder", "250 g", 450), ("Turmeric", "100 g", 260)], 1.0),
    "Dairy & Eggs": ("Fresh", 0.15, [("Full Cream Milk Powder", "400 g", 1150), ("Fresh Milk", "1 L", 520),
                     ("Yoghurt", "80 g", 90), ("Cheese Slices", "200 g", 1050), ("Butter", "200 g", 980),
                     ("Eggs (10 pack)", "10 pcs", 520)], 1.0),
    "Beverages": ("Grocery", 0.18, [("Ceylon Black Tea", "200 g", 640), ("Instant Coffee", "100 g", 1350),
                  ("Soft Drink", "1.5 L", 420), ("Fruit Juice", "1 L", 580), ("Mineral Water", "1.5 L", 140),
                  ("Energy Drink", "250 ml", 390), ("Malted Drink Powder", "400 g", 990)], 1.35),
    "Snacks & Biscuits": ("Grocery", 0.22, [("Cream Crackers", "190 g", 230), ("Chocolate Biscuits", "100 g", 210),
                          ("Potato Chips", "50 g", 180), ("Mixture", "200 g", 350), ("Chocolate Bar", "50 g", 290),
                          ("Kokis Pack", "200 g", 420)], 1.05),
    "Bakery": ("Fresh", 0.25, [("Sandwich Bread", "450 g", 190), ("Fish Bun", "1 pc", 120),
               ("Butter Cake", "500 g", 850), ("Rotti Pack", "5 pcs", 250)], 1.0),
    "Fruits & Vegetables": ("Fresh", 0.20, [("Bananas (Ambul)", "1 kg", 380), ("Carrots", "1 kg", 520),
                            ("Onions (Big)", "1 kg", 360), ("Potatoes", "1 kg", 410), ("Tomatoes", "1 kg", 480),
                            ("Leeks", "1 kg", 430), ("Papaya", "1 kg", 300)], 1.0),
    "Meat & Fish": ("Fresh", 0.14, [("Chicken (Whole)", "1 kg", 1350), ("Chicken Sausages", "500 g", 980),
                    ("Tuna (Kelawalla)", "1 kg", 2400), ("Prawns", "500 g", 1650), ("Dried Fish", "250 g", 780)], 1.0),
    "Frozen Foods": ("Fresh", 0.20, [("Ice Cream", "1 L", 890), ("Frozen Chicken Nuggets", "400 g", 1250),
                     ("Frozen Mixed Vegetables", "500 g", 680)], 1.4),
    "Household Care": ("Non-Food", 0.24, [("Washing Powder", "1 kg", 690), ("Dishwash Liquid", "500 ml", 420),
                       ("Floor Cleaner", "1 L", 560), ("Toilet Cleaner", "500 ml", 480), ("Tissue Rolls", "4 pack", 520)], 1.0),
    "Personal Care": ("Non-Food", 0.28, [("Toothpaste", "120 g", 380), ("Shampoo", "180 ml", 690),
                      ("Bath Soap", "100 g", 190), ("Body Lotion", "200 ml", 980), ("Herbal Soap", "100 g", 220)], 1.05),
    "Baby Care": ("Non-Food", 0.20, [("Baby Diapers", "30 pack", 3450), ("Baby Wipes", "80 pcs", 790),
                  ("Infant Formula", "400 g", 2350)], 1.0),
}
BRANDS = ["UrbanBasket", "Lanka Choice", "GoldenLeaf", "Island Fresh", "PureLife", "Ceylon Pride"]

products = []
for cat, (dept, margin, items, _) in CATALOG.items():
    for name, unit, price in items:
        products.append({
            "ProductID": f"P{len(products) + 1:03d}",
            "ProductName": name,
            "Unit": unit,
            "Category": cat,
            "Department": dept,
            "Brand": rng.choice(BRANDS),
            "UnitPrice2024": float(price),
            "UnitCost2024": round(price * (1 - margin * rng.uniform(0.8, 1.2)), 2),
        })
products = pd.DataFrame(products)
# popularity: cheap everyday items sell more often
pop = 1 / np.sqrt(products.UnitPrice2024)
pop *= products.Category.map({"Rice & Grains": 1.3, "Cooking Essentials": 1.3, "Bakery": 1.5,
                              "Fruits & Vegetables": 1.4, "Dairy & Eggs": 1.2}).fillna(1.0)

# ---------------------------------------------------------------- Branches
BRANCHES = [  # name, district, province, format, opened, size factor
    ("Colombo 07", "Colombo", "Western", "Hypermarket", "2016-03-01", 1.8),
    ("Nugegoda", "Colombo", "Western", "Supermarket", "2017-06-01", 1.3),
    ("Dehiwala", "Colombo", "Western", "Express", "2020-09-01", 0.7),
    ("Negombo", "Gampaha", "Western", "Supermarket", "2018-02-01", 1.1),
    ("Gampaha", "Gampaha", "Western", "Supermarket", "2019-05-01", 1.0),
    ("Panadura", "Kalutara", "Western", "Express", "2021-01-01", 0.65),
    ("Kandy City", "Kandy", "Central", "Hypermarket", "2017-11-01", 1.5),
    ("Peradeniya", "Kandy", "Central", "Express", "2022-04-01", 0.6),
    ("Galle Fort", "Galle", "Southern", "Supermarket", "2018-08-01", 1.0),
    ("Matara", "Matara", "Southern", "Supermarket", "2020-03-01", 0.85),
    ("Kurunegala", "Kurunegala", "North Western", "Supermarket", "2019-10-01", 0.95),
    ("Jaffna", "Jaffna", "Northern", "Supermarket", "2023-02-01", 0.75),
    ("Ratnapura", "Ratnapura", "Sabaragamuwa", "Express", "2025-07-01", 0.6),   # new branch
]
branches = pd.DataFrame(BRANCHES, columns=["BranchName", "District", "Province", "Format", "OpenDate", "Size"])
branches.insert(0, "BranchID", [f"B{i + 1:02d}" for i in range(len(branches))])
branches["FloorAreaSqFt"] = (branches.Size * 9000 * rng.uniform(0.9, 1.1, len(branches))).round(-2).astype(int)
FORMAT_BASKET = {"Hypermarket": 6.5, "Supermarket": 4.5, "Express": 2.6}   # avg items per basket
FORMAT_TRAFFIC = {"Hypermarket": 1.0, "Supermarket": 1.0, "Express": 1.35}

# ---------------------------------------------------------------- Calendar effects
days = pd.date_range(START, END, freq="D")
month_factor = np.array([0.95, 0.9, 1.05, 1.45, 1.05, 0.95, 0.95, 0.95, 0.97, 1.0, 1.05, 1.3])
weekday_factor = np.array([0.9, 0.88, 0.9, 0.95, 1.05, 1.3, 1.2])  # Mon..Sun
day_factor = (month_factor[days.month - 1] * weekday_factor[days.weekday]
              * 1.08 ** ((days - days[0]).days / 365.25))
# the week before New Year (14 April) is extra busy
avurudu = (days.month == 4) & (days.day >= 5) & (days.day <= 13)
day_factor = np.where(avurudu, day_factor * 1.5, day_factor)
salary = (days.day >= 25) | (days.day <= 5)

# ---------------------------------------------------------------- Transactions (baskets)
baskets = []
for _, b in branches.iterrows():
    open_mask = days >= pd.Timestamp(b.OpenDate)
    n = rng.poisson(8 * b.Size * FORMAT_TRAFFIC[b.Format] * day_factor * open_mask)
    idx = np.repeat(np.arange(len(days)), n)
    baskets.append(pd.DataFrame({"day": idx, "BranchID": b.BranchID, "Format": b.Format}))
baskets = pd.concat(baskets, ignore_index=True)
nb = len(baskets)
baskets["TransactionID"] = [f"T{i + 1:07d}" for i in range(nb)]
baskets["Date"] = days[baskets.day]
hour_p = np.array([2, 5, 7, 7, 6, 6, 7, 9, 11, 12, 11, 8, 5, 4], float)  # 8am .. 9pm
baskets["Hour"] = rng.choice(np.arange(8, 22), nb, p=hour_p / hour_p.sum())
progress = baskets.day.to_numpy() / len(days)                 # 0 -> 1 over the period
cash_p = 0.55 - 0.15 * progress
wallet_p = 0.10 + 0.10 * progress
u = rng.random(nb)
baskets["PaymentMethod"] = np.where(u < cash_p, "Cash", np.where(u < cash_p + wallet_p, "Mobile Wallet", "Card"))
baskets["LoyaltyMember"] = np.where(rng.random(nb) < 0.42, "Yes", "No")
mean_items = baskets.Format.map(FORMAT_BASKET).to_numpy() * np.where(salary[baskets.day], 1.2, 1.0)
baskets["Items"] = 1 + rng.poisson(mean_items - 1)

# ---------------------------------------------------------------- Sales lines
lines = baskets.loc[baskets.index.repeat(baskets.Items),
                    ["TransactionID", "Date", "Hour", "BranchID", "PaymentMethod", "LoyaltyMember"]].reset_index(drop=True)
lines.insert(1, "LineNo", lines.groupby("TransactionID").cumcount() + 1)
month = lines.Date.dt.month.to_numpy()
hot = np.isin(month, [3, 4, 5])
# pick products; hot-season categories get a boost in Mar-May
boost = products.Category.map({c: v[3] for c, v in CATALOG.items()}).to_numpy()
p_normal = (pop / pop.sum()).to_numpy()
p_hot = pop.to_numpy() * boost
p_hot = p_hot / p_hot.sum()
prod_idx = np.where(hot, rng.choice(len(products), len(lines), p=p_hot),
                    rng.choice(len(products), len(lines), p=p_normal))
prod = products.iloc[prod_idx].reset_index(drop=True)
lines["ProductID"] = prod.ProductID
lines["Quantity"] = 1 + rng.poisson(np.where(prod.UnitPrice2024 < 400, 0.9, 0.25))
inflation = np.where(lines.Date.dt.year >= 2025, 1.06, 1.0)     # 6% price rise in 2025
lines["UnitPrice"] = (prod.UnitPrice2024 * inflation).round(2)
lines["UnitCost"] = (prod.UnitCost2024 * inflation).round(2)
promo = rng.random(len(lines)) < 0.12
lines["DiscountPct"] = np.where(promo, rng.choice([0.05, 0.10, 0.15, 0.20], len(lines)), 0.0)
lines["Date"] = lines.Date.dt.date

# ---------------------------------------------------------------- Dirty data
products_out = products.drop(columns=["UnitPrice2024", "UnitCost2024"]).copy()
messy = rng.random(len(products_out)) < 0.15
products_out.loc[messy, "Category"] = products_out.loc[messy, "Category"].str.upper() + " "
returns = lines.sample(frac=0.003, random_state=1).index
lines.loc[returns, "Quantity"] = -lines.loc[returns, "Quantity"]
lines.loc[lines.sample(frac=0.002, random_state=3).index, "PaymentMethod"] = ""
lines = pd.concat([lines, lines.sample(60, random_state=2)]).sort_values(["Date", "TransactionID"])

# ---------------------------------------------------------------- Monthly targets per branch
clean = lines[lines.Quantity > 0].drop_duplicates()
clean = clean.assign(Revenue=clean.Quantity * clean.UnitPrice * (1 - clean.DiscountPct),
                     MonthStart=pd.to_datetime(clean.Date).dt.to_period("M").dt.to_timestamp())
targets = clean.groupby(["MonthStart", "BranchID"]).Revenue.sum().reset_index()
targets["TargetRevenue"] = (targets.Revenue * rng.normal(1.03, 0.06, len(targets))).round(-4)
targets = targets.drop(columns="Revenue")
targets["MonthStart"] = targets.MonthStart.dt.date

# ---------------------------------------------------------------- Save
products_out.to_csv(OUT / "products.csv", index=False)
branches.drop(columns="Size").to_csv(OUT / "branches.csv", index=False)
lines.to_csv(OUT / "sales.csv", index=False)
targets.to_csv(OUT / "targets.csv", index=False)

print(f"products {len(products_out):>9,}")
print(f"branches {len(branches):>9,}")
print(f"sales    {len(lines):>9,} lines in {nb:,} transactions")
print(f"targets  {len(targets):>9,}")
print(f"revenue  LKR {clean.Revenue.sum() / 1e6:,.1f} M (clean)")
