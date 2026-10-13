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

    return sum(R.values())

# Parameters
gamma = 0.1  # Recovery rate
initial_infected = ['Istanbul', 'Berlin']
lambda_values = np.linspace(0.1, 1.0, 10)  # Range of lambda values
num_simulations = 100  # Number of simulations for averaging

# Run simulations for a range of lambda values and calculate R
R_values = []

for beta in lambda_values:
    total_R = 0
    for _ in range(num_simulations):
        total_R += SIR_simulation(G, initial_infected, beta, gamma)
    average_R = total_R / num_simulations
    R_values.append(round(average_R))

# Plot results
plt.figure(figsize=(10, 6))
plt.plot(lambda_values, R_values, marker='o')
plt.xlabel('Transmission Rate (λ)')
plt.ylabel('Number of Recovered Cities (R)')
plt.title('Number of Recovered Cities vs Transmission Rate')
plt.grid(True)
plt.show()

# Iterative solution for si
def calculate_si(G, beta, tol=1e-6, max_iter=1000):
    nodes = list(G.nodes)
    N = len(nodes)
    s = np.random.rand(N)
    node_index = {node: idx for idx, node in enumerate(nodes)}
    
    A = nx.to_numpy_array(G, nodelist=nodes)
    
    for iteration in range(max_iter):
        s_new = np.ones(N)
        for i, node in enumerate(nodes):
            neighbors = list(G.neighbors(node))
            neighbor_indices = [node_index[neighbor] for neighbor in neighbors]
            s_new[i] = np.prod([1 - beta + s[j] * beta for j in neighbor_indices])

        if np.linalg.norm(s_new - s) < tol:
            print(f'Converged after {iteration} iterations')
            break
        s = s_new
    
    return s

# Calculate si for a range of lambda values
si_values = []

for beta in lambda_values:
    s = calculate_si(G, beta)
    si_values.append(s)

# Compare predictions to simulations
predicted_R_values = [len(G.nodes) - sum(si) for si in si_values]

plt.figure(figsize=(10, 6))
plt.plot(lambda_values, R_values, label='Simulated R', marker='o')
plt.plot(lambda_values, predicted_R_values, label='Predicted R', marker='x')
plt.xlabel('Transmission Rate (λ)')
plt.ylabel('Number of Recovered Cities (R)')
plt.title('Comparison of Simulated and Predicted R Values')
plt.legend()
plt.grid(True)
plt.show()

# Eigenvalue analysis for stability
A = nx.to_numpy_array(G)
eigenvalues = np.linalg.eigvals(A)
lambda_c = 1 / max(eigenvalues)
print(f'Estimated epidemic threshold λ: {lambda_c:.4f}')
