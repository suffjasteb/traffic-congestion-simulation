import numpy as np
import random
from typing import Dict, List, Callable

class TrafficPatternGenerator:
    """Generate realistic traffic patterns"""
    
    @staticmethod
    def morning_rush_pattern(minute: int) -> float:
        """
        Morning rush hour pattern (7-9 AM simulation)
        Returns multiplier for base traffic rate
        """
        # Peak at minute 30 (8 AM)
        if minute < 30:
            # Gradual increase
            return 0.5 + (minute / 30) * 1.5
        elif minute < 60:
            # Peak and gradual decrease
            return 2.0 - ((minute - 30) / 30) * 1.0
        else:
            return 1.0
    
    @staticmethod
    def evening_rush_pattern(minute: int) -> float:
        """
        Evening rush hour pattern (5-7 PM simulation)
        Returns multiplier for base traffic rate
        """
        if minute < 20:
            # Quick ramp up
            return 1.0 + (minute / 20) * 1.5
        elif minute < 50:
            # Sustained peak
            return 2.5
        else:
            # Sharp decline
            return 2.5 - ((minute - 50) / 10) * 1.5
    
    @staticmethod
    def weekend_pattern(minute: int) -> float:
        """Weekend traffic - more distributed, lower peaks"""
        # Gentle sine wave
        return 0.7 + 0.3 * np.sin((minute / 60) * np.pi)
    
    @staticmethod
    def special_event_pattern(minute: int, event_start: int = 30, event_duration: int = 15) -> float:
        """
        Simulate special event (concert, sports game) causing traffic spike
        """
        if minute < event_start:
            # Build up before event
            return 1.0 + ((minute / event_start) * 0.5)
        elif minute < event_start + event_duration:
            # During event - very high traffic
            return 3.0
        elif minute < event_start + event_duration + 20:
            # After event - gradual decrease
            offset = minute - (event_start + event_duration)
            return 3.0 - (offset / 20) * 2.0
        else:
            return 1.0
    
    @staticmethod
    def weather_impact(base_pattern: Callable, weather: str) -> Callable:
        """
        Apply weather effects to traffic pattern
        weather: 'clear', 'rain', 'heavy_rain', 'snow'
        """
        weather_multipliers = {
            'clear': 1.0,
            'rain': 0.85,  # 15% slower
            'heavy_rain': 0.65,  # 35% slower
            'snow': 0.50  # 50% slower
        }
        
        multiplier = weather_multipliers.get(weather, 1.0)
        
        def modified_pattern(minute: int) -> float:
            return base_pattern(minute) * multiplier
        
        return modified_pattern
    
    @staticmethod
    def multi_phase_pattern(phases: List[Dict]) -> Callable:
        """
        Create complex multi-phase pattern
        
        phases format:
        [
            {'duration': 20, 'base_rate': [10, 15], 'multiplier': 1.0},
            {'duration': 30, 'base_rate': [20, 30], 'multiplier': 2.5},
            {'duration': 10, 'base_rate': [15, 20], 'multiplier': 1.5}
        ]
        """
        def pattern(minute: int) -> Dict:
            cumulative = 0
            for phase in phases:
                if minute < cumulative + phase['duration']:
                    return {
                        'base_rate': phase['base_rate'],
                        'multiplier': phase['multiplier']
                    }
                cumulative += phase['duration']
            
            # Default to last phase
            return {
                'base_rate': phases[-1]['base_rate'],
                'multiplier': phases[-1]['multiplier']
            }
        
        return pattern

class RealWorldScenarios:
    """Predefined realistic traffic scenarios"""
    
    @staticmethod
    def surabaya_morning_commute():
        """Surabaya typical morning commute pattern"""
        return {
            'name': 'Surabaya Morning Commute',
            'description': 'Typical workday morning in Surabaya (6-10 AM)',
            'pattern': TrafficPatternGenerator.multi_phase_pattern([
                {'duration': 30, 'base_rate': [8, 12], 'multiplier': 1.2},  # 6-6:30 AM
                {'duration': 60, 'base_rate': [15, 25], 'multiplier': 2.0},  # 6:30-7:30 AM Peak
                {'duration': 60, 'base_rate': [12, 20], 'multiplier': 1.8},  # 7:30-8:30 AM
                {'duration': 30, 'base_rate': [8, 15], 'multiplier': 1.3},  # 8:30-9 AM
                {'duration': 60, 'base_rate': [5, 10], 'multiplier': 0.8}   # 9-10 AM Normal
            ]),
            'accident_probability': 0.06,  # Higher in rush hour
            'green_capacity': 8
        }
    
    @staticmethod
    def rainy_season_traffic():
        """Surabaya rainy season impact"""
        base_pattern = TrafficPatternGenerator.morning_rush_pattern
        return {
            'name': 'Rainy Season Traffic',
            'description': 'Heavy rain during morning commute',
            'pattern': TrafficPatternGenerator.weather_impact(base_pattern, 'heavy_rain'),
            'accident_probability': 0.12,  # Much higher in rain
            'green_capacity': 6  # Reduced capacity due to visibility
        }
    
    @staticmethod
    def weekend_mall_traffic():
        """Weekend shopping area traffic"""
        return {
            'name': 'Weekend Mall Traffic',
            'description': 'Weekend afternoon shopping area',
            'pattern': TrafficPatternGenerator.multi_phase_pattern([
                {'duration': 60, 'base_rate': [5, 10], 'multiplier': 1.0},  # Morning
                {'duration': 120, 'base_rate': [10, 18], 'multiplier': 1.5},  # Afternoon peak
                {'duration': 60, 'base_rate': [8, 15], 'multiplier': 1.2}   # Evening
            ]),
            'accident_probability': 0.03,
            'green_capacity': 10
        }
    
    @staticmethod
    def concert_venue_exit():
        """Traffic after major event"""
        return {
            'name': 'Concert Venue Exit',
            'description': 'Mass exodus after 2-hour event',
            'pattern': TrafficPatternGenerator.special_event_pattern(
                event_start=120,  # Event ends at 2 hours
                event_duration=30  # 30 min exodus
            ),
            'accident_probability': 0.08,
            'green_capacity': 8
        }
    
    @staticmethod
    def road_construction_detour():
        """Detour due to construction"""
        return {
            'name': 'Construction Detour',
            'description': 'Single lane operation due to construction',
            'pattern': TrafficPatternGenerator.morning_rush_pattern,
            'accident_probability': 0.04,
            'green_capacity': 4,  # Severely reduced
            'construction_active': True
        }

class VehicleTypeSimulation:
    """Simulate different vehicle types with different behaviors"""
    
    VEHICLE_TYPES = {
        'car': {
            'capacity_usage': 1.0,
            'speed_multiplier': 1.0,
            'proportion': 0.60
        },
        'motorcycle': {
            'capacity_usage': 0.3,
            'speed_multiplier': 1.2,
            'proportion': 0.30
        },
        'bus': {
            'capacity_usage': 2.0,
            'speed_multiplier': 0.8,
            'proportion': 0.05
        },
        'truck': {
            'capacity_usage': 2.5,
            'speed_multiplier': 0.7,
            'proportion': 0.05
        }
    }
    
    @staticmethod
    def generate_vehicle_mix(num_vehicles: int) -> Dict[str, int]:
        """Generate realistic vehicle mix"""
        mix = {}
        remaining = num_vehicles
        
        types = list(VehicleTypeSimulation.VEHICLE_TYPES.keys())
        proportions = [VehicleTypeSimulation.VEHICLE_TYPES[t]['proportion'] 
                      for t in types]
        
        # Generate counts based on proportions
        for i, vtype in enumerate(types[:-1]):
            count = int(num_vehicles * proportions[i])
            mix[vtype] = count
            remaining -= count
        
        # Remainder goes to last type
        mix[types[-1]] = remaining
        
        return mix
    
    @staticmethod
    def calculate_effective_capacity_usage(vehicle_mix: Dict[str, int]) -> float:
        """Calculate how much road capacity is actually used"""
        total_usage = 0
        for vtype, count in vehicle_mix.items():
            usage = VehicleTypeSimulation.VEHICLE_TYPES[vtype]['capacity_usage']
            total_usage += count * usage
        
        return total_usage

def run_advanced_simulation(
    scenario_config: Dict,
    simulation_minutes: int = 240,
    simulations: int = 1000
) -> Dict:
    """
    Run simulation with advanced traffic patterns
    """
    
    pattern_func = scenario_config['pattern']
    accident_prob = scenario_config['accident_probability']
    base_capacity = scenario_config['green_capacity']
    
    all_results = []
    
    for sim_num in range(simulations):
        queue = 0
        max_queue = 0
        total_waiting = 0
        total_vehicles = 0
        vehicles_served = 0
        
        accident_active = False
        accident_remaining = 0
        
        queue_history = []
        
        for minute in range(simulation_minutes):
            # Get traffic pattern for this minute
            pattern_data = pattern_func(minute)
            
            if isinstance(pattern_data, dict):
                # Multi-phase pattern
                base_rate = pattern_data['base_rate']
                multiplier = pattern_data['multiplier']
                arrivals = random.randint(base_rate[0], base_rate[1])
                arrivals = int(arrivals * multiplier)
            else:
                # Simple pattern
                base_arrivals = random.randint(5, 15)
                arrivals = int(base_arrivals * pattern_data)
            
            queue += arrivals
            total_vehicles += arrivals
            
            # Accident handling
            if not accident_active and random.random() < accident_prob:
                accident_active = True
                accident_remaining = random.randint(5, 15)
            
            capacity = base_capacity
            if accident_active:
                capacity = max(2, base_capacity // 4)
                accident_remaining -= 1
                if accident_remaining <= 0:
                    accident_active = False
            
            # Process vehicles
            served = min(queue, capacity)
            queue -= served
            vehicles_served += served
            
            total_waiting += queue
            max_queue = max(max_queue, queue)
            queue_history.append(queue)
        
        # Calculate metrics
        avg_waiting = total_waiting / total_vehicles if total_vehicles > 0 else 0
        service_rate = vehicles_served / total_vehicles if total_vehicles > 0 else 0
        
        all_results.append({
            'max_queue': max_queue,
            'avg_waiting': avg_waiting,
            'service_rate': service_rate,
            'queue_history': queue_history
        })
    
    # Aggregate
    max_queues = [r['max_queue'] for r in all_results]
    avg_waitings = [r['avg_waiting'] for r in all_results]
    service_rates = [r['service_rate'] for r in all_results]
    
    return {
        'scenario_name': scenario_config['name'],
        'scenario_description': scenario_config['description'],
        'avg_max_queue': float(np.mean(max_queues)),
        'std_max_queue': float(np.std(max_queues)),
        'median_max_queue': float(np.median(max_queues)),
        'percentile_95': float(np.percentile(max_queues, 95)),
        'avg_waiting_time': float(np.mean(avg_waitings)),
        'avg_service_rate': float(np.mean(service_rates)),
        'all_max_queues': max_queues,
        'sample_queue_history': all_results[0]['queue_history']
    }

if __name__ == "__main__":
    print("Testing Advanced Traffic Patterns...")
    print("=" * 60)
    
    # Test Surabaya morning commute
    scenario = RealWorldScenarios.surabaya_morning_commute()
    
    print(f"\nSimulating: {scenario['name']}")
    print(f"Description: {scenario['description']}")
    
    result = run_advanced_simulation(scenario, simulation_minutes=240, simulations=100)
    
    print(f"\nResults:")
    print(f"  Avg Max Queue: {result['avg_max_queue']:.1f} vehicles")
    print(f"  Avg Waiting Time: {result['avg_waiting_time']:.2f} minutes")
    print(f"  Service Rate: {result['avg_service_rate']*100:.1f}%")
    
    print("\n✅ Advanced patterns working!")