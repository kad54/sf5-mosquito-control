import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import random

# Load data
print("Loading data...")
city_population_data = pd.read_csv('data/population/city_population_data.csv')
city_distances = pd.read_csv('data/city_distances.csv')
city_temperature_data = pd.read_csv('data/climate/city_temperature_data.csv')

# Print head of each dataframe to verify correct loading
print("City Population Data:")
print(city_population_data.head())

print("City Distances Data:")
print(city_distances.head())

print("City Temperature Data:")
print(city_temperature_data.head())

# Inspect the date format
print("Original date values:")
print(city_temperature_data['index'].head())

# Adjust date parsing logic
print("Parsing dates in climate data...")
try:
    city_temperature_data['datetime'] = pd.to_datetime(city_temperature_data['index'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
    city_temperature_data = city_temperature_data.dropna(subset=['datetime'])
    print("Parsed climate data:")
    print(city_temperature_data.head())
except Exception as e:
    print(f"Error parsing dates: {e}")

# Calculate average temperature for each city
print("Calculating average temperatures for each city...")
try:
    avg_temperatures = city_temperature_data.groupby('city')['tavg'].mean().to_dict()
    print("Average temperatures:")
    print(avg_temperatures)
except Exception as e:
    print(f"Error calculating average temperatures: {e}")

# Create graph
G = nx.Graph()

# Add nodes with population data
print("Adding nodes to the graph...")
for _, row in city_population_data.iterrows():
    G.add_node(row['city'], population=row['population'], country=row['country'], lat=row['lat'], lng=row['lng'])
print("Nodes added:", len(G.nodes))

# Add edges based on distance threshold
print("Adding edges to the graph...")
distance_threshold = 100  # You can adjust this threshold
for _, row in city_distances.iterrows():
    if row['distance'] <= distance_threshold:
        G.add_edge(row['city1'], row['city2'], weight=row['distance'])
print("Edges added:", len(G.edges))

# Define a function to determine transmission probability based on temperature
def transmission_probability(temp):
    try:
        min_temp = min(avg_temperatures.values())
        max_temp = max(avg_temperatures.values())
        return 0.1 + (temp - min_temp) / (max_temp - min_temp) * 0.4
    except ValueError:
        return 0.1  # default value if there's an error

# Assign transmission probabilities to each city
print("Assigning transmission probabilities...")
for city in G.nodes:
    temp = avg_temperatures.get(city, 0)  # Default to 0 if temperature data is missing
    G.nodes[city]['lambda'] = transmission_probability(temp)
print("Transmission probabilities assigned.")

def SIR_simulation(G, initial_infected, beta, gamma):
    S = {node: True for node in G.nodes}
    I = {node: False for node in G.nodes}
    R = {node: False for node in G.nodes}

    for node in initial_infected:
        S[node] = False
        I[node] = True

    S_values, I_values, R_values = [], [], []

    time_step = 0
    while any(I.values()):
        new_I = []
        for node in list(I.keys()):
            if I[node]:
                for neighbor in G.neighbors(node):
                    if S[neighbor] and random.random() < beta * G.nodes[neighbor]['lambda']:
                        new_I.append(neighbor)
                R[node] = True
                I[node] = False

        for node in new_I:
            S[node] = False
            I[node] = True

        S_values.append(sum(S.values()))
        I_values.append(sum(I.values()))
        R_values.append(sum(R.values()))

        time_step += 1

    return S, I, R, S_values, I_values, R_values

# Example initial infected cities
initial_infected = ['Istanbul', 'Berlin']

# Example parameters
beta_values = [0.2, 0.4, 0.6]  # Different values of beta (λ)
gamma = 0.1  # Recovery rate

# Number of simulations to average
num_simulations = 10

# Run the simulation for different beta values and plot averaged results
plt.figure(figsize=(12, 8))
for beta in beta_values:
    print(f"Running simulation for beta={beta}...")
    
    all_S_values = []
    all_I_values = []
    all_R_values = []
    
    for _ in range(num_simulations):
        S, I, R, S_values, I_values, R_values = SIR_simulation(G, initial_infected, beta, gamma)
        all_S_values.append(S_values)
        all_I_values.append(I_values)
        all_R_values.append(R_values)
    
    # Pad lists with zeros to the maximum length of the time series
    max_len = max(map(len, all_S_values))
    all_S_values = [s + [s[-1]] * (max_len - len(s)) for s in all_S_values]
    all_I_values = [i + [i[-1]] * (max_len - len(i)) for i in all_I_values]
    all_R_values = [r + [r[-1]] * (max_len - len(r)) for r in all_R_values]
    
    # Calculate the average values
    avg_S_values = np.mean(all_S_values, axis=0)
    avg_I_values = np.mean(all_I_values, axis=0)
    avg_R_values = np.mean(all_R_values, axis=0)
    
    plt.plot(avg_S_values, label=f'Susceptible (λ={beta})')
    plt.plot(avg_I_values, label=f'Infected (λ={beta})')
    plt.plot(avg_R_values, label=f'Recovered (λ={beta})')
    
    print(f"Final averaged SIR values for beta={beta}:")
    print(f"Overall Susceptible: {avg_S_values[-1]}")
    print(f"Overall Infected: {avg_I_values[-1]}")
    print(f"Overall Recovered: {avg_R_values[-1]}")

plt.xlabel('Time')
plt.ylabel('Number of Cities')
plt.legend()
plt.title('SIR Model Simulation for Different Transmission Probabilities (λ)')
plt.show()
