import matplotlib.pyplot as plt
import numpy as np
import os
from src.simulation import run_enhanced_simulation, run_scenario_comparison
from src.config import DEFAULT_CONFIG, SCENARIOS, get_all_scenario_names

# Set matplotlib style
plt.style.use('seaborn-v0_8-darkgrid')

def ensure_results_dir():
    """Ensure results directory exists"""
    os.makedirs("results/figures", exist_ok=True)

def plot_histogram(data, title, xlabel, save_path, color='#2196F3'):
    """Plot histogram of data"""
    plt.figure(figsize=(10, 6))
    
    plt.hist(data, bins=30, edgecolor='black', alpha=0.7, color=color)
    plt.title(title, fontsize=16, fontweight='bold')
    plt.xlabel(xlabel, fontsize=12)
    plt.ylabel("Frequency", fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # Add statistics text
    mean_val = np.mean(data)
    median_val = np.median(data)
    std_val = np.std(data)
    
    stats_text = f'Mean: {mean_val:.1f}\nMedian: {median_val:.1f}\nStd Dev: {std_val:.1f}'
    plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes,
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Saved: {save_path}")

def plot_time_series(data, title, save_path):
    """Plot time series data"""
    plt.figure(figsize=(12, 6))
    
    plt.plot(range(1, len(data) + 1), data, linewidth=2, color='#FF5722', alpha=0.8)
    plt.fill_between(range(1, len(data) + 1), data, alpha=0.3, color='#FF5722')
    
    plt.title(title, fontsize=16, fontweight='bold')
    plt.xlabel("Time (minutes)", fontsize=12)
    plt.ylabel("Queue Length (vehicles)", fontsize=12)
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Saved: {save_path}")

def plot_comparison_bar(scenarios_data, metric_key, metric_name, save_path):
    """Create bar chart comparing scenarios"""
    scenarios = list(scenarios_data.keys())
    values = [scenarios_data[s][metric_key] for s in scenarios]
    
    plt.figure(figsize=(12, 6))
    
    colors = ['#4CAF50' if v == min(values) else '#F44336' if v == max(values) else '#2196F3' 
              for v in values]
    
    bars = plt.bar(scenarios, values, color=colors, alpha=0.7, edgecolor='black')
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom', fontweight='bold')
    
    plt.title(f'Scenario Comparison: {metric_name}', fontsize=16, fontweight='bold')
    plt.xlabel('Scenario', fontsize=12)
    plt.ylabel(metric_name, fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Saved: {save_path}")

def plot_probability_comparison(scenarios_data, save_path):
    """Create stacked bar chart for traffic probabilities"""
    scenarios = list(scenarios_data.keys())
    
    light = [scenarios_data[s]['prob_light_traffic'] * 100 for s in scenarios]
    moderate = [scenarios_data[s]['prob_moderate_jam'] * 100 for s in scenarios]
    severe = [scenarios_data[s]['prob_severe_jam'] * 100 for s in scenarios]
    
    plt.figure(figsize=(12, 6))
    
    x = np.arange(len(scenarios))
    width = 0.6
    
    plt.bar(x, light, width, label='Light Traffic', color='#4CAF50', alpha=0.8)
    plt.bar(x, moderate, width, bottom=light, label='Moderate', color='#FFC107', alpha=0.8)
    plt.bar(x, severe, width, bottom=np.array(light) + np.array(moderate), 
            label='Severe Jam', color='#F44336', alpha=0.8)
    
    plt.xlabel('Scenario', fontsize=12)
    plt.ylabel('Probability (%)', fontsize=12)
    plt.title('Traffic Level Probabilities by Scenario', fontsize=16, fontweight='bold')
    plt.xticks(x, scenarios, rotation=45, ha='right')
    plt.legend()
    plt.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Saved: {save_path}")

def plot_box_plot(scenarios_data, save_path):
    """Create box plot comparing queue distributions"""
    scenarios = list(scenarios_data.keys())
    data_lists = [scenarios_data[s]['all_max_queues'] for s in scenarios]
    
    plt.figure(figsize=(12, 6))
    
    bp = plt.boxplot(data_lists, labels=scenarios, patch_artist=True)
    
    # Color boxes
    colors = ['#2196F3', '#4CAF50', '#FF9800', '#F44336', '#9C27B0', '#00BCD4']
    for patch, color in zip(bp['boxes'], colors[:len(scenarios)]):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    plt.xlabel('Scenario', fontsize=12)
    plt.ylabel('Maximum Queue Length (vehicles)', fontsize=12)
    plt.title('Queue Length Distribution Comparison', fontsize=16, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Saved: {save_path}")

def generate_all_plots(simulations=1000):
    """Generate all visualization plots"""
    ensure_results_dir()
    
    print("=" * 60)
    print("GENERATING VISUALIZATION PLOTS")
    print("=" * 60)
    print(f"Simulations per scenario: {simulations}\n")
    
    # Run baseline simulation
    print("Running baseline simulation...")
    baseline_result = run_enhanced_simulation(
        **DEFAULT_CONFIG,
        simulations=simulations
    )
    
    # Plot baseline results
    print("\nGenerating baseline plots...")
    plot_histogram(
        baseline_result['all_max_queues'],
        "Distribution of Maximum Queue Length (Baseline)",
        "Queue Length (vehicles)",
        "results/figures/baseline_histogram.png"
    )
    
    plot_time_series(
        baseline_result['sample_queue_history'],
        "Queue Evolution Over Time (Sample Simulation)",
        "results/figures/baseline_timeseries.png"
    )
    
    # Run scenario comparison
    print("\nRunning scenario comparison...")
    scenario_names = get_all_scenario_names()
    scenarios = [SCENARIOS[name] for name in scenario_names]
    comparison_results = run_scenario_comparison(scenarios, simulations)
    
    # Plot comparisons
    print("\nGenerating comparison plots...")
    plot_comparison_bar(
        comparison_results,
        'avg_max_queue',
        'Average Maximum Queue Length (vehicles)',
        'results/figures/comparison_queue.png'
    )
    
    plot_comparison_bar(
        comparison_results,
        'avg_waiting_time',
        'Average Waiting Time (minutes)',
        'results/figures/comparison_waiting.png'
    )
    
    plot_comparison_bar(
        comparison_results,
        'avg_service_rate',
        'Average Service Rate',
        'results/figures/comparison_service.png'
    )
    
    plot_probability_comparison(
        comparison_results,
        'results/figures/comparison_probabilities.png'
    )
    
    plot_box_plot(
        comparison_results,
        'results/figures/comparison_boxplot.png'
    )
    
    print("\n" + "=" * 60)
    print("✅ ALL PLOTS GENERATED SUCCESSFULLY!")
    print("=" * 60)
    print(f"Location: results/figures/")
    print(f"Total files: 7 PNG images")

def plot_single_scenario(scenario_name, simulations=1000):
    """Generate plots for a single scenario"""
    ensure_results_dir()
    
    print(f"Generating plots for scenario: {scenario_name}")
    
    scenario = SCENARIOS.get(scenario_name)
    if not scenario:
        print(f"Error: Scenario '{scenario_name}' not found")
        return
    
    result = run_enhanced_simulation(
        rush_hour_rate=scenario['rush_hour_rate'],
        normal_rate=scenario['normal_rate'],
        rush_hour_minutes=scenario['rush_hour_minutes'],
        green_capacity_normal=scenario['green_capacity_normal'],
        green_capacity_accident=scenario['green_capacity_accident'],
        accident_probability=scenario['accident_probability'],
        accident_duration_range=scenario['accident_duration_range'],
        simulation_minutes=scenario['simulation_minutes'],
        simulations=simulations
    )
    
    plot_histogram(
        result['all_max_queues'],
        f"Queue Distribution - {scenario['name']}",
        "Queue Length (vehicles)",
        f"results/figures/{scenario_name}_histogram.png"
    )
    
    plot_time_series(
        result['sample_queue_history'],
        f"Queue Over Time - {scenario['name']}",
        f"results/figures/{scenario_name}_timeseries.png"
    )
    
    print(f"✅ Plots saved for {scenario_name}")

if __name__ == "__main__":
    # Generate all plots
    generate_all_plots(simulations=1000)
    
    # Optional: Generate for specific scenario
    # plot_single_scenario('heavy_traffic', simulations=1000)