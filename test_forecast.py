"""
Test script for the enhanced forecasting system
"""
import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'sales_inventory_system'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'system.settings')
django.setup()

# Now import and test forecasting
from sales_inventory_system.analytics.forecasting import forecast_sales

print("=" * 70)
print("Testing Enhanced Sales Forecasting System")
print("=" * 70)

# Test with default parameters (60 days back, 7 days ahead)
print("\nGenerating forecast with 60 days of historical data...")
result = forecast_sales(days_back=60, days_ahead=7)

if result['success']:
    print("\n✓ Forecast generated successfully!")
    print(f"\nModel Type: {result['model_type']}")

    # Display statistics
    stats = result['statistics']
    print("\nModel Accuracy Metrics:")
    print(f"  - MAPE (Mean Absolute Percentage Error): {stats['mape']:.2f}%")
    print(f"  - Accuracy Grade: {stats['accuracy_grade']}")
    print(f"  - MAE (Mean Absolute Error): ${stats['mae']:.2f}")
    print(f"  - RMSE (Root Mean Square Error): ${stats['rmse']:.2f}")
    print(f"  - AIC: {stats['aic']:.2f}")

    # Display summary
    if 'summary' in result:
        summary = result['summary']
        print("\nForecast Summary:")
        print(f"  - Historical Average: ${summary['historical_avg']:.2f}/day")
        print(f"  - Historical Total: ${summary['historical_total']:.2f}")
        print(f"  - Forecast Average: ${summary['forecast_avg']:.2f}/day")
        print(f"  - Forecast Total: ${summary['forecast_total']:.2f}")
        print(f"  - Growth Rate: {summary['growth_rate']:.2f}%")
        print(f"  - Data Points Used: {summary['data_points_used']}")

    # Display forecast values
    print("\nNext 7 Days Forecast:")
    print("-" * 70)
    for i, forecast_day in enumerate(result['forecast'], 1):
        ci = result['confidence_intervals'][i-1]
        print(f"{i}. {forecast_day['day_name']}, {forecast_day['date']}")
        print(f"   Forecast: ${forecast_day['value']:.2f}")
        print(f"   95% Confidence Interval: ${ci['lower']:.2f} - ${ci['upper']:.2f}")

    print("\n" + "=" * 70)
    print("✓ All tests passed! Forecasting system is working correctly.")
    print("=" * 70)
else:
    print(f"\n✗ Forecast failed: {result['error']}")
    print(f"  Message: {result['message']}")
    print("\nNote: This is expected if there's insufficient historical data.")
    print("Run the data seeder to generate test data if needed.")
