import numpy as np
import csv
import json
from datetime import datetime
from src.simulation import run_enhanced_simulation, run_scenario_comparison
from src.config import DEFAULT_CONFIG, SCENARIOS, get_all_scenario_names

def analyze_single_scenario(result: dict) -> dict:
    """Analyze results from a single simulation run"""
    
    analysis = {
        "summary": {
            "avg_max_queue": result["avg_max_queue"],
            "std_max_queue": result["std_max_queue"],
            "median_max_queue": result["median_max_queue"],
            "percentile_95": result["percentile_95"],
            "percentile_99": result["percentile_99"]
        },
        
        "waiting_metrics": {
            "avg_waiting_time": result["avg_waiting_time"],
            "max_waiting_time": result["max_waiting_time"]
        },
        
        "efficiency": {
            "avg_service_rate": result["avg_service_rate"],
            "min_service_rate": result["min_service_rate"]
        },
        
        "reliability": {
            "prob_severe_jam": result["prob_severe_jam"],
            "prob_moderate_jam": result["prob_moderate_jam"],
            "prob_light_traffic": result["prob_light_traffic"]
        },
        
        "incidents": {
            "avg_accidents_per_hour": result["avg_accidents_per_hour"],
            "max_accidents": result["max_accidents"]
        }
    }
    
    # Recommendations based on results
    recommendations = generate_recommendations(result)
    analysis["recommendations"] = recommendations
    
    return analysis

def generate_recommendations(result: dict) -> list:
    """Generate recommendations based on simulation results"""
    recommendations = []
    
    # Check queue length
    if result["avg_max_queue"] > 100:
        recommendations.append({
            "type": "critical",
            "issue": "Very high queue length",
            "suggestion": "Increase green light capacity or duration",
            "expected_improvement": "30-50% reduction in queue"
        })
    elif result["avg_max_queue"] > 60:
        recommendations.append({
            "type": "warning",
            "issue": "Moderate congestion",
            "suggestion": "Consider traffic light optimization",
            "expected_improvement": "15-25% improvement"
        })
    
    # Check service rate
    if result["avg_service_rate"] < 0.7:
        recommendations.append({
            "type": "critical",
            "issue": "Low service rate",
            "suggestion": "System cannot handle current demand",
            "expected_improvement": "Requires capacity expansion"
        })
    
    # Check waiting time
    if result["avg_waiting_time"] > 10:
        recommendations.append({
            "type": "warning",
            "issue": "High average waiting time",
            "suggestion": "Implement adaptive traffic light timing",
            "expected_improvement": "20-30% waiting time reduction"
        })
    
    # Check accident impact
    if result["avg_accidents_per_hour"] > 2:
        recommendations.append({
            "type": "info",
            "issue": "High accident frequency",
            "suggestion": "Improve road safety measures and emergency response",
            "expected_improvement": "Reduced accident duration and impact"
        })
    
    # Check severe jam probability
    if result["prob_severe_jam"] > 0.2:
        recommendations.append({
            "type": "critical",
            "issue": "High probability of severe congestion (>20%)",
            "suggestion": "Immediate intervention needed - consider alternative routes or timing changes",
            "expected_improvement": "Major congestion reduction"
        })
    
    return recommendations

def compare_scenarios_analysis(comparison_results: dict) -> dict:
    """Analyze comparison between multiple scenarios"""
    
    comparison = {
        "best_scenario": None,
        "worst_scenario": None,
        "rankings": {},
        "improvements": {}
    }
    
    # Rank scenarios by avg_max_queue (lower is better)
    ranked = sorted(
        comparison_results.items(), 
        key=lambda x: x[1]["avg_max_queue"]
    )
    
    comparison["best_scenario"] = ranked[0][0]
    comparison["worst_scenario"] = ranked[-1][0]
    
    # Calculate rankings
    for rank, (scenario_name, _) in enumerate(ranked, 1):
        comparison["rankings"][scenario_name] = rank
    
    # Calculate improvements compared to baseline
    if "Baseline (Current)" in comparison_results:
        baseline = comparison_results["Baseline (Current)"]
        
        for scenario_name, result in comparison_results.items():
            if scenario_name != "Baseline (Current)":
                improvement = {
                    "queue_reduction_pct": 
                        ((baseline["avg_max_queue"] - result["avg_max_queue"]) / 
                         baseline["avg_max_queue"] * 100),
                    
                    "waiting_time_reduction_pct": 
                        ((baseline["avg_waiting_time"] - result["avg_waiting_time"]) / 
                         baseline["avg_waiting_time"] * 100),
                    
                    "service_rate_improvement_pct": 
                        ((result["avg_service_rate"] - baseline["avg_service_rate"]) / 
                         baseline["avg_service_rate"] * 100)
                }
                
                comparison["improvements"][scenario_name] = improvement
    
    return comparison

def save_analysis_to_json(analysis: dict, path: str = "results/analysis.json"):
    """Save analysis results to JSON file"""
    analysis["timestamp"] = datetime.now().isoformat()
    
    with open(path, "w") as f:
        json.dump(analysis, f, indent=2)
    
    print(f"Analysis saved to {path}")

def save_comparison_to_csv(comparison_results: dict, path: str = "results/comparison.csv"):
    """Save scenario comparison to CSV"""
    
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            "Scenario",
            "Avg Max Queue",
            "Std Dev",
            "Avg Waiting Time",
            "Service Rate",
            "Prob Severe Jam",
            "Avg Accidents/Hour"
        ])
        
        # Data rows
        for scenario_name, result in comparison_results.items():
            writer.writerow([
                scenario_name,
                f"{result['avg_max_queue']:.2f}",
                f"{result['std_max_queue']:.2f}",
                f"{result['avg_waiting_time']:.2f}",
                f"{result['avg_service_rate']:.2%}",
                f"{result['prob_severe_jam']:.2%}",
                f"{result['avg_accidents_per_hour']:.2f}"
            ])
    
    print(f"Comparison saved to {path}")

def generate_summary_report(comparison_results: dict) -> str:
    """Generate human-readable summary report"""
    
    comparison = compare_scenarios_analysis(comparison_results)
    
    report = []
    report.append("=" * 60)
    report.append("TRAFFIC SIMULATION ANALYSIS REPORT")
    report.append("=" * 60)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # Best and worst scenarios
    report.append(f"🏆 BEST SCENARIO: {comparison['best_scenario']}")
    report.append(f"⚠️  WORST SCENARIO: {comparison['worst_scenario']}")
    report.append("")
    
    # Rankings
    report.append("SCENARIO RANKINGS (by avg queue length):")
    for scenario, rank in comparison['rankings'].items():
        result = comparison_results[scenario]
        report.append(f"  {rank}. {scenario}: {result['avg_max_queue']:.1f} vehicles")
    report.append("")
    
    # Improvements over baseline
    if comparison['improvements']:
        report.append("IMPROVEMENTS vs BASELINE:")
        for scenario, improvement in comparison['improvements'].items():
            report.append(f"\n  {scenario}:")
            report.append(f"    - Queue reduction: {improvement['queue_reduction_pct']:.1f}%")
            report.append(f"    - Waiting time reduction: {improvement['waiting_time_reduction_pct']:.1f}%")
            report.append(f"    - Service rate improvement: {improvement['service_rate_improvement_pct']:.1f}%")
    
    report.append("")
    report.append("=" * 60)
    
    return "\n".join(report)

def run_full_analysis(simulations: int = 1000):
    """Run complete analysis of all scenarios"""
    
    print("Running full scenario analysis...")
    print(f"Simulations per scenario: {simulations}")
    print("")
    
    # Get all scenarios
    scenario_names = get_all_scenario_names()
    scenarios = [SCENARIOS[name] for name in scenario_names]
    
    # Run comparison
    print("Running simulations...")
    comparison_results = run_scenario_comparison(scenarios, simulations)
    
    # Analyze
    print("Analyzing results...")
    comparison_analysis = compare_scenarios_analysis(comparison_results)
    
    # Generate report
    report = generate_summary_report(comparison_results)
    print(report)
    
    # Save results
    print("\nSaving results...")
    save_comparison_to_csv(comparison_results, "results/comparison.csv")
    
    full_analysis = {
        "comparison_results": comparison_results,
        "comparison_analysis": comparison_analysis
    }
    save_analysis_to_json(full_analysis, "results/full_analysis.json")
    
    print("\n✅ Analysis complete!")
    return full_analysis

if __name__ == "__main__":
    run_full_analysis(simulations=1000)