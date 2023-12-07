# -*- coding: utf-8 -*-
import dataiku
import pandas as pd, numpy as np
from datetime import date, datetime, timedelta
from dataiku import pandasutils as pdu
import holidays
from calendar import monthrange


# Create a list of holidays for Norway
norwegian_holidays = holidays.Norway()

# Define the start and end dates
start_date = date(2006, 1, 1)
end_date = date(2030, 12, 31)

# Initialize the cumulative days dictionary
cumulative_days = {}

# Create an empty DataFrame to store the calendar data
calendar = pd.DataFrame(columns=[
    'SYSTEM_DATE', 'START_OF_WEEK', 'END_OF_WEEK', 'START_OF_MONTH', 'END_OF_MONTH',
    'START_OF_QUARTER', 'END_OF_QUARTER', 'YEAR', 'MONTH', 'MONTH_NAME', 'RELATIVE_MONTH', 'DAY',
    'DAY_OF_WEEK', 'DAY_OF_YEAR', 'WEEK_OF_YEAR', 'QUARTER_OF_YEAR', 'RELATIVE_QUARTER', 'DAY_NAME', 'WEEKDAY_OR_WEEKEND_DAY_TYPE',
    'NORWEGIAN_HOLIDAY', 'DAYS_IN_MONTH', 'WEEKDAYS_PER_MONTH'
])

# Generate calendar data
current_date = start_date
while current_date <= end_date:
    year = current_date.year
    month = current_date.month
    quarter = (month - 1) // 3 + 1
    day_name = current_date.strftime('%A')
    day_of_week = current_date.isoweekday()
    day_of_year = (current_date - date(year, 1, 1)).days + 1
    week_of_year = current_date.strftime('%U')
    is_weekend = day_name in ['Saturday', 'Sunday']
    weekday_or_weekend = 'WEEKEND' if is_weekend else 'WEEKDAY'
    last_month_of_quarter = 3 * quarter
    relative_date = date.today()
    years_difference = year - date.today().year
    quarter_difference = (month - 1 ) // 3 - (date.today().month - 1) // 3
    relative_quarter = quarter_difference + 4 * years_difference
    month_difference = (month - 1 ) - (date.today().month - 1)
    relative_month = month_difference + 12 * years_difference
    year_month = f"{year}{str(month).zfill(2)}"
    year_week = f"{year}{str(week_of_year).zfill(2)}"

    # Check if the date is a Norwegian holiday
    is_norwegian_holiday = current_date in norwegian_holidays


    
    # Calculate the number of days for the current month considering leap years
    is_leap_year = (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0))
    days_in_month = 29 if is_leap_year and month == 2 else 28 if month == 2 else 31 if month in [1, 3, 5, 7, 8, 10, 12] else 30

    date_format = "%Y-%m-%d"

    calendar = calendar.append({
        'SYSTEM_DATE': pd.to_datetime(current_date),
        'START_OF_WEEK': pd.to_datetime(current_date - timedelta(days=(day_of_week - 1))),
        'END_OF_WEEK': pd.to_datetime(current_date + timedelta(days=(7 - day_of_week))),
        'START_OF_MONTH': pd.to_datetime(date(year, month, 1)),
        'END_OF_MONTH': pd.to_datetime(date(year, month, days_in_month)),
        'START_OF_QUARTER': pd.to_datetime(date(year, 3 * (quarter - 1) + 1, 1)),
        'END_OF_QUARTER': pd.to_datetime((current_date + pd.offsets.QuarterEnd()).date()),
        'YEAR': year,
        'MONTH': month,
        'YEAR_MONTH': year_month,
        'MONTH_NAME': current_date.strftime('%B'),
        'RELATIVE_MONTH': relative_month,
        'DAY': current_date.day,
        'DAY_OF_WEEK': day_of_week,
        'DAY_OF_YEAR': day_of_year,
        'WEEK_OF_YEAR': int(week_of_year),
        'YEAR_WEEK': year_week,
        'QUARTER_OF_YEAR': quarter,
        'RELATIVE_QUARTER': relative_quarter,
        'DAY_NAME': day_name,
        'WEEKDAY_OR_WEEKEND_DAY_TYPE': weekday_or_weekend,
        'NORWEGIAN_HOLIDAY': is_norwegian_holiday,
        'DAYS_IN_MONTH' : days_in_month,
        'WEEKDAYS_PER_MONTH': 0 
    }, ignore_index=True)

    current_date += timedelta(days=1)
    
# Create a new column 'WEEKDAYS_PER_MONTH' that counts weekdays per month
calendar['WEEKDAYS_PER_MONTH'] = calendar.groupby(['YEAR', 'MONTH'])['WEEKDAY_OR_WEEKEND_DAY_TYPE'].transform(lambda x: x.eq('WEEKDAY').sum())

# Convert 'WEEKDAYS_PER_MONTH' to integer
calendar['WEEKDAYS_PER_MONTH'] = calendar['WEEKDAYS_PER_MONTH'].astype(int)
calendar['NORWEGIAN_HOLIDAY'] = calendar['NORWEGIAN_HOLIDAY'].astype(int)

#Give the calendar a name
calendar_name = calendar

#START Added logic for holiday extension
#def check_holiday_extension(row):
#    if ((row['DAY'] >= 27 and row['DAY'] <= 31 and row['MONTH'] == 12) and row['WEEKDAY_OR_WEEKEND_DAY_TYPE'] == 'WEEKDAY'):
#        return 1  # Flag indicating an extended holiday period
#    return 0  # No extended holiday period

def find_first_norwegian_holiday(year):
    norwegian_holidays_in_year = calendar[(calendar['NORWEGIAN_HOLIDAY']) & (calendar['YEAR'] == year) & (calendar['MONTH'] > 2)]
    if not norwegian_holidays_in_year.empty:
        return norwegian_holidays_in_year['SYSTEM_DATE'].min()
    else:
        return pd.NaT  #Return a null value if there are no Norwegian holidays in the specified year

# Apply the function to the DataFrame
calendar_name['FIRST_HOLIDAY_DATE'] = calendar_name['YEAR'].apply(find_first_norwegian_holiday)

def combined_holiday_flags(row):
    if ((row['DAY'] >= 27 and row['DAY'] <= 31 and row['MONTH'] == 12) and row['WEEKDAY_OR_WEEKEND_DAY_TYPE'] == 'WEEKDAY'):
        return 1  # Flag indicating an extended holiday period
    
    if not pd.isnull(row['FIRST_HOLIDAY_DATE']):
        diff = (row['FIRST_HOLIDAY_DATE'] - row['SYSTEM_DATE']).days
        if 0 < diff <= 3:
            return 1  # Flag indicating an extended holiday period

    return 0  # No extended holiday period

# Apply the combined function to create the new column
calendar_name['HOLIDAY_NO_EXTENDED_PERIOD_FLAG'] = calendar_name.apply(combined_holiday_flags, axis=1)

#TO DO - Write the dataframe calendar_name to a location of your choice


