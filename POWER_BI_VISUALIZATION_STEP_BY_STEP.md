# 📊 Step-by-Step Guide: Building Pizza Analytics in Power BI

This guide provides a detailed walkthrough for cashiers and managers to create professional charts and analytics using the exported CSV data from the FJC Pizza system.

---

## 🛠️ Step 1: Connecting the Data
1.  Open **Power BI Desktop**.
2.  Click **Get Data** > **Text/CSV**.
3.  Import all files from the `bi_exports` folder:
    - `fact_sales.csv`
    - `fact_stock_transactions.csv`
    - `fact_waste.csv`
    - `fact_inventory_counts.csv`
    - `dim_products.csv`
    - `dim_ingredients.csv`
    - `dim_users.csv`
    - `dim_recipes.csv`

---

## 🏗️ Step 2: Data Modeling (The Relationships)
Go to the **Model View** (left sidebar) and ensure the following links exist:
- **Product Relationship**: `dim_products[Name]` ↔ `fact_sales[Item_Product]`
- **Ingredient Relationship**: `dim_ingredients[Name]` ↔ `fact_stock_transactions[Ingredient_Name]`
- **Sales Date**: Create a **Calendar Table** using DAX:
  ```dax
  DimCalendar = CALENDARAUTO()
  ```
  Then link `DimCalendar[Date]` to `fact_sales[Order_Date]`.

---

## 📈 Step 3: Creating Essential Charts

### 1. Sales Trend (Line Chart)
*   **Purpose**: Identify which days/hours are the busiest for the pizza shop.
*   **X-Axis**: `DimCalendar[Date]`
*   **Y-Axis**: `SUM(fact_sales[Item_Subtotal])`
*   **Legend**: `fact_sales[Item_Category]`
*   **Tip**: Right-click the X-axis and select **Expand to Next Level** to see daily sales.

### 2. Product Popularity (Tree Map)
*   **Purpose**: See which pizza flavors are "Best Sellers."
*   **Category**: `dim_products[Name]`
*   **Values**: `SUM(fact_sales[Item_Quantity])`
*   **Color**: Set colors to FJC Pizza brand (e.g., Orange/Red).

### 3. Waste Analysis (Clustered Bar Chart)
*   **Purpose**: Identify which ingredients are being thrown away the most.
*   **X-Axis**: `fact_waste[Ingredient_Name]`
*   **Y-Axis**: `SUM(fact_waste[Quantity])`
*   **Legend**: `fact_waste[Type]` (Spoilage, Freebie, etc.)

---

## 🧮 Step 4: Powerful DAX Measures (The "Secret Sauce")

### A. Total Revenue
```dax
Total Revenue = SUM(fact_sales[Item_Subtotal])
```

### B. Waste-to-Sales Ratio
```dax
Waste Ratio = 
DIVIDE(
    SUM(fact_waste[Quantity]), 
    SUM(fact_sales[Item_Quantity]), 
    0
)
```

### C. Low Stock Alert (KPI)
*   Create a **Card Visual**.
*   **Measure**:
```dax
Critical Stock Count = 
COUNTROWS(
    FILTER(dim_ingredients, [Current_Stock] < [Min_Stock])
)
```

---

## 🎨 Step 5: Design & Aesthetics
1.  **Themes**: Go to **View** > **Themes** and select a "Dark Mode" or "High Contrast" theme for a premium feel.
2.  **Slicers**: Add a **Slicer** for `DimCalendar[Date]` (Date Range) and `dim_products[Category]` to allow users to filter the entire report.
3.  **Visual Polish**: Turn on **Shadows** and **Rounded Corners** in the "Format" pane for every visual.

---

## 🚀 Final Checklist
- [ ] Are the relationships linked?
- [ ] Do the colors match the brand?
- [ ] Is the "Total Revenue" card clearly visible?
- [ ] Can you filter by date?

*This guide is part of the FJC Pizza BI Implementation Suite.*
