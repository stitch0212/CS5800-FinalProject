import osmnx as ox
import networkx as nx
from scripts.extract_network import extract_road_network
from scripts.calculate_travel_time import calculate_travel_times
from scripts.fetch_solar_data import calculate_road_solar_exposure
from scripts.visualize_route import visualize_route
from scripts.sun_optimized_route import sun_optimized_route

def test_with_LA_data():
    # Define locations
    location = "Los Angeles, California, USA"
    graph_path = "./data/road_network.graphml"
    time_weighted_path = "./data/road_network_time_weighted.graphml"
    solar_weighted_path = "./data/road_network_solar_weighted.graphml"

    # Extract the road network
    print("\n=== Extracting Road Network ===")
    G = extract_road_network(location, graph_path)

    # Calculate travel times
    print("\n=== Calculating Travel Times ===")
    G_time = calculate_travel_times(graph_path, time_weighted_path)

    # Fetch solar data and calculate solar exposure
    print("\n=== Calculating Solar Exposure ===")
    api_key = "YOUR_NREL_API_KEY"  # Replace with your API key
    G_solar = calculate_road_solar_exposure(G, api_key, output_path=solar_weighted_path)

    # Test different scenarios
    test_scenarios = [
        {
            "name": "City Hall to USC",
            "start": (34.0537, -118.2428),  # Los Angeles City Hall
            "end": (34.0219, -118.2854),    # USC
            "initial_energy": 50.0,          # kWh (typical EV battery capacity)
            "consumption_rate": 0.15,        # kWh/km (typical EV consumption)
        },
        {
            "name": "Downtown to Santa Monica",
            "start": (34.0522, -118.2437),   # Downtown LA
            "end": (34.0195, -118.4912),     # Santa Monica
            "initial_energy": 8.0,           # kWh
            "consumption_rate": 0.25,        # kWh/km (higher due to highway speeds)
        }
    ]

    for scenario in test_scenarios:
        print(f"\n=== Testing Scenario: {scenario['name']} ===")
        print(f"Initial Energy: {scenario['initial_energy']} kWh")
        print(f"Consumption Rate: {scenario['consumption_rate']} kWh/km")

        # Get start and end nodes
        start_node = ox.distance.nearest_nodes(G_time, 
                                             X=scenario['start'][1], 
                                             Y=scenario['start'][0])
        end_node = ox.distance.nearest_nodes(G_time, 
                                           X=scenario['end'][1], 
                                           Y=scenario['end'][0])

        # Check if path exists
        if not nx.has_path(G_time, start_node, end_node):
            print(f"No path exists between start and end points.")
            continue

        # Find optimal route
        route, solar_gained, distance, final_energy = sun_optimized_route(
            G_time,
            G_solar,
            start=start_node,
            end=end_node,
            initial_energy=scenario['initial_energy'],
            consumption_rate=scenario['consumption_rate']
        )

        if route:
            # Calculate travel time
            travel_time = sum(
                G_time[u][v][0]['travel_time']
                for u, v in zip(route[:-1], route[1:])
            )
            energy_consumed = distance * scenario['consumption_rate']

            print("\nRoute Metrics:")
            print(f"Distance: {distance:.2f} km")
            print(f"Travel Time: {travel_time:.2f} minutes")
            print(f"Energy Consumed: {energy_consumed:.2f} kWh")
            print(f"Solar Energy Gained: {solar_gained:.2f} kWh")
            print(f"Final Energy: {final_energy:.2f} kWh")

            # Visualize route
            output_path = f"./output/route_{scenario['name'].replace(' ', '_').lower()}.png"
            visualize_route(
                G_time,
                route,
                output_path=output_path,
                title=f"Route: {scenario['name']}\nEnergy: {final_energy:.1f} kWh"
            )
            print(f"Route visualization saved to {output_path}")
        else:
            print("No viable route found for this scenario.")

if __name__ == "__main__":
    test_with_LA_data()