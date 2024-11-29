import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
from scripts.sun_optimization_with_pareto import sun_optimized_route
from scripts.visualize_route import visualize_route
from scripts.solar_config import SolarConfig
import time

def evaluate_routes():
    """
    Evaluate routing algorithm by comparing solar-optimized routes with shortest paths.
    """
    output_dir = Path("./output/route_evaluation")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n=== Loading Graph ===")
    G_combined = ox.load_graphml("./data/road_network_combined.graphml")
    
    test_scenarios = [
        {
            "name": "Limited Energy",
            "start": (34.0522, -118.2437),    # Downtown LA
            "end": (34.086818, -118.289575),  # East Hollywood
            "initial_energy": 0.62,            # Limited energy
            "consumption_rate": 0.17,          # Moderate consumption
            "description": "Should allow solar optimization"
        },
        {
            "name": "Sufficient Energy",
            "start": (34.0522, -118.2437),    # Downtown LA
            "end": (34.086818, -118.289575),  # East Hollywood
            "initial_energy": 2.0,             # Sufficient energy
            "consumption_rate": 0.17,          # Moderate consumption
            "description": "Should take shortest path"
        }
    ]
    
    solar_config = SolarConfig(use_enhanced=True)
    results = []
    
    # Process each scenario
    for scenario in test_scenarios:
        print(f"\n=== Testing Scenario: {scenario['name']} ===")
        print(f"Description: {scenario['description']}")
        print(f"Initial Energy: {scenario['initial_energy']} kWh")
        print(f"Consumption Rate: {scenario['consumption_rate']} kWh/km")
        
        # Get nodes
        start_node = ox.distance.nearest_nodes(
            G_combined,
            X=scenario['start'][1],
            Y=scenario['start'][0]
        )
        end_node = ox.distance.nearest_nodes(
            G_combined,
            X=scenario['end'][1],
            Y=scenario['end'][0]
        )
        
        # Calculate shortest path metrics
        shortest_path = nx.shortest_path(G_combined, start_node, end_node, weight='travel_time')
        shortest_distance = sum(
            G_combined[u][v][0]['length'] for u, v in zip(shortest_path[:-1], shortest_path[1:])
        ) / 1000
        
        # Calculate energy metrics for shortest path
        shortest_energy_consumed = shortest_distance * scenario['consumption_rate']
        shortest_solar_gained = sum(
            solar_config.calculate_solar_gain(
                time_minutes=G_combined[u][v][0]['travel_time'],
                GHI=G_combined[u][v][0]['solar_exposure']
            )
            for u, v in zip(shortest_path[:-1], shortest_path[1:])
        )
        shortest_final_energy = scenario['initial_energy'] - shortest_energy_consumed + shortest_solar_gained
        
        # Store shortest path results
        results.append({
            'scenario': scenario['name'],
            'route_type': 'Shortest Path',
            'initial_energy': scenario['initial_energy'],
            'distance': shortest_distance,
            'energy_consumed': shortest_energy_consumed,
            'solar_gained': shortest_solar_gained,
            'final_energy': shortest_final_energy,
            'solar_efficiency': shortest_solar_gained / shortest_distance if shortest_distance > 0 else 0
        })
        
        # Visualize shortest path
        route_file = f"route_{scenario['name'].lower()}_shortest.png"
        visualize_route(
            G_combined,
            shortest_path,
            output_path=output_dir / route_file,
            title=f"{scenario['name']} - Shortest Path\nDistance: {shortest_distance:.1f}km, Final Energy: {shortest_final_energy:.1f}kWh"
        )
        
        # Calculate solar-optimized route
        solar_path, solar_gained, distance, final_energy = sun_optimized_route(
            G_combined,
            G_combined,
            start_node,
            end_node,
            scenario['initial_energy'],
            scenario['consumption_rate'],
            min_energy_buffer=0.1,
            solar_config=solar_config
        )
        
        if solar_path:
            energy_consumed = distance * scenario['consumption_rate']
            
            # Store solar-optimized results
            results.append({
                'scenario': scenario['name'],
                'route_type': 'Solar Optimized',
                'initial_energy': scenario['initial_energy'],
                'distance': distance,
                'energy_consumed': energy_consumed,
                'solar_gained': solar_gained,
                'final_energy': final_energy,
                'solar_efficiency': solar_gained / distance if distance > 0 else 0
            })
            
            # Visualize solar-optimized path
            route_file = f"route_{scenario['name'].lower()}_solar.png"
            visualize_route(
                G_combined,
                solar_path,
                output_path=output_dir / route_file,
                title=f"{scenario['name']} - Solar Optimized\nDistance: {distance:.1f}km, Final Energy: {final_energy:.1f}kWh"
            )
            
            # Print comparison
            print(f"\nComparison for {scenario['name']}:")
            print(f"Shortest Path - Distance: {shortest_distance:.2f}km, Final Energy: {shortest_final_energy:.2f}kWh")
            print(f"Solar Optimized - Distance: {distance:.2f}km, Final Energy: {final_energy:.2f}kWh")
            print(f"Difference - Distance: {((distance/shortest_distance)-1)*100:+.1f}%, Energy: {final_energy-shortest_final_energy:+.2f}kWh")
    
    # Create comparative plots
    if results:
        df = pd.DataFrame(results)
        create_comparison_plots(df, output_dir)
        df.to_csv(output_dir / 'route_comparison_results.csv', index=False)
    
    return df

def create_comparison_plots(df, output_dir):
    """Create comparative visualization plots."""
    scenarios = df['scenario'].unique()
    
    # 1. Distance Comparison
    plt.figure(figsize=(10, 5))
    x = range(len(scenarios))
    width = 0.35
    
    shortest_distances = df[df['route_type'] == 'Shortest Path']['distance']
    solar_distances = df[df['route_type'] == 'Solar Optimized']['distance']
    
    plt.bar(x, shortest_distances, width, label='Shortest Path', color='blue', alpha=0.6)
    plt.bar([i + width for i in x], solar_distances, width, label='Solar Optimized', color='orange', alpha=0.6)
    
    plt.xlabel('Scenario')
    plt.ylabel('Distance (km)')
    plt.title('Route Distance Comparison')
    plt.xticks([i + width/2 for i in x], scenarios, rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / 'distance_comparison.png')
    plt.close()
    
    # 2. Energy Comparison
    plt.figure(figsize=(10, 5))
    plt.subplot(1, 2, 1)
    
    for i, scenario in enumerate(scenarios):
        scenario_data = df[df['scenario'] == scenario]
        shortest = scenario_data[scenario_data['route_type'] == 'Shortest Path'].iloc[0]
        solar = scenario_data[scenario_data['route_type'] == 'Solar Optimized'].iloc[0]
        
        x = [0, 1]
        plt.plot(x, [shortest['final_energy'], solar['final_energy']], 
                marker='o', label=scenario)
    
    plt.xticks([0, 1], ['Shortest Path', 'Solar Optimized'])
    plt.ylabel('Final Energy (kWh)')
    plt.title('Final Energy Comparison')
    plt.legend()
    
    plt.subplot(1, 2, 2)
    shortest_efficiency = df[df['route_type'] == 'Shortest Path']['solar_efficiency']
    solar_efficiency = df[df['route_type'] == 'Solar Optimized']['solar_efficiency']
    
    plt.bar(x, [shortest_efficiency.mean(), solar_efficiency.mean()], alpha=0.6)
    plt.xticks([0, 1], ['Shortest Path', 'Solar Optimized'])
    plt.ylabel('Solar Efficiency (kWh/km)')
    plt.title('Average Solar Efficiency')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'energy_comparison.png')
    plt.close()

if __name__ == "__main__":
    try:
        results_df = evaluate_routes()
        print("\nEvaluation completed successfully!")
    except Exception as e:
        print(f"Evaluation failed with error: {str(e)}")
        raise