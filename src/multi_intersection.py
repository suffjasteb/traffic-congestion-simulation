import random
import numpy as np
from typing import Dict, List, Tuple
from collections import defaultdict

class Intersection:
    """Represents a single traffic intersection"""
    
    def __init__(self, intersection_id, green_capacity=8, accident_prob=0.05):
        self.id = intersection_id
        self.green_capacity = green_capacity
        self.green_capacity_accident = max(2, green_capacity // 4)
        self.accident_prob = accident_prob
        
        self.queue = 0
        self.max_queue = 0
        self.total_waiting_time = 0
        self.vehicles_served = 0
        self.total_vehicles = 0
        
        self.accident_active = False
        self.accident_remaining = 0
        self.accident_count = 0
        
        self.queue_history = []
        self.throughput_history = []
    
    def add_vehicles(self, count):
        """Add vehicles to intersection queue"""
        self.queue += count
        self.total_vehicles += count
    
    def process_cycle(self, minute):
        """Process one minute of traffic"""
        # Check for new accident
        if not self.accident_active and random.random() < self.accident_prob:
            self.accident_active = True
            self.accident_remaining = random.randint(5, 15)
            self.accident_count += 1
        
        # Determine capacity
        if self.accident_active:
            capacity = self.green_capacity_accident
            self.accident_remaining -= 1
            if self.accident_remaining <= 0:
                self.accident_active = False
        else:
            capacity = self.green_capacity
        
        # Process vehicles
        served = min(self.queue, capacity)
        self.queue -= served
        self.vehicles_served += served
        
        # Update statistics
        self.total_waiting_time += self.queue
        self.max_queue = max(self.max_queue, self.queue)
        
        # Record history
        self.queue_history.append(self.queue)
        self.throughput_history.append(served)
        
        return served
    
    def get_metrics(self):
        """Get intersection performance metrics"""
        avg_waiting_time = (self.total_waiting_time / self.total_vehicles 
                           if self.total_vehicles > 0 else 0)
        service_rate = (self.vehicles_served / self.total_vehicles 
                       if self.total_vehicles > 0 else 0)
        
        return {
            'intersection_id': self.id,
            'max_queue': self.max_queue,
            'final_queue': self.queue,
            'avg_waiting_time': avg_waiting_time,
            'service_rate': service_rate,
            'total_vehicles': self.total_vehicles,
            'vehicles_served': self.vehicles_served,
            'accident_count': self.accident_count
        }

class TrafficNetwork:
    """Network of interconnected intersections"""
    
    def __init__(self, network_config):
        """
        network_config format:
        {
            'intersections': [
                {'id': 'A', 'capacity': 8, 'accident_prob': 0.05},
                {'id': 'B', 'capacity': 10, 'accident_prob': 0.03},
                ...
            ],
            'routes': [
                {'from': None, 'to': 'A', 'flow_rate': [10, 20], 'split': 1.0},
                {'from': 'A', 'to': 'B', 'split': 0.6},
                {'from': 'A', 'to': 'C', 'split': 0.4},
                ...
            ]
        }
        """
        self.intersections = {}
        self.routes = []
        
        # Create intersections
        for config in network_config['intersections']:
            intersection = Intersection(
                intersection_id=config['id'],
                green_capacity=config.get('capacity', 8),
                accident_prob=config.get('accident_prob', 0.05)
            )
            self.intersections[config['id']] = intersection
        
        # Store routes
        self.routes = network_config['routes']
    
    def simulate_minute(self, minute, is_rush_hour=False):
        """Simulate one minute of traffic across the network"""
        
        # Process external arrivals (routes with from=None)
        for route in self.routes:
            if route['from'] is None:
                # External traffic entering network
                flow_rate = route['flow_rate']
                arrivals = random.randint(flow_rate[0], flow_rate[1])
                
                to_intersection = self.intersections[route['to']]
                to_intersection.add_vehicles(arrivals)
        
        # Process each intersection
        departures = {}
        for intersection_id, intersection in self.intersections.items():
            served = intersection.process_cycle(minute)
            departures[intersection_id] = served
        
        # Route departed vehicles to next intersections
        for route in self.routes:
            if route['from'] is not None:
                from_id = route['from']
                to_id = route['to']
                split = route['split']
                
                vehicles_to_route = int(departures[from_id] * split)
                
                if to_id in self.intersections:
                    self.intersections[to_id].add_vehicles(vehicles_to_route)
    
    def get_network_metrics(self):
        """Get metrics for entire network"""
        metrics = {}
        
        for intersection_id, intersection in self.intersections.items():
            metrics[intersection_id] = intersection.get_metrics()
        
        # Calculate network-wide metrics
        total_max_queue = sum(m['max_queue'] for m in metrics.values())
        total_vehicles = sum(m['total_vehicles'] for m in metrics.values())
        total_served = sum(m['vehicles_served'] for m in metrics.values())
        
        metrics['network_summary'] = {
            'total_max_queue': total_max_queue,
            'avg_max_queue_per_intersection': total_max_queue / len(self.intersections),
            'total_vehicles': total_vehicles,
            'total_served': total_served,
            'network_service_rate': total_served / total_vehicles if total_vehicles > 0 else 0,
            'total_accidents': sum(m['accident_count'] for m in metrics.values())
        }
        
        return metrics

def run_network_simulation(
    network_config: Dict,
    rush_hour_minutes: int = 20,
    simulation_minutes: int = 60,
    simulations: int = 100
) -> Dict:
    """
    Run Monte Carlo simulation on traffic network
    """
    
    all_results = []
    
    for sim_num in range(simulations):
        network = TrafficNetwork(network_config)
        
        for minute in range(simulation_minutes):
            is_rush_hour = minute < rush_hour_minutes
            network.simulate_minute(minute, is_rush_hour)
        
        metrics = network.get_network_metrics()
        all_results.append(metrics)
    
    # Aggregate results
    aggregated = {
        'intersections': {},
        'network_summary': {}
    }
    
    # Aggregate per intersection
    for intersection_id in network_config['intersections']:
        int_id = intersection_id['id']
        
        max_queues = [r[int_id]['max_queue'] for r in all_results]
        avg_waits = [r[int_id]['avg_waiting_time'] for r in all_results]
        service_rates = [r[int_id]['service_rate'] for r in all_results]
        
        aggregated['intersections'][int_id] = {
            'avg_max_queue': float(np.mean(max_queues)),
            'std_max_queue': float(np.std(max_queues)),
            'median_max_queue': float(np.median(max_queues)),
            'avg_waiting_time': float(np.mean(avg_waits)),
            'avg_service_rate': float(np.mean(service_rates)),
            'all_max_queues': max_queues
        }
    
    # Aggregate network summary
    network_max_queues = [r['network_summary']['total_max_queue'] for r in all_results]
    network_service_rates = [r['network_summary']['network_service_rate'] for r in all_results]
    
    aggregated['network_summary'] = {
        'avg_total_max_queue': float(np.mean(network_max_queues)),
        'std_total_max_queue': float(np.std(network_max_queues)),
        'avg_network_service_rate': float(np.mean(network_service_rates)),
        'all_network_max_queues': network_max_queues
    }
    
    return aggregated

# Predefined network configurations
NETWORK_CONFIGS = {
    'simple_two_intersection': {
        'intersections': [
            {'id': 'A', 'capacity': 8, 'accident_prob': 0.05},
            {'id': 'B', 'capacity': 8, 'accident_prob': 0.05}
        ],
        'routes': [
            {'from': None, 'to': 'A', 'flow_rate': [10, 20], 'split': 1.0},
            {'from': 'A', 'to': 'B', 'split': 0.8},
            {'from': 'A', 'to': None, 'split': 0.2}  # Some leave network
        ]
    },
    
    'four_way_grid': {
        'intersections': [
            {'id': 'NW', 'capacity': 8, 'accident_prob': 0.05},
            {'id': 'NE', 'capacity': 8, 'accident_prob': 0.05},
            {'id': 'SW', 'capacity': 10, 'accident_prob': 0.03},
            {'id': 'SE', 'capacity': 10, 'accident_prob': 0.03}
        ],
        'routes': [
            # External arrivals
            {'from': None, 'to': 'NW', 'flow_rate': [8, 15], 'split': 1.0},
            {'from': None, 'to': 'NE', 'flow_rate': [8, 15], 'split': 1.0},
            
            # Internal routes
            {'from': 'NW', 'to': 'NE', 'split': 0.3},
            {'from': 'NW', 'to': 'SW', 'split': 0.5},
            {'from': 'NW', 'to': None, 'split': 0.2},
            
            {'from': 'NE', 'to': 'SE', 'split': 0.6},
            {'from': 'NE', 'to': None, 'split': 0.4},
            
            {'from': 'SW', 'to': 'SE', 'split': 0.7},
            {'from': 'SW', 'to': None, 'split': 0.3},
            
            {'from': 'SE', 'to': None, 'split': 1.0}
        ]
    },
    
    'highway_corridor': {
        'intersections': [
            {'id': 'Entry', 'capacity': 12, 'accident_prob': 0.02},
            {'id': 'Mid1', 'capacity': 10, 'accident_prob': 0.05},
            {'id': 'Mid2', 'capacity': 10, 'accident_prob': 0.05},
            {'id': 'Exit', 'capacity': 12, 'accident_prob': 0.03}
        ],
        'routes': [
            {'from': None, 'to': 'Entry', 'flow_rate': [15, 30], 'split': 1.0},
            {'from': 'Entry', 'to': 'Mid1', 'split': 0.9},
            {'from': 'Entry', 'to': None, 'split': 0.1},
            {'from': 'Mid1', 'to': 'Mid2', 'split': 0.8},
            {'from': 'Mid1', 'to': None, 'split': 0.2},
            {'from': 'Mid2', 'to': 'Exit', 'split': 0.9},
            {'from': 'Mid2', 'to': None, 'split': 0.1},
            {'from': 'Exit', 'to': None, 'split': 1.0}
        ]
    }
}

if __name__ == "__main__":
    print("Testing Multi-Intersection Simulation...")
    print("=" * 60)
    
    # Test simple network
    print("\nSimulating simple two-intersection network...")
    result = run_network_simulation(
        NETWORK_CONFIGS['simple_two_intersection'],
        simulations=100
    )
    
    print("\nResults:")
    for int_id, metrics in result['intersections'].items():
        print(f"\nIntersection {int_id}:")
        print(f"  Avg Max Queue: {metrics['avg_max_queue']:.1f} vehicles")
        print(f"  Avg Waiting Time: {metrics['avg_waiting_time']:.2f} minutes")
        print(f"  Service Rate: {metrics['avg_service_rate']*100:.1f}%")
    
    print(f"\nNetwork Summary:")
    print(f"  Total Avg Max Queue: {result['network_summary']['avg_total_max_queue']:.1f}")
    print(f"  Network Service Rate: {result['network_summary']['avg_network_service_rate']*100:.1f}%")
    
    print("\n✅ Multi-intersection simulation working!")