import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sns
import random
from mpl_toolkits.basemap import Basemap

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

# Adjust date parsing logic
print("Parsing dates in climate data...")
city_temperature_data['datetime'] = pd.to_datetime(city_temperature_data['index'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
city_temperature_data = city_temperature_data.dropna(subset=['datetime'])
print("Parsed climate data:")
print(city_temperature_data.head())

# Calculate average temperature for each city
print("Calculating average temperatures for each city...")
avg_temperatures = city_temperature_data.groupby('city')['tavg'].mean().to_dict()
print("Average temperatures:")
print(avg_temperatures)

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
        if node in G.nodes:
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

    final_S = sum(S.values())
    final_I = sum(I.values())
    final_R = sum(R.values())
    
    return final_S, final_I, final_R, S_values, I_values, R_values

# Define an improved mosquito removal strategy based on multiple centrality measures
def combined_centrality_removal_strategy(G, num_to_remove):
    # Calculate centrality measures for each node
    degree_centrality = nx.degree_centrality(G)
    betweenness_centrality = nx.betweenness_centrality(G)
    closeness_centrality = nx.closeness_centrality(G)
    eigenvector_centrality = nx.eigenvector_centrality(G)
    
    # Normalize centrality measures
    max_degree = max(degree_centrality.values())
    max_betweenness = max(betweenness_centrality.values())
    max_closeness = max(closeness_centrality.values())
    max_eigenvector = max(eigenvector_centrality.values())
    
    for node in G.nodes:
        degree_centrality[node] /= max_degree
        betweenness_centrality[node] /= max_betweenness
        closeness_centrality[node] /= max_closeness
        eigenvector_centrality[node] /= max_eigenvector
    
    # Calculate combined centrality score
    combined_centrality = {}
    for node in G.nodes:
        combined_centrality[node] = (degree_centrality[node] +
                                     betweenness_centrality[node] +
                                     closeness_centrality[node] +
                                     eigenvector_centrality[node]) / 4
    
    # Sort cities by combined centrality score
    prioritized_cities = sorted(combined_centrality.items(), key=lambda x: x[1], reverse=True)
    
    # Remove top 'num_to_remove' cities based on combined centrality score
    removed_cities = [city for city, _ in prioritized_cities[:num_to_remove]]
    for city in removed_cities:
        if city in G:
            G.remove_node(city)
            print(f"Removed city: {city}")
        else:
            print(f"City {city} not found in the graph and cannot be removed.")
        
    print("Cities removed for mosquito control.")
    return removed_cities

# Randomly select 200 cities to be initially infected
initial_infected = random.sample(list(G.nodes), 200)

# Example parameters
beta_values = [0.2, 0.4, 0.6]  # Different values of beta (λ)
gamma = 0.1  # Recovery rate

# Number of simulations to average
num_simulations = 1

# Number of cities to remove for mosquito control
num_to_remove = 5

# Run the simulation before removing any cities
print("Running simulation before removing cities...")
final_results_before = []

for beta in beta_values:
    all_S_values_before = []
    all_I_values_before = []
    all_R_values_before = []
    
    for _ in range(num_simulations):
        final_S, final_I, final_R, S_values, I_values, R_values = SIR_simulation(G, initial_infected, beta, gamma)
        all_S_values_before.append(S_values)
        all_I_values_before.append(I_values)
        all_R_values_before.append(R_values)
    
    max_len = max(map(len, all_S_values_before))
    all_S_values_before = [s + [s[-1]] * (max_len - len(s)) for s in all_S_values_before]
    all_I_values_before = [i + [i[-1]] * (max_len - len(i)) for i in all_I_values_before]
    all_R_values_before = [r + [r[-1]] * (max_len - len(r)) for r in all_R_values_before]
    
    avg_S_values_before = np.mean(all_S_values_before, axis=0)
    avg_I_values_before = np.mean(all_I_values_before, axis=0)
    avg_R_values_before = np.mean(all_R_values_before, axis=0)
    
    final_results_before.append((beta, final_S, final_I, final_R, avg_S_values_before, avg_I_values_before, avg_R_values_before))

# Apply improved mosquito removal strategy
removed_cities = combined_centrality_removal_strategy(G, num_to_remove)

# Update initial infected list by removing those that have been removed from the graph
initial_infected = [city for city in initial_infected if city in G.nodes]

# Run the simulation after removing cities with improved strategy
print("Running simulation after removing cities with improved strategy...")
final_results_after_improved = []

for beta in beta_values:
    all_S_values_after = []
    all_I_values_after = []
    all_R_values_after = []
    
    for _ in range(num_simulations):
        final_S, final_I, final_R, S_values, I_values, R_values = SIR_simulation(G, initial_infected, beta, gamma)
        all_S_values_after.append(S_values)
        all_I_values_after.append(I_values)
        all_R_values_after.append(R_values)
    
    max_len = max(map(len, all_S_values_after))
    all_S_values_after = [s + [s[-1]] * (max_len - len(s)) for s in all_S_values_after]
    all_I_values_after = [i + [i[-1]] * (max_len - len(i)) for i in all_I_values_after]
    all_R_values_after = [r + [r[-1]] * (max_len - len(r)) for r in all_R_values_after]
    
    avg_S_values_after = np.mean(all_S_values_after, axis=0)
    avg_I_values_after = np.mean(all_I_values_after, axis=0)
    avg_R_values_after = np.mean(all_R_values_after, axis=0)
    
    final_results_after_improved.append((beta, final_S, final_I, final_R, avg_S_values_after, avg_I_values_after, avg_R_values_after))

# Display removed cities
print(f"Cities removed for mosquito control: {removed_cities}")

# Display final results after applying the strategy
print("Final Results After Improved Strategy:")
print(final_results_after_improved)

# Generate heatmaps
def generate_heatmap(data, title, xlabel, ylabel):
    plt.figure(figsize=(10, 8))
    sns.heatmap(data, cmap='viridis')
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.show()

# Prepare data for heatmaps
heatmap_data_before = []
heatmap_data_after = []

for beta, final_S, final_I, final_R, S_values, I_values, R_values in final_results_before:
    for t, (s, i, r) in enumerate(zip(S_values, I_values, R_values)):
        heatmap_data_before.append([beta, t, s, i, r])

for beta, final_S, final_I, final_R, S_values, I_values, R_values in final_results_after_improved:
    for t, (s, i, r) in enumerate(zip(S_values, I_values, R_values)):
        heatmap_data_after.append([beta, t, s, i, r])

heatmap_df_before = pd.DataFrame(heatmap_data_before, columns=['Beta', 'Time', 'Susceptible', 'Infected', 'Recovered'])
heatmap_df_after = pd.DataFrame(heatmap_data_after, columns=['Beta', 'Time', 'Susceptible', 'Infected', 'Recovered'])

# Generate heatmaps for Infected individuals
generate_heatmap(heatmap_df_before.pivot(index='Time', columns='Beta', values='Infected'), 'Heatmap of Infected Individuals (Before)', 'Beta', 'Time')
generate_heatmap(heatmap_df_after.pivot(index='Time', columns='Beta', values='Infected'), 'Heatmap of Infected Individuals (After)', 'Beta', 'Time')
