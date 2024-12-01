import networkx as nx
import math
import heapq
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from typing import Dict, List, Tuple
from scripts.solar_config import SolarConfig
from geopy.distance import geodesic
from collections import defaultdict
from pathlib import Path

def multi_objective_heuristic(current_node, target_node, G, solar_weight=1.0):
    """Multi-objective heuristic combining travel time and solar potential."""
    lat1, lon1 = G.nodes[current_node]["y"], G.nodes[current_node]["x"]
    lat2, lon2 = G.nodes[target_node]["y"], G.nodes[target_node]["x"]
    distance = geodesic((lat1, lon1), (lat2, lon2)).kilometers
    solar_estimate = distance * solar_weight
    return distance + solar_estimate

def visualize_pareto_frontier(paths_with_objectives, output_path=None, title="Pareto Frontier"):
    """
    Visualize the Pareto frontier for multiple objectives.

    Args:
        paths_with_objectives (list): List of dictionaries containing path metrics
        output_path (str): File path to save the visualization (optional)
        title (str): Title of the visualization plot
    """
    print("Visualizing Pareto frontier...")

    try:
        # Extract metrics for all paths
        travel_times = [path['travel_time'] for path in paths_with_objectives]
        solar_gains = [path['solar_gain'] for path in paths_with_objectives]
        energy_consumed = [path['energy_consumed'] for path in paths_with_objectives]

        # Create 3D scatter plot
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')

        # Plot all points
        scatter = ax.scatter(
            travel_times,
            solar_gains,
            energy_consumed,
            c='blue',
            marker='o',
            label='All Paths'
        )

        # Identify and plot Pareto optimal points
        pareto_points = []
        for i, path in enumerate(paths_with_objectives):
            dominated = False
            for other in paths_with_objectives:
                if (
                    other['travel_time'] <= path['travel_time'] and
                    other['solar_gain'] >= path['solar_gain'] and
                    other['energy_consumed'] <= path['energy_consumed'] and
                    (
                        other['travel_time'] < path['travel_time'] or
                        other['solar_gain'] > path['solar_gain'] or
                        other['energy_consumed'] < path['energy_consumed']
                    )
                ):
                    dominated = True
                    break
            if not dominated:
                pareto_points.append(i)

        # Plot Pareto optimal points
        pareto_travel_times = [travel_times[i] for i in pareto_points]
        pareto_solar_gains = [solar_gains[i] for i in pareto_points]
        pareto_energy = [energy_consumed[i] for i in pareto_points]

        ax.scatter(
            pareto_travel_times,
            pareto_solar_gains,
            pareto_energy,
            c='red',
            marker='*',
            s=100,
            label='Pareto Optimal'
        )

        # Connect Pareto points with lines
        if len(pareto_points) > 1:
            # Sort points by travel time for clean visualization
            pareto_indices = np.argsort(pareto_travel_times)
            sorted_times = np.array(pareto_travel_times)[pareto_indices]
            sorted_solar = np.array(pareto_solar_gains)[pareto_indices]
            sorted_energy = np.array(pareto_energy)[pareto_indices]
            
            ax.plot(
                sorted_times,
                sorted_solar,
                sorted_energy,
                'r--',
                alpha=0.5,
                label='Pareto Frontier'
            )

        # Labels and title
        ax.set_xlabel('Travel Time (minutes)')
        ax.set_ylabel('Solar Gain (kWh)')
        ax.set_zlabel('Energy Consumed (kWh)')
        ax.set_title(title)

        # Add legend
        ax.legend()

        # Adjust the viewing angle for better visualization
        ax.view_init(elev=20, azim=45)

        # Save if output path provided
        if output_path:
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, bbox_inches='tight', dpi=300)
            print(f"Pareto visualization saved at {output_path}")

        # Create 2D projections
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))

        # Time vs Solar Gain
        ax1.scatter(travel_times, solar_gains, c='blue', alpha=0.5, label='All Paths')
        ax1.scatter([travel_times[i] for i in pareto_points], 
                   [solar_gains[i] for i in pareto_points],
                   c='red', marker='*', s=100, label='Pareto Optimal')
        ax1.set_xlabel('Travel Time (minutes)')
        ax1.set_ylabel('Solar Gain (kWh)')
        ax1.set_title('Time vs Solar Gain')
        ax1.legend()

        # Time vs Energy Consumed
        ax2.scatter(travel_times, energy_consumed, c='blue', alpha=0.5, label='All Paths')
        ax2.scatter([travel_times[i] for i in pareto_points],
                   [energy_consumed[i] for i in pareto_points],
                   c='red', marker='*', s=100, label='Pareto Optimal')
        ax2.set_xlabel('Travel Time (minutes)')
        ax2.set_ylabel('Energy Consumed (kWh)')
        ax2.set_title('Time vs Energy Consumed')
        ax2.legend()

        # Solar Gain vs Energy Consumed
        ax3.scatter(solar_gains, energy_consumed, c='blue', alpha=0.5, label='All Paths')
        ax3.scatter([solar_gains[i] for i in pareto_points],
                   [energy_consumed[i] for i in pareto_points],
                   c='red', marker='*', s=100, label='Pareto Optimal')
        ax3.set_xlabel('Solar Gain (kWh)')
        ax3.set_ylabel('Energy Consumed (kWh)')
        ax3.set_title('Solar Gain vs Energy Consumed')
        ax3.legend()

        plt.tight_layout()

        # Save 2D projections if output path provided
        if output_path:
            base_path = str(output_path).rsplit('.', 1)[0]
            plt.savefig(f"{base_path}_2d_projections.png", bbox_inches='tight', dpi=300)

    except Exception as e:
        print(f"Error during Pareto visualization: {str(e)}")
        raise

def calculate_pareto_frontier(paths_with_objectives):
    """Calculate the Pareto frontier for multiple objectives."""
    pareto_frontier = []
    for candidate in paths_with_objectives:
        dominated = False
        for other in paths_with_objectives:
            if (
                other['travel_time'] <= candidate['travel_time'] and
                other['solar_gain'] >= candidate['solar_gain'] and
                other['energy_consumed'] <= candidate['energy_consumed'] and
                (
                    other['travel_time'] < candidate['travel_time'] or
                    other['solar_gain'] > candidate['solar_gain'] or
                    other['energy_consumed'] < candidate['energy_consumed']
                )
            ):
                dominated = True
                break
        if not dominated:
            pareto_frontier.append(candidate)
    return pareto_frontier

def sun_optimized_route(
    G_travel_time: nx.MultiDiGraph,
    G_solar_exposure: nx.MultiDiGraph,
    start: int,
    end: int,
    initial_energy: float,
    consumption_rate: float,
    min_energy_buffer: float = 0,
    solar_config: SolarConfig = None,
    k_paths: int = 10
) -> Tuple[List[int], float, float, float]:
    """
    Find optimal route:
    - Use shortest path if initial energy is sufficient
    - Use Pareto optimization if energy is limited
    """
    if solar_config is None:
        solar_config = SolarConfig()
    
    print(f"\nAnalyzing route from {start} to {end}")
    print(f"Initial energy: {initial_energy:.2f} kWh")
    solar_config.print_specs()
    
    def evaluate_path(path):
        """Calculate metrics for a given path."""
        distance = sum(
            G_travel_time[u][v][0]["length"] for u, v in zip(path[:-1], path[1:])
        ) / 1000
        
        energy_consumed = distance * consumption_rate
        solar_gained = sum(
            solar_config.calculate_solar_gain(
                time_minutes=G_travel_time[u][v][0]['travel_time'],
                GHI=G_solar_exposure[u][v][0]['solar_exposure']
            )
            for u, v in zip(path[:-1], path[1:])
        )
        
        final_energy = initial_energy - energy_consumed + solar_gained
        
        travel_time = sum(
            float(G_travel_time[u][v][0]['travel_time'])
            for u, v in zip(path[:-1], path[1:])
        )
        
        avg_solar = sum(
            float(G_solar_exposure[u][v][0]['solar_exposure'])
            for u, v in zip(path[:-1], path[1:])
        ) / len(path[:-1])
        
        return {
            'path': path,
            'distance': distance,
            'energy_consumed': energy_consumed,
            'solar_gain': solar_gained,
            'final_energy': final_energy,
            'travel_time': travel_time,
            'avg_solar': avg_solar
        }
    
    # First try shortest path
    shortest_path = nx.shortest_path(G_travel_time, source=start, target=end, weight="travel_time")
    shortest_metrics = evaluate_path(shortest_path)
    
    print(f"\nShortest path analysis:")
    print(f"Distance: {shortest_metrics['distance']:.2f} km")
    print(f"Energy consumed: {shortest_metrics['energy_consumed']:.2f} kWh")
    print(f"Solar gained: {shortest_metrics['solar_gain']:.2f} kWh")
    print(f"Final energy: {shortest_metrics['final_energy']:.2f} kWh")
    print(f"Travel time: {shortest_metrics['travel_time']:.2f} minutes")

    # Check if shortest path has sufficient energy
    if shortest_metrics['final_energy'] >= min_energy_buffer:
        print("\nShortest path has sufficient energy - using it")
        return (
            shortest_metrics['path'],
            shortest_metrics['solar_gain'],
            shortest_metrics['distance'],
            shortest_metrics['final_energy']
        )

    print("\nInsufficient energy for shortest path - searching for solar-optimized route...")
    
    # Initialize containers for paths
    candidate_paths = [shortest_metrics]
    
    # Convert MultiDiGraph to DiGraph with modified weights
    G_solar = nx.DiGraph()
    
    max_solar = max(
        float(G_solar_exposure[u][v][0]['solar_exposure'])
        for u, v in G_solar_exposure.edges()
    )
    
    energy_per_km = consumption_rate
    
    # Add edges with modified weights
    for u, v, data in G_travel_time.edges(data=True):
        if not G_solar.has_edge(u, v):
            time_weight = data['travel_time']
            distance = data['length'] / 1000
            
            try:
                solar_exposure = float(G_solar_exposure[u][v][0]['solar_exposure'])
                solar_factor = solar_exposure / max_solar
                
                energy_cost = distance * energy_per_km
                potential_gain = solar_config.calculate_solar_gain(
                    time_minutes=time_weight,
                    GHI=solar_exposure
                )
                energy_balance = energy_cost - potential_gain
                
                # Adjust weights based on energy state
                if initial_energy < shortest_metrics['energy_consumed']:
                    # Critical energy state - prioritize solar gain
                    TIME_WEIGHT = 0.2
                    SOLAR_WEIGHT = 0.8
                else:
                    # Normal energy state
                    TIME_WEIGHT = 0.3
                    SOLAR_WEIGHT = 0.7
                
                if energy_balance > 0:
                    energy_factor = 1 + energy_balance
                else:
                    energy_factor = 1 / (1 - energy_balance)
                    
                weight = (
                    TIME_WEIGHT * time_weight + 
                    SOLAR_WEIGHT * (time_weight * energy_factor * (1 - solar_factor))
                )
                
            except (ValueError, TypeError):
                weight = time_weight * 2
            
            G_solar.add_edge(u, v, 
                           weight=weight,
                           travel_time=time_weight,
                           length=data['length'])
    
    # Find k alternative paths using A* with multi-objective heuristic
    open_set = [(0, start, [start], initial_energy)]
    visited = set()
    
    while open_set and len(candidate_paths) < k_paths:
        _, current, path, remaining_energy = heapq.heappop(open_set)
        
        if current == end:
            metrics = evaluate_path(path)
            if metrics['final_energy'] >= min_energy_buffer:
                candidate_paths.append(metrics)
            continue
            
        if current in visited:
            continue
        visited.add(current)
        
        for neighbor in G_solar.neighbors(current):
            if neighbor in visited:
                continue
                
            edge_data = G_solar.get_edge_data(current, neighbor)
            new_path = path + [neighbor]
            
            heuristic = multi_objective_heuristic(neighbor, end, G_travel_time)
            priority = edge_data['weight'] + heuristic
            
            heapq.heappush(open_set, (priority, neighbor, new_path, remaining_energy))
    
    # Visualize Pareto frontier before calculating optimal path
    pareto_plot_path = f"output/pareto/pareto_frontier_{start}_{end}.png"
    visualize_pareto_frontier(
        candidate_paths,
        output_path=pareto_plot_path,
        title=f"Pareto Frontier for Route {start} to {end}"
    )
    
    # Calculate Pareto-optimal paths
    pareto_optimal = calculate_pareto_frontier(candidate_paths)
    
    if not pareto_optimal:
        print("\nNo viable paths found")
        return None, 0.0, 0.0, initial_energy
    
    # Choose best path based on combined criteria
    best_path = max(
        pareto_optimal,
        key=lambda x: (x['final_energy'] / x['distance']) * (1 + x['avg_solar'] / 1000)
    )

    if best_path['final_energy'] < min_energy_buffer:
        print("\nBest path does not meet minimum energy requirements")
        return None, 0.0, 0.0, initial_energy
    
    print(f"\nSelected solar-optimized path:")
    print(f"Distance: {best_path['distance']:.2f} km")
    print(f"Energy consumed: {best_path['energy_consumed']:.2f} kWh")
    print(f"Solar gained: {best_path['solar_gain']:.2f} kWh")
    print(f"Final energy: {best_path['final_energy']:.2f} kWh")
    print(f"Travel time: {best_path['travel_time']:.2f} minutes")

    return (
        best_path['path'],
        best_path['solar_gain'],
        best_path['distance'],
        best_path['final_energy']
    )