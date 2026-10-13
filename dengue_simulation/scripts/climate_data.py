import pandas as pd
import numpy as np
from meteostat import Point, Daily
from datetime import datetime, timedelta

# Load city population data
city_population_data = pd.read_csv('data/population/city_population_data.csv')

# Prepare a list to store temperature data
temperature_data_list = []

# Define the date range for historical data
start = datetime(2023, 1, 1)
end = datetime(2023, 12, 31)

# Define mean daily temperatures for each country with a simple seasonal pattern
def generate_seasonal_temperatures(mean_temp, amplitude=10):
    days = np.arange(1, 366)
    return mean_temp + amplitude * np.sin(2 * np.pi * (days - 80) / 365)

country_seasonal_temperatures = {
    'Albania': generate_seasonal_temperatures(15.5),
    'Andorra': generate_seasonal_temperatures(9.7),
    'Austria': generate_seasonal_temperatures(8.6),
    'Belgium': generate_seasonal_temperatures(10.3),
    'Bosnia and Herzegovina': generate_seasonal_temperatures(11.5),
    'Bulgaria': generate_seasonal_temperatures(11.3),
    'Croatia': generate_seasonal_temperatures(12.5),
    'Cyprus': generate_seasonal_temperatures(19.5),
    'Czech Republic': generate_seasonal_temperatures(8.0),
    'Denmark': generate_seasonal_temperatures(8.3),
    'Estonia': generate_seasonal_temperatures(6.1),
    'Finland': generate_seasonal_temperatures(5.1),
    'France': generate_seasonal_temperatures(12.1),
    'Germany': generate_seasonal_temperatures(9.5),
    'Greece': generate_seasonal_temperatures(16.4),
    'Hungary': generate_seasonal_temperatures(10.9),
    'Iceland': generate_seasonal_temperatures(3.3),
    'Ireland': generate_seasonal_temperatures(9.8),
    'Italy': generate_seasonal_temperatures(13.7),
    'Kosovo': generate_seasonal_temperatures(9.8),
    'Latvia': generate_seasonal_temperatures(6.2),
    'Liechtenstein': generate_seasonal_temperatures(7.5),
    'Lithuania': generate_seasonal_temperatures(6.2),
    'Luxembourg': generate_seasonal_temperatures(8.8),
    'Malta': generate_seasonal_temperatures(18.8),
    'Moldova': generate_seasonal_temperatures(9.6),
    'Monaco': generate_seasonal_temperatures(16.1),
    'Montenegro': generate_seasonal_temperatures(11.4),
    'Netherlands': generate_seasonal_temperatures(10.1),
    'North Macedonia': generate_seasonal_temperatures(11.3),
    'Norway': generate_seasonal_temperatures(6.3),
    'Poland': generate_seasonal_temperatures(7.6),
    'Portugal': generate_seasonal_temperatures(15.0),
    'Romania': generate_seasonal_temperatures(10.4),
    'San Marino': generate_seasonal_temperatures(12.4),
    'Serbia': generate_seasonal_temperatures(11.0),
    'Slovakia': generate_seasonal_temperatures(9.2),
    'Slovenia': generate_seasonal_temperatures(10.5),
    'Spain': generate_seasonal_temperatures(14.1),
    'Sweden': generate_seasonal_temperatures(6.7),
    'Switzerland': generate_seasonal_temperatures(8.5),
    'Turkey': generate_seasonal_temperatures(12.9),
    'United Kingdom': generate_seasonal_temperatures(10.8),
    'Vatican City': generate_seasonal_temperatures(15.5)
}

# Function to fetch temperature data for a given location
def fetch_temperature_data(lat, lng, start, end):
    location = Point(lat, lng)
    data = Daily(location, start, end)
    try:
        print(f"Fetching data for location: {city}")
        return data.fetch()
    except Exception as e:
        print(f"Error fetching data for location: {lat}, {lng} - {e}")
        return pd.DataFrame()

# Iterate over each city to fetch temperature data
for index, row in city_population_data.iterrows():
    city = row['city']
    country = row['country']
    lat = row['lat']
    lng = row['lng']
    
    # Fetch daily temperature data for the location
    data = fetch_temperature_data(lat, lng, start, end)
    if data.empty:
        # Use the seasonal temperatures for the country if city data is unavailable
        print(f"No temperature data found for city: {city}. Using seasonal data for country: {country}")
        seasonal_temps = country_seasonal_temperatures.get(country)
        if seasonal_temps is not None:
            date_range = pd.date_range(start, periods=365)
            data = pd.DataFrame({
                'time': date_range,
                'tavg': seasonal_temps,
                'city': [city] * 365,
                'country': [country] * 365
            })
        else:
            print(f"No temperature data found for country: {country}")
            continue

    # Add city and country information to the data
    data['city'] = city
    data['country'] = country
    
    # Append the data to the list
    temperature_data_list.append(data)

# Concatenate all the data into a single DataFrame
if temperature_data_list:
    temperature_data = pd.concat(temperature_data_list)
    # Reset index for the final DataFrame
    temperature_data.reset_index(inplace=True)

    # Save the temperature data to a CSV file
    temperature_data.to_csv('data/climate/city_temperature_data.csv', index=False)
    print("Temperature data fetching complete.")
else:
    print("No temperature data was fetched.")
