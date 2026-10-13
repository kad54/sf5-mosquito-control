"""Original SIR and combined-centrality functions, extracted from scripts/results.py.

Function bodies are retained verbatim. Gamma is accepted but unused in the
original implementation; infectious cities recover after one transmission step.
"""

import random
import networkx as nx


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
