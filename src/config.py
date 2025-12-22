# Default Configuration
DEFAULT_CONFIG = {
    "rush_hour_rate": [12, 25],
    "normal_rate": [5, 15],
    "rush_hour_minutes": 20,
    "green_capacity_normal": 8,
    "green_capacity_accident": 2,
    "accident_probability": 0.05,
    "accident_duration_range": [5, 15],
    "simulation_minutes": 60,
    "simulations": 1000
}

# Preset Scenarios untuk comparison
SCENARIOS = {
    "baseline": {
        "name": "Baseline (Current)",
        "description": "Current traffic light configuration",
        "rush_hour_rate": [12, 25],
        "normal_rate": [5, 15],
        "rush_hour_minutes": 20,
        "green_capacity_normal": 8,
        "green_capacity_accident": 2,
        "accident_probability": 0.05,
        "accident_duration_range": [5, 15],
        "simulation_minutes": 60
    },
    
    "optimized": {
        "name": "Optimized Traffic Light",
        "description": "Longer green time, better capacity",
        "rush_hour_rate": [12, 25],
        "normal_rate": [5, 15],
        "rush_hour_minutes": 20,
        "green_capacity_normal": 12,  # Increased capacity
        "green_capacity_accident": 3,
        "accident_probability": 0.05,
        "accident_duration_range": [5, 15],
        "simulation_minutes": 60
    },
    
    "heavy_traffic": {
        "name": "Heavy Traffic Day",
        "description": "Extended rush hour with more vehicles",
        "rush_hour_rate": [20, 35],  # Much higher traffic
        "normal_rate": [8, 18],
        "rush_hour_minutes": 40,  # Longer rush hour
        "green_capacity_normal": 8,
        "green_capacity_accident": 2,
        "accident_probability": 0.08,  # More accidents
        "accident_duration_range": [8, 20],
        "simulation_minutes": 60
    },
    
    "accident_prone": {
        "name": "Accident-Prone Area",
        "description": "High accident rate scenario",
        "rush_hour_rate": [12, 25],
        "normal_rate": [5, 15],
        "rush_hour_minutes": 20,
        "green_capacity_normal": 8,
        "green_capacity_accident": 2,
        "accident_probability": 0.15,  # 15% accident chance
        "accident_duration_range": [10, 25],  # Longer accidents
        "simulation_minutes": 60
    },
    
    "ideal_conditions": {
        "name": "Ideal Conditions",
        "description": "Best case scenario - light traffic, no accidents",
        "rush_hour_rate": [8, 15],
        "normal_rate": [3, 10],
        "rush_hour_minutes": 15,
        "green_capacity_normal": 10,
        "green_capacity_accident": 5,
        "accident_probability": 0.01,  # Very rare accidents
        "accident_duration_range": [3, 8],
        "simulation_minutes": 60
    },
    
    "weekend": {
        "name": "Weekend Traffic",
        "description": "Light traffic throughout",
        "rush_hour_rate": [5, 12],
        "normal_rate": [2, 8],
        "rush_hour_minutes": 10,
        "green_capacity_normal": 8,
        "green_capacity_accident": 2,
        "accident_probability": 0.03,
        "accident_duration_range": [5, 15],
        "simulation_minutes": 60
    }
}

# Traffic level classifications
TRAFFIC_LEVELS = {
    "light": {
        "max_queue": 30,
        "color": "#4CAF50",  # Green
        "description": "Traffic flowing smoothly"
    },
    "moderate": {
        "max_queue": 60,
        "color": "#FFC107",  # Yellow
        "description": "Some congestion, manageable"
    },
    "heavy": {
        "max_queue": 100,
        "color": "#FF9800",  # Orange
        "description": "Heavy congestion, slow movement"
    },
    "severe": {
        "max_queue": float('inf'),
        "color": "#F44336",  # Red
        "description": "Severe congestion, major delays"
    }
}

# Metrics thresholds for alerts
ALERT_THRESHOLDS = {
    "queue_critical": 120,
    "waiting_time_high": 15,  # minutes
    "service_rate_low": 0.7,  # 70%
    "accident_rate_high": 3  # per hour
}

def get_scenario(scenario_name: str):
    """Get scenario configuration by name"""
    return SCENARIOS.get(scenario_name, SCENARIOS["baseline"])

def get_traffic_level(queue_size: int):
    """Determine traffic level based on queue size"""
    for level, config in TRAFFIC_LEVELS.items():
        if queue_size <= config["max_queue"]:
            return level, config
    return "severe", TRAFFIC_LEVELS["severe"]

def get_all_scenario_names():
    """Get list of all available scenario names"""
    return list(SCENARIOS.keys())