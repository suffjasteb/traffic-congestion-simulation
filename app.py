from flask import Flask, render_template, request, jsonify
from src.simulation import (
    run_simulation, 
    run_enhanced_simulation, 
    run_scenario_comparison,
    calculate_confidence_intervals
)
from src.config import (
    DEFAULT_CONFIG, 
    SCENARIOS, 
    get_scenario, 
    get_all_scenario_names,
    get_traffic_level
)

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/simulate", methods=["POST"])
def simulate():
    """Basic simulation endpoint - backward compatible"""
    data = request.json

    result = run_simulation(
        arrival_rate=data["arrival_rate"],
        green_capacity=data["green_capacity"],
        cycles=data["cycles"],
        simulations=data.get("simulations", 1000)
    )

    return jsonify(result)

@app.route("/simulate/enhanced", methods=["POST"])
def simulate_enhanced():
    """Enhanced simulation with rush hour and accidents"""
    data = request.json
    
    # Use defaults if not provided
    config = DEFAULT_CONFIG.copy()
    config.update(data)
    
    result = run_enhanced_simulation(
        rush_hour_rate=config["rush_hour_rate"],
        normal_rate=config["normal_rate"],
        rush_hour_minutes=config["rush_hour_minutes"],
        green_capacity_normal=config["green_capacity_normal"],
        green_capacity_accident=config["green_capacity_accident"],
        accident_probability=config["accident_probability"],
        accident_duration_range=config["accident_duration_range"],
        simulation_minutes=config["simulation_minutes"],
        simulations=config["simulations"]
    )
    
    # Add traffic level classification
    traffic_level, level_config = get_traffic_level(result["avg_max_queue"])
    result["traffic_level"] = traffic_level
    result["traffic_level_color"] = level_config["color"]
    result["traffic_level_description"] = level_config["description"]
    
    # Calculate confidence intervals
    ci_95 = calculate_confidence_intervals(result["all_max_queues"], 0.95)
    result["confidence_interval_95"] = {
        "lower": float(ci_95[0]),
        "upper": float(ci_95[1])
    }
    
    return jsonify(result)

@app.route("/scenarios", methods=["GET"])
def get_scenarios():
    """Get all available scenarios"""
    return jsonify({
        "scenarios": get_all_scenario_names(),
        "details": SCENARIOS
    })

@app.route("/scenarios/compare", methods=["POST"])
def compare_scenarios():
    """Compare multiple scenarios"""
    data = request.json
    scenario_names = data.get("scenarios", ["baseline", "optimized"])
    simulations = data.get("simulations", 1000)
    
    # Build scenario list
    scenarios = []
    for name in scenario_names:
        scenario = get_scenario(name)
        scenarios.append(scenario)
    
    # Run comparison
    results = run_scenario_comparison(scenarios, simulations)
    
    # Add traffic levels for each scenario
    for scenario_name, result in results.items():
        traffic_level, level_config = get_traffic_level(result["avg_max_queue"])
        result["traffic_level"] = traffic_level
        result["traffic_level_color"] = level_config["color"]
    
    return jsonify(results)

@app.route("/scenarios/<scenario_name>", methods=["POST"])
def simulate_scenario(scenario_name):
    """Run simulation for a specific preset scenario"""
    scenario = get_scenario(scenario_name)
    
    if not scenario:
        return jsonify({"error": "Scenario not found"}), 404
    
    simulations = request.json.get("simulations", 1000) if request.json else 1000
    
    result = run_enhanced_simulation(
        rush_hour_rate=scenario["rush_hour_rate"],
        normal_rate=scenario["normal_rate"],
        rush_hour_minutes=scenario["rush_hour_minutes"],
        green_capacity_normal=scenario["green_capacity_normal"],
        green_capacity_accident=scenario["green_capacity_accident"],
        accident_probability=scenario["accident_probability"],
        accident_duration_range=scenario["accident_duration_range"],
        simulation_minutes=scenario["simulation_minutes"],
        simulations=simulations
    )
    
    # Add scenario info
    result["scenario_name"] = scenario["name"]
    result["scenario_description"] = scenario["description"]
    
    # Add traffic level
    traffic_level, level_config = get_traffic_level(result["avg_max_queue"])
    result["traffic_level"] = traffic_level
    result["traffic_level_color"] = level_config["color"]
    result["traffic_level_description"] = level_config["description"]
    
    return jsonify(result)

@app.route("/config", methods=["GET"])
def get_config():
    """Get default configuration"""
    return jsonify(DEFAULT_CONFIG)

if __name__ == "__main__":
    app.run(debug=True)