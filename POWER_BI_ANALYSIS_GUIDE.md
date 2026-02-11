# 📊 Power BI Business Analysis Guide: FJC Pizza Sales & Inventory

This guide outlines the strategy for implementing a professional Business Intelligence (BI) suite using Power BI for the FJC Pizza Sales & Inventory System.

## 📈 Analysis Implementation Overview
| Metric | Target | Description |
|--------|--------|-------------|
| **Primary Tables** | 6 | Core fact & dimension tables for data modeling. |
| **Supporting Tables** | 3 | Calendar, Measure Groups, and Parameter tables. |
| **Visualizations** | 15+ | Across 3 specialized report pages. |
| **DAX Measures** | 20+ | Calculated KPIs and time-intelligence analysis. |
| **Implementation Progress** | 80% | Current status (Seeders & Export Engine implemented). |

---

## 🏗️ 1. Data Model Structure (The Tables)
To perform robust analysis, we need to export the following tables from the Django database to CSV/DirectQuery:

1.  **FactSales**: Order Items, Quantity, Prices, and Subtotals.
2.  **FactInventory**: Stock Transactions, Waste Logs, and Physical Counts.
3.  **DimProducts**: Product Names, Categories, and BOM Requirements.
4.  **DimIngredients**: Raw Materials, Units, and Thresholds.
5.  **DimUsers**: Cashiers and Admins (for performance tracking).
6.  **DimCalendar**: **(CRITICAL)** Generated in Power BI for Time Intelligence.

---

## 🧮 2. Key DAX Measures (The Logic)

### Revenue & Sales
-   **Total Sales**: `SUM(FactSales[Subtotal])`
-   **Avg Ticket Size**: `DIVIDE([Total Sales], DISTINCTCOUNT(FactSales[OrderID]))`
-   **YoY Sales Growth**: Comparing current period to the same period last year.

### Inventory & Variance
-   **Theoretical Usage**: Calculated based on Recipe BOM vs. Sales Quantity.
-   **Actual Usage**: Calculated from `StockTransaction` (Deductions + Waste).
-   **Variance %**: `DIVIDE([Actual Usage] - [Theoretical Usage], [Theoretical Usage], 0)`
-   **Waste Rate**: `DIVIDE([Total Waste Volume], [Total Sales Volume], 0)`

---

## 🖼️ 3. Analysis Reports & KPIs

### Page 1: Executive Sales Dashboard
*   **KPIs**: Gross Revenue, Net Profit Margin, Customer Count.
*   **Visual 1 (Line Chart)**: 90-Day Sales Trend (Weekly/Daily).
*   **Visual 2 (Donut Chart)**: Revenue share by Pizza Category (Small, Medium, Large).
*   **Visual 3 (Heatmap)**: Peak Sales Hours (Identifying when to staff more cashiers).

### Page 2: Inventory & Waste Intelligence
*   **KPIs**: Inventory Turnover Ratio, Total Spoilage Cost.
*   **Visual 1 (Bar Chart)**: Top 5 most wasted ingredients.
*   **Visual 2 (Gauge)**: Ingredients below threshold (Real-time alert).
*   **Visual 3 (Scatter Plot)**: Variance % vs. Total Usage per ingredient.

### Page 3: Operational Performance
*   **KPIs**: Avg Preparation Time, Multi-Order Processing Rate.
*   **Visual 1 (Table)**: Cashier Performance League Table (Sales vs. Errors).
*   **Visual 2 (Treemap)**: Product popularity vs. Profitability.

---

## 🏁 4. Implementation Checklist
- [x] **Data Seeding**: Fixed historical data generator for 90-day trends.
- [x] **Relational Schema**: Verified Foreign Key relationships for Star Schema.
- [ ] **CSV Export Engine**: Create Django admin action to batch export analytical data.
- [ ] **Power BI Connection**: Import CSVs and establish relationships.
- [ ] **DAX Development**: Finalize logic for "Waste-to-Sales" correlation.
- [ ] **Visual Polish**: Apply FJC Pizza brand colors and dark-mode styling.

---

## 🛠️ Step-by-Step Power BI Setup
1.  **Extract**: Run the CSV Export tool in the Django app.
    - *Note: If you are having database connection issues, run `python create_mock_bi_data.py` to generate sample data instantly for testing.*
2.  **Transform**: Use `Power Query` to ensure consistency.
3.  **Model**: Link `FactSales[ProductID]` to `DimProducts[ID]` and `FactSales[Date]` to `DimCalendar[Date]`.
4.  **Analyze**: Create a new measure group and input the DAX formulas provided in Section 2.
5.  **Visualize**: Follow the steps in `POWER_BI_VISUALIZATION_STEP_BY_STEP.md`.

---
*Last Updated: February 2026 | Project: FJC-Pizza Analytics*
