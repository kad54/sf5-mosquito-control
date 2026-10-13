import pandas as pd
import numpy as np
import os
from geopy.distance import geodesic
from joblib import Parallel, delayed
import time

def calculate_distance(lat1, lon1, lat2, lon2):
    return geodesic((lat1, lon1), (lat2, lon2)).kilometers

def compute_distances(city_data, output_file='city_distances.csv', num_biggest_cities=1000):
    start_time = time.time()
    
    # Sort the city data by population and select the top num_biggest_cities
    biggest_cities = city_data.nlargest(num_biggest_cities, 'population')
    print(f"Selected {num_biggest_cities} biggest cities for distance calculation.")

    # Function to calculate and store distance
    def calculate_and_store_distance(city1, city2):
        if city1['city'] != city2['city']:
            distance = calculate_distance(city1['lat'], city1['lng'], city2['lat'], city2['lng'])
            return {'city1': city1['city'], 'city2': city2['city'], 'distance': distance}
        return None

    # Precompute distances between all city pairs using parallel processing
    distances = []
    for idx, city1 in biggest_cities.iterrows():
        print(f"Calculating distances for {city1['city']} ({idx+1}/{len(biggest_cities)})...")
        city_distances = Parallel(n_jobs=-1)(
            delayed(calculate_and_store_distance)(city1, city2) 
            for jdx, city2 in biggest_cities.iterrows() 
            if idx != jdx
        )
        distances.extend([d for d in city_distances if d is not None])

    # Save distances to a file
    df_distances = pd.DataFrame(distances)
    df_distances.to_csv(output_file, index=False)
    
    end_time = time.time()
    print(f"Distances saved to {output_file}.")
    print(f"Time taken: {end_time - start_time:.2f} seconds.")

# Example usage
# Load city data (assuming a DataFrame with 'city', 'lat', 'lng', and 'population' columns)
city_data = pd.read_csv('data/population/city_population_data.csv')
compute_distances(city_data, num_biggest_cities=1000)

# The 'city_data' DataFrame should be loaded with your actual data.
