class SolarConfig:
    """Unified solar configuration for route planning algorithms."""
    
    def __init__(self, use_enhanced=False):
        """Initialize solar configuration.
        
        Args:
            use_enhanced (bool): If True, use enhanced parameters for testing
        """
        if use_enhanced:
            # Enhanced but still realistic parameters
            self.PANEL_AREA = 2.5         # m² (larger car roof coverage)
            self.PANEL_EFFICIENCY = 0.25   # 25% efficient panels (high-end commercial)
            self.SYSTEM_LOSSES = 0.90      # 10% system losses
            self.DAYLIGHT_HOURS = 5        # concentrated sunlight hours
        else:
            # Standard parameters
            self.PANEL_AREA = 1.5         # m² (typical car roof)
            self.PANEL_EFFICIENCY = 0.20   # 20% efficient panels (typical)
            self.SYSTEM_LOSSES = 0.85      # 15% system losses
            self.DAYLIGHT_HOURS = 4        # effective peak sunlight hours

    def calculate_solar_gain(self, time_minutes: float, GHI: float) -> float:
        """Calculate solar energy gain for a time period."""
        if time_minutes < 0.06:  # Avoid calculations for very short segments (less than 6 seconds)
            return 0.0

        try:
            ghi_float = float(GHI)
        except (ValueError, TypeError):
            print(f"Unexpected GHI format: {GHI}")
            return 0.0
        
        # Convert GHI to kWh/m²
        kwh_per_m2 = ghi_float * (time_minutes / 60)  # Convert minutes to hours

        # Calculate actual energy gained
        energy_gained = (
            kwh_per_m2 *
            self.PANEL_AREA *
            self.PANEL_EFFICIENCY *
            self.SYSTEM_LOSSES
        )
        
        return energy_gained

    def print_specs(self):
        """Print current solar configuration specs."""
        print("Solar Configuration:")
        print(f"Panel Area: {self.PANEL_AREA}m²")
        print(f"Panel Efficiency: {self.PANEL_EFFICIENCY*100}%")
        print(f"System Efficiency: {self.SYSTEM_LOSSES*100}%")
        print(f"Daylight Hours: {self.DAYLIGHT_HOURS}")