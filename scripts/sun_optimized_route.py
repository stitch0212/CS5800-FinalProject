import networkx as nx
from typing import Dict, List, Tuple

def sun_optimized_route(
    G_travel_time, 
    G_solar_exposure, 
    start, 
    end, 
    initial_energy, 
    consumption_rate,
    min_energy_buffer=0.5
) -> Tuple[List[int], float, float, float]:
    """
    Compute sun-optimized route with standardized solar power calculation.
    
    Args:
        G_travel_time: Graph weighted by travel times
        G_solar_exposure: Graph with GHI (solar exposure) data
        start: Start node
        end: End node
        initial_energy: Initial battery energy (kWh)
        consumption_rate: Energy consumption per km (kWh/km)
        min_energy_buffer: Minimum energy buffer to maintain (kWh)
    
    Returns:
        tuple: (path, solar_gained, distance, final_energy)
    """
    # Solar panel specifications
    PANEL_AREA = 2.0  # m² (typical car roof)
    PANEL_EFFICIENCY = 0.20  # 20% efficient panels
    SYSTEM_LOSSES = 0.85  # 15% system losses
    DAYLIGHT_HOURS = 8  # hours of effective sunlight per day
    
    def calculate_segment_solar_gain(time_hours: float, GHI: float) -> float:
        """Calculate solar energy gained for a segment of the route."""
        hourly_GHI = GHI / DAYLIGHT_HOURS  # Convert daily GHI to hourly
        return hourly_GHI * PANEL_AREA * PANEL_EFFICIENCY * SYSTEM_LOSSES * time_hours
    
    print(f"\nAnalyzing route from {start} to {end}")
    print(f"Initial energy: {initial_energy:.2f} kWh")
    print(f"Solar panel specs: {PANEL_AREA}m², {PANEL_EFFICIENCY*100}% efficiency")
    
    # Calculate shortest path first
    shortest_path = nx.shortest_path(G_travel_time, source=start, target=end, weight="weight")
    
    # Calculate metrics for shortest path
    shortest_distance = sum(
        G_travel_time[u][v][0]["length"] for u, v in zip(shortest_path[:-1], shortest_path[1:])
    ) / 1000  # Convert meters to km
    
    energy_consumed = shortest_distance * consumption_rate
    
    # Calculate solar gain with standard equation
    total_time_hours = sum(
        G_travel_time[u][v][0]['travel_time'] for u, v in zip(shortest_path[:-1], shortest_path[1:])
    ) / 3600  # Convert seconds to hours
    
    solar_gained = sum(
        calculate_segment_solar_gain(
            time_hours=G_travel_time[u][v][0]['travel_time'] / 3600,
            GHI=G_solar_exposure[u][v][0]['solar_exposure']
        )
        for u, v in zip(shortest_path[:-1], shortest_path[1:])
    )
    
    print(f"\nShortest path analysis:")
    print(f"Distance: {shortest_distance:.2f} km")
    print(f"Travel time: {total_time_hours:.2f} hours")
    print(f"Energy required: {energy_consumed:.2f} kWh")
    print(f"Solar energy gained: {solar_gained:.2f} kWh")
    print(f"Net energy requirement: {energy_consumed - solar_gained:.2f} kWh")

    # Check if shortest path is feasible
    if initial_energy + solar_gained >= energy_consumed + min_energy_buffer:
        print("Sufficient energy for shortest path")
        final_energy = initial_energy - energy_consumed + solar_gained
        return shortest_path, solar_gained, shortest_distance, final_energy

    print("Insufficient energy, calculating solar-assisted path...")
    
    # Create graph with combined weights
    G_energy = G_travel_time.copy()
    for u, v, k, data in G_energy.edges(data=True, keys=True):
        # Calculate energy costs and gains
        distance = data['length'] / 1000  # km
        energy_cost = distance * consumption_rate
        time_hours = data['travel_time'] / 3600
        
        solar_gain = calculate_segment_solar_gain(
            time_hours=time_hours,
            GHI=G_solar_exposure[u][v][k]['solar_exposure']
        )
        
        # Net energy cost (consumption minus solar gain)
        net_energy = max(0.1, energy_cost - solar_gain)
        
        # Combined weight considering both time and energy
        data['weight'] = data['travel_time'] * net_energy

    try:
        solar_path = nx.shortest_path(G_energy, source=start, target=end, weight='weight')
        
        # Calculate metrics for solar optimized path
        distance = sum(
            G_travel_time[u][v][0]['length'] for u, v in zip(solar_path[:-1], solar_path[1:])
        ) / 1000  # km
        
        energy_consumed = distance * consumption_rate
        solar_gained = sum(
            calculate_segment_solar_gain(
                time_hours=G_travel_time[u][v][0]['travel_time'] / 3600,
                GHI=G_solar_exposure[u][v][0]['solar_exposure']
            )
            for u, v in zip(solar_path[:-1], solar_path[1:])
        )
        
        final_energy = initial_energy - energy_consumed + solar_gained
        
        # Check if route is actually feasible
        if final_energy < min_energy_buffer:
            print(f"Route not feasible: final energy ({final_energy:.2f} kWh) below minimum buffer ({min_energy_buffer} kWh)")
            return None, 0.0, 0.0, initial_energy
        
        print("\nSolar-assisted path analysis:")
        print(f"Distance: {distance:.2f} km")
        print(f"Energy consumed: {energy_consumed:.2f} kWh")
        print(f"Solar energy gained: {solar_gained:.2f} kWh")
        print(f"Net energy used: {energy_consumed - solar_gained:.2f} kWh")
        print(f"Final energy: {final_energy:.2f} kWh")
        
        return solar_path, solar_gained, distance, final_energy

    except nx.NetworkXNoPath:
        print("No viable path found")
        return None, 0.0, 0.0, initial_energy