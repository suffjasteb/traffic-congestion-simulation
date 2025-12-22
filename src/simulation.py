import random
import numpy as np
from typing import Dict, List, Tuple

def run_simulation(arrival_rate, green_capacity, cycles, simulations):
    """
    Basic simulation - backward compatible with existing API
    """
    max_queues = []

    for _ in range(simulations):
        queue = 0
        max_queue = 0

        for _ in range(cycles):
            arrivals = random.randint(arrival_rate[0], arrival_rate[1])
            queue += arrivals
            queue = max(0, queue - green_capacity)
            max_queue = max(max_queue, queue)

        max_queues.append(max_queue)

    return {
        "avg_max_queue": float(np.mean(max_queues)),
        "min_max_queue": int(np.min(max_queues)),
        "max_max_queue": int(np.max(max_queues)),
        "std_max_queue": float(np.std(max_queues)),
        "all_max_queues": max_queues  # untuk plotting
    }


def run_enhanced_simulation(
    rush_hour_rate: List[int],
    normal_rate: List[int],
    rush_hour_minutes: int,
    green_capacity_normal: int,
    green_capacity_accident: int,
    accident_probability: float,
    accident_duration_range: List[int],
    simulation_minutes: int,
    simulations: int = 1000
) -> Dict:
    """
    Enhanced simulation dengan rush hour, accidents, dan metrics detail
    """
    
    all_results = []
    
    for sim_num in range(simulations):
        # State variables
        queue = 0
        max_queue = 0
        total_waiting_time = 0
        total_vehicles = 0
        vehicles_served = 0
        
        # Tracking metrics per minute
        queue_history = []
        throughput_history = []
        
        # Accident state
        accident_active = False
        accident_remaining = 0
        accident_count = 0
        
        for minute in range(simulation_minutes):
            # Determine if rush hour
            is_rush_hour = minute < rush_hour_minutes
            
            # Get arrival rate based on time
            if is_rush_hour:
                arrivals = random.randint(rush_hour_rate[0], rush_hour_rate[1])
            else:
                arrivals = random.randint(normal_rate[0], normal_rate[1])
            
            # Add new vehicles to queue
            queue += arrivals
            total_vehicles += arrivals
            
            # Check for accident (only if no accident currently active)
            if not accident_active and random.random() < accident_probability:
                accident_active = True
                accident_remaining = random.randint(
                    accident_duration_range[0], 
                    accident_duration_range[1]
                )
                accident_count += 1
            
            # Determine green light capacity
            if accident_active:
                capacity = green_capacity_accident
                accident_remaining -= 1
                if accident_remaining <= 0:
                    accident_active = False
            else:
                capacity = green_capacity_normal
            
            # Process vehicles through green light
            served = min(queue, capacity)
            queue -= served
            vehicles_served += served
            
            # Calculate waiting time for all vehicles in queue
            total_waiting_time += queue
            
            # Track maximum queue
            max_queue = max(max_queue, queue)
            
            # Record history
            queue_history.append(queue)
            throughput_history.append(served)
        
        # Calculate final metrics for this simulation
        avg_waiting_time = total_waiting_time / total_vehicles if total_vehicles > 0 else 0
        service_rate = vehicles_served / total_vehicles if total_vehicles > 0 else 0
        
        all_results.append({
            'max_queue': max_queue,
            'final_queue': queue,
            'avg_waiting_time': avg_waiting_time,
            'total_vehicles': total_vehicles,
            'vehicles_served': vehicles_served,
            'service_rate': service_rate,
            'accident_count': accident_count,
            'queue_history': queue_history,
            'throughput_history': throughput_history
        })
    
    # Aggregate results across all simulations
    max_queues = [r['max_queue'] for r in all_results]
    final_queues = [r['final_queue'] for r in all_results]
    avg_waiting_times = [r['avg_waiting_time'] for r in all_results]
    service_rates = [r['service_rate'] for r in all_results]
    accident_counts = [r['accident_count'] for r in all_results]
    
    # Calculate probabilities
    prob_severe_jam = np.mean([1 if q > 100 else 0 for q in max_queues])
    prob_moderate_jam = np.mean([1 if 50 < q <= 100 else 0 for q in max_queues])
    prob_light_traffic = np.mean([1 if q <= 50 else 0 for q in max_queues])
    
    return {
        # Queue metrics
        "avg_max_queue": float(np.mean(max_queues)),
        "min_max_queue": int(np.min(max_queues)),
        "max_max_queue": int(np.max(max_queues)),
        "std_max_queue": float(np.std(max_queues)),
        "median_max_queue": float(np.median(max_queues)),
        
        "avg_final_queue": float(np.mean(final_queues)),
        "max_final_queue": int(np.max(final_queues)),
        
        # Waiting time metrics
        "avg_waiting_time": float(np.mean(avg_waiting_times)),
        "min_waiting_time": float(np.min(avg_waiting_times)),
        "max_waiting_time": float(np.max(avg_waiting_times)),
        
        # Service metrics
        "avg_service_rate": float(np.mean(service_rates)),
        "min_service_rate": float(np.min(service_rates)),
        
        # Accident metrics
        "avg_accidents_per_hour": float(np.mean(accident_counts)),
        "max_accidents": int(np.max(accident_counts)),
        
        # Probabilities
        "prob_severe_jam": float(prob_severe_jam),
        "prob_moderate_jam": float(prob_moderate_jam),
        "prob_light_traffic": float(prob_light_traffic),
        
        # Percentiles
        "percentile_95": float(np.percentile(max_queues, 95)),
        "percentile_99": float(np.percentile(max_queues, 99)),
        
        # Raw data for plotting
        "all_max_queues": max_queues,
        "all_final_queues": final_queues,
        "sample_queue_history": all_results[0]['queue_history'],  # first simulation
        "sample_throughput_history": all_results[0]['throughput_history']
    }


def run_scenario_comparison(scenarios: List[Dict], simulations: int = 1000) -> Dict:
    """
    Compare multiple scenarios
    
    Example scenarios:
    [
        {"name": "Normal", "green_capacity": 8, "accident_prob": 0.05},
        {"name": "Optimized", "green_capacity": 12, "accident_prob": 0.02}
    ]
    """
    results = {}
    
    for scenario in scenarios:
        scenario_name = scenario.get('name', 'Unnamed')
        
        result = run_enhanced_simulation(
            rush_hour_rate=scenario.get('rush_hour_rate', [12, 25]),
            normal_rate=scenario.get('normal_rate', [5, 15]),
            rush_hour_minutes=scenario.get('rush_hour_minutes', 20),
            green_capacity_normal=scenario.get('green_capacity_normal', 8),
            green_capacity_accident=scenario.get('green_capacity_accident', 2),
            accident_probability=scenario.get('accident_probability', 0.05),
            accident_duration_range=scenario.get('accident_duration_range', [5, 15]),
            simulation_minutes=scenario.get('simulation_minutes', 60),
            simulations=simulations
        )
        
        results[scenario_name] = result
    
    return results


def calculate_confidence_intervals(data: List[float], confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculate confidence interval for data
    """
    mean = np.mean(data)
    std_error = np.std(data) / np.sqrt(len(data))
    
    # For 95% confidence, z-score is ~1.96
    z_score = 1.96 if confidence == 0.95 else 2.576  # 99%
    
    margin = z_score * std_error
    return (mean - margin, mean + margin)