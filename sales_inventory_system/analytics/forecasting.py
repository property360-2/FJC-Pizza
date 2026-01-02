"""
Sales Forecasting using Holt-Winters Exponential Smoothing (ETS)
Enhanced with automatic model selection and outlier handling
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum
from django.db.models.functions import TruncDate
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sales_inventory_system.orders.models import Payment
from decimal import Decimal
from scipy import stats


def detect_outliers_iqr(data, multiplier=1.5):
    """
    Detect outliers using the Interquartile Range (IQR) method

    Args:
        data: pandas.Series of values
        multiplier: IQR multiplier (default 1.5 for moderate outlier detection)

    Returns:
        pandas.Series: Boolean mask where True indicates outliers
    """
    if len(data) < 4:
        return pd.Series([False] * len(data), index=data.index)

    Q1 = data.quantile(0.25)
    Q3 = data.quantile(0.75)
    IQR = Q3 - Q1

    lower_bound = Q1 - multiplier * IQR
    upper_bound = Q3 + multiplier * IQR

    return (data < lower_bound) | (data > upper_bound)


def clean_sales_data(data):
    """
    Clean sales data by handling outliers and filling missing values

    Args:
        data: pandas.Series of sales data

    Returns:
        pandas.Series: Cleaned data
    """
    if len(data) < 7:
        return data

    cleaned = data.copy()

    # Detect outliers using a more lenient threshold
    outliers = detect_outliers_iqr(cleaned, multiplier=2.5)

    # Replace outliers with rolling median instead of interpolation
    if outliers.sum() > 0:
        rolling_median = cleaned.rolling(window=7, center=True, min_periods=1).median()
        cleaned[outliers] = rolling_median[outliers]

    # Fill any remaining NaN values with rolling median
    if cleaned.isna().sum() > 0:
        cleaned = cleaned.fillna(cleaned.rolling(window=7, center=True, min_periods=1).median())

    # Final fallback to overall median
    if cleaned.isna().sum() > 0:
        cleaned = cleaned.fillna(cleaned.median())

    # Ensure no negative values
    cleaned = cleaned.clip(lower=0)

    # Apply light smoothing to reduce noise (exponential moving average)
    # This helps the model find patterns in noisy data
    smoothed = cleaned.ewm(span=3, adjust=False).mean()

    return smoothed


def prepare_sales_data(days=60):
    """
    Prepare historical sales data for forecasting with improved data quality

    Args:
        days: Number of days of historical data to use (default 60 for better patterns)

    Returns:
        pandas.Series: Time series of daily revenue (cleaned)
    """
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)

    # Get daily revenue data using optimized query
    daily_payments = Payment.objects.filter(
        status='SUCCESS',
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).values('created_at__date').annotate(
        total=Sum('amount')
    ).order_by('created_at__date')

    # Create complete date range
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')

    # Build dictionary from query results
    revenue_dict = {
        item['created_at__date']: float(item['total'] or 0)
        for item in daily_payments
    }

    # Create time series with all dates (fill missing dates with 0)
    sales_data = [revenue_dict.get(date.date(), 0.0) for date in date_range]
    ts = pd.Series(sales_data, index=date_range)

    # Clean the data (handle outliers)
    ts_cleaned = clean_sales_data(ts)

    return ts_cleaned


def select_best_model(historical_data, seasonal_periods=7):
    """
    Automatically select the best Holt-Winters model configuration
    using cross-validation for better out-of-sample accuracy

    Args:
        historical_data: pandas.Series of historical sales data
        seasonal_periods: Length of seasonal cycle

    Returns:
        tuple: (best_model, model_params)
    """
    # Check if we have enough data for seasonal model
    min_data_points = seasonal_periods * 2

    if len(historical_data) < min_data_points:
        # Not enough data for seasonality
        return None, {'trend': 'add', 'seasonal': None, 'reason': 'insufficient_data'}

    # Test different model configurations
    models_to_test = []

    # Check if data has variance for multiplicative models
    min_value = historical_data.min()
    has_zeros = (historical_data == 0).any()
    has_low_values = min_value < 1

    # Additive models (work with zeros and low values)
    models_to_test.append({
        'trend': 'add',
        'seasonal': 'add',
        'seasonal_periods': seasonal_periods,
        'damped_trend': False
    })

    models_to_test.append({
        'trend': 'add',
        'seasonal': 'add',
        'seasonal_periods': seasonal_periods,
        'damped_trend': True
    })

    # No trend models (good for stable businesses)
    models_to_test.append({
        'trend': None,
        'seasonal': 'add',
        'seasonal_periods': seasonal_periods,
        'damped_trend': False
    })

    # Multiplicative seasonal if no zeros/low values
    if not has_zeros and not has_low_values:
        models_to_test.append({
            'trend': 'add',
            'seasonal': 'mul',
            'seasonal_periods': seasonal_periods,
            'damped_trend': False
        })

        models_to_test.append({
            'trend': 'add',
            'seasonal': 'mul',
            'seasonal_periods': seasonal_periods,
            'damped_trend': True
        })

    # Use cross-validation to select best model (hold out last 7 days)
    train_data = historical_data[:-7]
    test_data = historical_data[-7:]

    best_mape = float('inf')
    best_config = models_to_test[0]
    best_aic = float('inf')

    for config in models_to_test:
        try:
            model = ExponentialSmoothing(
                train_data,
                trend=config['trend'],
                seasonal=config['seasonal'],
                seasonal_periods=config.get('seasonal_periods'),
                damped_trend=config.get('damped_trend', False),
                initialization_method='estimated'
            )
            fitted = model.fit(optimized=True, use_brute=True)

            # Forecast the test period
            forecast = fitted.forecast(steps=7)

            # Calculate MAPE on test set
            non_zero_mask = test_data != 0
            if non_zero_mask.sum() > 0:
                mape = np.mean(np.abs((test_data[non_zero_mask].values - forecast[non_zero_mask].values) / test_data[non_zero_mask].values)) * 100
            else:
                mape = float('inf')

            # Select based on test MAPE (out-of-sample performance)
            if mape < best_mape:
                best_mape = mape
                best_config = config
                best_aic = fitted.aic
        except Exception:
            continue

    return best_config, {'aic': best_aic, 'cv_mape': best_mape}


def forecast_sales_holt_winters(historical_data, forecast_periods=7, seasonal_periods=7):
    """
    Forecast sales using Holt-Winters Exponential Smoothing with automatic model selection

    Args:
        historical_data: pandas.Series of historical sales data
        forecast_periods: Number of periods to forecast
        seasonal_periods: Length of seasonal cycle (7 for weekly seasonality)

    Returns:
        dict: Contains forecast values, confidence intervals, and model info
    """
    try:
        # Ensure we have enough data points
        min_required = max(14, seasonal_periods * 2)
        if len(historical_data) < min_required:
            return {
                'success': False,
                'error': 'Insufficient data',
                'message': f'At least {min_required} days of historical data required. Currently have {len(historical_data)} days.'
            }

        # Automatically select best model configuration
        best_config, selection_info = select_best_model(historical_data, seasonal_periods)

        if best_config is None:
            # Fallback to simple exponential smoothing
            model = ExponentialSmoothing(
                historical_data,
                trend='add',
                seasonal=None,
                initialization_method='estimated'
            )
            model_type = 'Simple Exponential Smoothing (Trend Only)'
        else:
            model = ExponentialSmoothing(
                historical_data,
                trend=best_config['trend'],
                seasonal=best_config['seasonal'],
                seasonal_periods=best_config.get('seasonal_periods'),
                damped_trend=best_config.get('damped_trend', False),
                initialization_method='estimated'
            )

            # Build model type description
            seasonal_type = best_config['seasonal']
            if seasonal_type:
                seasonal_str = 'Multiplicative' if seasonal_type == 'mul' else 'Additive'
                damped_str = ' (Damped)' if best_config.get('damped_trend') else ''
                model_type = f'Holt-Winters {seasonal_str} Seasonal{damped_str}'
            else:
                model_type = 'Holt-Winters (Trend Only)'

        # Fit the model with optimization (use_brute=True for better parameter search)
        fitted_model = model.fit(optimized=True, use_brute=True)

        # Generate forecast with prediction intervals
        forecast_result = fitted_model.forecast(steps=forecast_periods)

        # Get simulation-based prediction intervals for better accuracy
        # Use the model to simulate multiple paths
        simulations = fitted_model.simulate(
            nsimulations=forecast_periods,
            repetitions=1000,
            error='add'
        )

        # Calculate prediction intervals from simulations
        lower_bound = np.percentile(simulations, 2.5, axis=1)
        upper_bound = np.percentile(simulations, 97.5, axis=1)

        # Calculate fitted values (for plotting historical fit)
        fitted_values = fitted_model.fittedvalues

        # Calculate residuals and error metrics
        residuals = historical_data - fitted_values
        mse = float(np.mean(residuals**2))
        mae = float(np.mean(np.abs(residuals)))
        rmse = float(np.sqrt(mse))

        # Calculate MAPE (Mean Absolute Percentage Error) - avoiding division by zero
        non_zero_actuals = historical_data[historical_data != 0]
        non_zero_fitted = fitted_values[historical_data != 0]
        if len(non_zero_actuals) > 0:
            mape = float(np.mean(np.abs((non_zero_actuals - non_zero_fitted) / non_zero_actuals)) * 100)
        else:
            mape = 0.0

        # Calculate percentage versions of MAE and RMSE
        mean_actual = float(historical_data.mean())
        if mean_actual > 0:
            mae_pct = (mae / mean_actual) * 100
            rmse_pct = (rmse / mean_actual) * 100
        else:
            mae_pct = 0.0
            rmse_pct = 0.0

        # Forecast dates
        forecast_dates = pd.date_range(
            start=historical_data.index[-1] + timedelta(days=1),
            periods=forecast_periods,
            freq='D'
        )

        # Prepare confidence intervals
        confidence_intervals = []
        for i in range(forecast_periods):
            confidence_intervals.append({
                'date': forecast_dates[i].strftime('%Y-%m-%d'),
                'lower': max(0, float(lower_bound[i])),  # Revenue can't be negative
                'upper': float(upper_bound[i])
            })

        # Prepare forecast data
        forecast_data = []
        for i, value in enumerate(forecast_result):
            forecast_data.append({
                'date': forecast_dates[i].strftime('%Y-%m-%d'),
                'value': max(0, float(value)),  # Revenue can't be negative
                'day_name': forecast_dates[i].strftime('%A')
            })

        # Prepare historical data for return
        historical_list = []
        for date, value in historical_data.items():
            historical_list.append({
                'date': date.strftime('%Y-%m-%d'),
                'value': float(value),
                'day_name': date.strftime('%A')
            })

        # Model statistics with accuracy grade
        accuracy_grade = 'Excellent' if mape < 10 else 'Good' if mape < 20 else 'Fair' if mape < 30 else 'Poor'

        statistics = {
            'aic': float(fitted_model.aic),
            'bic': float(fitted_model.bic),
            'mse': mse,
            'mae': mae,
            'rmse': rmse,
            'mae_pct': mae_pct,
            'rmse_pct': rmse_pct,
            'mape': mape,
            'accuracy_grade': accuracy_grade
        }

        return {
            'success': True,
            'forecast': forecast_data,
            'historical': historical_list,
            'confidence_intervals': confidence_intervals,
            'statistics': statistics,
            'model_type': model_type,
            'seasonal_periods': seasonal_periods if best_config and best_config['seasonal'] else None
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': 'Unable to generate forecast. This may be due to insufficient or irregular data.'
        }


def forecast_sales(days_back=60, days_ahead=7):
    """
    Main function to generate sales forecast with enhanced accuracy

    Args:
        days_back: Number of historical days to use (default 60 for better pattern detection)
        days_ahead: Number of days to forecast

    Returns:
        dict: Forecast results with confidence intervals and statistics
    """
    # Prepare data with cleaning
    historical_data = prepare_sales_data(days=days_back)

    # Check if we have any data
    if historical_data.sum() == 0:
        return {
            'success': False,
            'error': 'No historical sales data available',
            'message': 'Please ensure there are completed orders in the system.'
        }

    # Check for sufficient variation in data
    if historical_data.std() == 0:
        return {
            'success': False,
            'error': 'Insufficient data variation',
            'message': 'Historical sales data shows no variation. More diverse data is needed for forecasting.'
        }

    # Generate forecast
    forecast_result = forecast_sales_holt_winters(
        historical_data,
        forecast_periods=days_ahead,
        seasonal_periods=7  # Weekly seasonality (day of week effect)
    )

    if forecast_result['success']:
        # Add summary statistics
        forecast_values = [f['value'] for f in forecast_result['forecast']]
        historical_values = [h['value'] for h in forecast_result['historical']]

        # Calculate growth rate
        if len(historical_values) > 0:
            avg_historical = np.mean(historical_values)
            avg_forecast = np.mean(forecast_values)
            growth_rate = ((avg_forecast - avg_historical) / avg_historical * 100) if avg_historical > 0 else 0
        else:
            growth_rate = 0

        forecast_result['summary'] = {
            'historical_avg': float(np.mean(historical_values)),
            'historical_total': float(np.sum(historical_values)),
            'historical_min': float(np.min(historical_values)),
            'historical_max': float(np.max(historical_values)),
            'forecast_avg': float(np.mean(forecast_values)),
            'forecast_total': float(np.sum(forecast_values)),
            'forecast_min': float(np.min(forecast_values)),
            'forecast_max': float(np.max(forecast_values)),
            'growth_rate': float(growth_rate),
            'data_points_used': len(historical_values)
        }

    return forecast_result
