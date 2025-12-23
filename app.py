from flask import Flask, render_template, request, jsonify, send_file
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
from src.export import (
    export_to_excel,
    export_comparison_to_excel,
    create_pdf_report,
    create_comparison_pdf
)
from src.history import history
from src.multi_intersection import (
    run_network_simulation,
    NETWORK_CONFIGS
)
from src.advanced_patterns import (
    RealWorldScenarios,
    run_advanced_simulation
)
import os

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
    
    traffic_level, level_config = get_traffic_level(result["avg_max_queue"])
    result["traffic_level"] = traffic_level
    result["traffic_level_color"] = level_config["color"]
    result["traffic_level_description"] = level_config["description"]
    
    ci_95 = calculate_confidence_intervals(result["all_max_queues"], 0.95)
    result["confidence_interval_95"] = {
        "lower": float(ci_95[0]),
        "upper": float(ci_95[1])
    }
    
    # Save to history
    history.save_simulation(data.get('scenario_name', 'custom'), result, config)
    
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
    
    scenarios = []
    for name in scenario_names:
        scenario = get_scenario(name)
        scenarios.append(scenario)
    
    results = run_scenario_comparison(scenarios, simulations)
    
    for scenario_name, result in results.items():
        traffic_level, level_config = get_traffic_level(result["avg_max_queue"])
        result["traffic_level"] = traffic_level
        result["traffic_level_color"] = level_config["color"]
    
    # Save comparison to history
    history.save_comparison(scenario_names, results, simulations)
    
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
    
    result["scenario_name"] = scenario["name"]
    result["scenario_description"] = scenario["description"]
    
    traffic_level, level_config = get_traffic_level(result["avg_max_queue"])
    result["traffic_level"] = traffic_level
    result["traffic_level_color"] = level_config["color"]
    result["traffic_level_description"] = level_config["description"]
    
    # Save to history
    history.save_simulation(scenario_name, result, scenario)
    
    return jsonify(result)

@app.route("/config", methods=["GET"])
def get_config():
    """Get default configuration"""
    return jsonify(DEFAULT_CONFIG)

# ============ ADVANCED FEATURES ============

@app.route("/export/excel", methods=["POST"])
def export_excel():
    """Export simulation results to Excel"""
    try:
        data = request.json
        result_data = data.get('result_data')
        scenario_name = data.get('scenario_name', 'simulation')
        
        filename = export_to_excel(result_data, scenario_name)
        return send_file(
            filename, 
            as_attachment=True,
            download_name=os.path.basename(filename),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/export/pdf", methods=["POST"])
def export_pdf():
    """Export simulation results to PDF"""
    try:
        data = request.json
        result_data = data.get('result_data')
        scenario_name = data.get('scenario_name', 'simulation')
        
        filename = create_pdf_report(result_data, scenario_name)
        return send_file(
            filename, 
            as_attachment=True,
            download_name=os.path.basename(filename),
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/export/comparison/excel", methods=["POST"])
def export_comparison_excel():
    """Export comparison results to Excel"""
    try:
        data = request.json
        comparison_data = data.get('comparison_data')
        
        filename = export_comparison_to_excel(comparison_data)
        return send_file(
            filename, 
            as_attachment=True,
            download_name=os.path.basename(filename),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/export/comparison/pdf", methods=["POST"])
def export_comparison_pdf():
    """Export comparison results to PDF"""
    try:
        data = request.json
        comparison_data = data.get('comparison_data')
        
        filename = create_comparison_pdf(comparison_data)
        return send_file(
            filename, 
            as_attachment=True,
            download_name=os.path.basename(filename),
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/history/recent", methods=["GET"])
def get_recent_history():
    """Get recent simulation history"""
    limit = request.args.get('limit', 10, type=int)
    results = history.get_recent_simulations(limit)
    return jsonify(results)

@app.route("/history/scenario/<scenario_name>", methods=["GET"])
def get_scenario_history(scenario_name):
    """Get history for specific scenario"""
    results = history.get_simulations_by_scenario(scenario_name)
    return jsonify(results)

@app.route("/history/statistics", methods=["GET"])
def get_history_statistics():
    """Get overall statistics"""
    stats = history.get_statistics_summary()
    return jsonify(stats)

@app.route("/history/trend/<scenario_name>", methods=["GET"])
def get_trend(scenario_name):
    """Get trend analysis for scenario"""
    days = request.args.get('days', 30, type=int)
    trend = history.get_trend_analysis(scenario_name, days)
    return jsonify(trend)

@app.route("/history/export", methods=["GET"])
def export_history():
    """Export full history to Excel"""
    filename = history.export_history_to_excel()
    return send_file(filename, as_attachment=True)

@app.route("/network/configs", methods=["GET"])
def get_network_configs():
    """Get available network configurations"""
    configs = {name: {
        'intersections': [i['id'] for i in config['intersections']],
        'num_intersections': len(config['intersections'])
    } for name, config in NETWORK_CONFIGS.items()}
    return jsonify(configs)

@app.route("/network/simulate/<config_name>", methods=["POST"])
def simulate_network(config_name):
    """Simulate multi-intersection network"""
    if config_name not in NETWORK_CONFIGS:
        return jsonify({"error": "Network config not found"}), 404
    
    data = request.json or {}
    simulations = data.get('simulations', 100)
    
    result = run_network_simulation(
        NETWORK_CONFIGS[config_name],
        simulations=simulations
    )
    
    return jsonify(result)

@app.route("/advanced/scenarios", methods=["GET"])
def get_advanced_scenarios():
    """Get list of advanced real-world scenarios"""
    scenarios = {
        'surabaya_morning': 'Surabaya Morning Commute',
        'rainy_season': 'Rainy Season Traffic',
        'weekend_mall': 'Weekend Mall Traffic',
        'concert_venue': 'Concert Venue Exit',
        'road_construction': 'Road Construction Detour'
    }
    return jsonify(scenarios)

@app.route("/advanced/simulate/<scenario_type>", methods=["POST"])
def simulate_advanced(scenario_type):
    """Run advanced pattern simulation"""
    data = request.json or {}
    simulations = data.get('simulations', 1000)
    simulation_minutes = data.get('simulation_minutes', 240)
    
    # Get scenario config
    scenario_map = {
        'surabaya_morning': RealWorldScenarios.surabaya_morning_commute,
        'rainy_season': RealWorldScenarios.rainy_season_traffic,
        'weekend_mall': RealWorldScenarios.weekend_mall_traffic,
        'concert_venue': RealWorldScenarios.concert_venue_exit,
        'road_construction': RealWorldScenarios.road_construction_detour
    }
    
    if scenario_type not in scenario_map:
        return jsonify({"error": "Scenario not found"}), 404
    
    scenario_config = scenario_map[scenario_type]()
    
    result = run_advanced_simulation(
        scenario_config,
        simulation_minutes=simulation_minutes,
        simulations=simulations
    )
    
    # Add traffic level
    traffic_level, level_config = get_traffic_level(result["avg_max_queue"])
    result["traffic_level"] = traffic_level
    result["traffic_level_color"] = level_config["color"]
    
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)