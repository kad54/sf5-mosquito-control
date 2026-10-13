import pandas as pd

# Load the world cities dataset
world_cities = pd.read_csv('worldcities.csv')

# List of European countries (can be customized as needed)
european_countries = [
    'Albania', 'Andorra', 'Austria', 'Belgium', 'Bosnia and Herzegovina',
    'Bulgaria', 'Croatia', 'Cyprus', 'Czech Republic', 'Denmark', 'Estonia', 'Finland', 'France', 
    'Germany', 'Greece', 'Hungary', 'Iceland', 'Ireland', 'Italy', 'Kosovo', 'Latvia', 'Liechtenstein',
    'Lithuania', 'Luxembourg', 'Malta', 'Moldova', 'Monaco', 'Montenegro', 'Netherlands', 'North Macedonia', 'Norway',
    'Poland', 'Portugal', 'Romania', 'San Marino', 'Serbia', 'Slovakia', 'Slovenia', 'Spain', 'Sweden',
    'Switzerland', 'Turkey', 'United Kingdom', 'Vatican City'
]

# Filter the dataset to include only European countries
european_cities = world_cities[world_cities['country'].isin(european_countries)]

# Select relevant columns
european_cities = european_cities[['city', 'country', 'population', 'lat', 'lng']]

# Save the filtered data to a CSV file
european_cities.to_csv('data/population/city_population_data.csv', index=False)

european_cities.head()
