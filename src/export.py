import pandas as pd
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import os

def ensure_export_dir():
    """Ensure export directory exists"""
    os.makedirs("results/exports", exist_ok=True)

def export_to_excel(result_data, scenario_name="simulation", filename=None):
    """
    Export simulation results to Excel file with multiple sheets
    """
    ensure_export_dir()
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"results/exports/{scenario_name}_{timestamp}.xlsx"
    
    try:
        # Prepare data first
        summary_data = {
            'Metric': [
                'Average Maximum Queue',
                'Minimum Maximum Queue',
                'Maximum Maximum Queue',
                'Standard Deviation',
                'Median Maximum Queue',
                '95th Percentile',
                '99th Percentile',
                'Average Final Queue',
                'Average Waiting Time',
                'Max Waiting Time',
                'Average Service Rate',
                'Minimum Service Rate',
                'Average Accidents per Hour',
                'Probability Severe Jam',
                'Probability Moderate Jam',
                'Probability Light Traffic'
            ],
            'Value': [
                result_data.get('avg_max_queue', 0),
                result_data.get('min_max_queue', 0),
                result_data.get('max_max_queue', 0),
                result_data.get('std_max_queue', 0),
                result_data.get('median_max_queue', 0),
                result_data.get('percentile_95', 0),
                result_data.get('percentile_99', 0),
                result_data.get('avg_final_queue', 0),
                result_data.get('avg_waiting_time', 0),
                result_data.get('max_waiting_time', 0),
                result_data.get('avg_service_rate', 0),
                result_data.get('min_service_rate', 0),
                result_data.get('avg_accidents_per_hour', 0),
                result_data.get('prob_severe_jam', 0),
                result_data.get('prob_moderate_jam', 0),
                result_data.get('prob_light_traffic', 0)
            ],
            'Unit': [
                'vehicles', 'vehicles', 'vehicles', 'vehicles', 'vehicles',
                'vehicles', 'vehicles', 'vehicles', 'minutes', 'minutes',
                'ratio', 'ratio', 'count', 'probability', 'probability', 'probability'
            ]
        }
        
        df_summary = pd.DataFrame(summary_data)
        
        # Max queues data
        max_queues = result_data.get('all_max_queues', [])
        if max_queues:
            df_max_queues = pd.DataFrame({
                'Simulation_Run': range(1, len(max_queues) + 1),
                'Max_Queue_Length': max_queues
            })
        else:
            df_max_queues = pd.DataFrame({'Message': ['No queue data available']})
        
        # Queue history
        queue_history = result_data.get('sample_queue_history', [])
        if queue_history:
            df_history = pd.DataFrame({
                'Minute': range(1, len(queue_history) + 1),
                'Queue_Length': queue_history
            })
        else:
            df_history = pd.DataFrame({'Message': ['No history data available']})
        
        # Throughput history
        throughput_history = result_data.get('sample_throughput_history', [])
        if throughput_history:
            df_throughput = pd.DataFrame({
                'Minute': range(1, len(throughput_history) + 1),
                'Vehicles_Served': throughput_history
            })
        else:
            df_throughput = pd.DataFrame({'Message': ['No throughput data available']})
        
        # Distribution analysis
        if max_queues and len(max_queues) > 0:
            bins = np.linspace(min(max_queues), max(max_queues), min(21, len(max_queues)))
            hist, bin_edges = np.histogram(max_queues, bins=bins)
            
            df_dist = pd.DataFrame({
                'Bin_Start': bin_edges[:-1],
                'Bin_End': bin_edges[1:],
                'Frequency': hist,
                'Percentage': (hist / len(max_queues)) * 100
            })
        else:
            df_dist = pd.DataFrame({'Message': ['No distribution data available']})
        
        # Write to Excel with error handling
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df_summary.to_excel(writer, sheet_name='Summary', index=False)
            df_max_queues.to_excel(writer, sheet_name='Max_Queue_Data', index=False)
            df_history.to_excel(writer, sheet_name='Queue_History', index=False)
            df_throughput.to_excel(writer, sheet_name='Throughput', index=False)
            df_dist.to_excel(writer, sheet_name='Distribution', index=False)
        
        print(f"✅ Excel exported: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Excel export error: {str(e)}")
        # Create simple fallback file
        fallback_filename = f"results/exports/{scenario_name}_simple_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df_summary.to_excel(fallback_filename, index=False)
        print(f"✅ Fallback Excel created: {fallback_filename}")
        return fallback_filename

def export_comparison_to_excel(comparison_data, filename=None):
    """Export scenario comparison to Excel"""
    ensure_export_dir()
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"results/exports/comparison_{timestamp}.xlsx"
    
    try:
        # Prepare comparison dataframe
        comparison_list = []
        for scenario_name, result in comparison_data.items():
            comparison_list.append({
                'Scenario': scenario_name,
                'Avg_Max_Queue': result.get('avg_max_queue', 0),
                'Std_Dev': result.get('std_max_queue', 0),
                'Median_Queue': result.get('median_max_queue', 0),
                'Percentile_95': result.get('percentile_95', 0),
                'Avg_Waiting_Time': result.get('avg_waiting_time', 0),
                'Service_Rate': result.get('avg_service_rate', 0),
                'Prob_Severe_Jam': result.get('prob_severe_jam', 0),
                'Prob_Moderate_Jam': result.get('prob_moderate_jam', 0),
                'Prob_Light_Traffic': result.get('prob_light_traffic', 0),
                'Avg_Accidents': result.get('avg_accidents_per_hour', 0)
            })
        
        df_comparison = pd.DataFrame(comparison_list)
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df_comparison.to_excel(writer, sheet_name='Comparison', index=False)
            
            # Add ranking sheet
            if len(df_comparison) > 0:
                df_ranked = df_comparison.sort_values('Avg_Max_Queue')
                df_ranked['Rank'] = range(1, len(df_ranked) + 1)
                df_ranked.to_excel(writer, sheet_name='Rankings', index=False)
        
        print(f"✅ Comparison Excel exported: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Comparison export error: {str(e)}")
        raise

def create_pdf_report(result_data, scenario_name="simulation", filename=None):
    """
    Create comprehensive PDF report with charts and statistics
    """
    ensure_export_dir()
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"results/exports/{scenario_name}_report_{timestamp}.pdf"
    
    try:
        with PdfPages(filename) as pdf:
            
            # Page 1: Title and Summary
            fig = plt.figure(figsize=(8.5, 11))
            fig.suptitle(f'Traffic Simulation Report\n{scenario_name}', 
                         fontsize=18, fontweight='bold', y=0.95)
            
            # Add timestamp
            plt.text(0.5, 0.88, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                    ha='center', fontsize=11, style='italic', transform=fig.transFigure)
            
            # Summary statistics table
            summary_text = f"""
KEY METRICS SUMMARY
{'=' * 50}

Queue Analysis:
  • Avg Maximum Queue: {result_data.get('avg_max_queue', 0):.1f} vehicles
  • Std Deviation: {result_data.get('std_max_queue', 0):.1f} vehicles
  • Median: {result_data.get('median_max_queue', 0):.1f} vehicles
  • 95th Percentile: {result_data.get('percentile_95', 0):.1f} vehicles

Waiting Time Analysis:
  • Avg Waiting Time: {result_data.get('avg_waiting_time', 0):.2f} min
  • Max Waiting Time: {result_data.get('max_waiting_time', 0):.2f} min

System Performance:
  • Avg Service Rate: {result_data.get('avg_service_rate', 0)*100:.1f}%
  • Min Service Rate: {result_data.get('min_service_rate', 0)*100:.1f}%

Traffic Probabilities:
  • Light Traffic: {result_data.get('prob_light_traffic', 0)*100:.1f}%
  • Moderate Jam: {result_data.get('prob_moderate_jam', 0)*100:.1f}%
  • Severe Jam: {result_data.get('prob_severe_jam', 0)*100:.1f}%

Incidents:
  • Avg Accidents/Hour: {result_data.get('avg_accidents_per_hour', 0):.2f}
            """
            
            plt.text(0.1, 0.75, summary_text, fontsize=9, family='monospace',
                    verticalalignment='top', transform=fig.transFigure)
            
            plt.axis('off')
            pdf.savefig(fig, bbox_inches='tight')
            plt.close()
            
            # Page 2: Queue Distribution Histogram
            all_max_queues = result_data.get('all_max_queues', [])
            if all_max_queues and len(all_max_queues) > 0:
                fig, ax = plt.subplots(figsize=(8.5, 6))
                
                ax.hist(all_max_queues, bins=min(30, len(all_max_queues)//10 + 1), 
                       edgecolor='black', alpha=0.7, color='#2196F3')
                ax.set_title('Distribution of Maximum Queue Length', 
                            fontsize=14, fontweight='bold', pad=15)
                ax.set_xlabel('Queue Length (vehicles)', fontsize=11)
                ax.set_ylabel('Frequency', fontsize=11)
                ax.grid(True, alpha=0.3)
                
                # Add statistics box
                stats_text = f'Mean: {np.mean(all_max_queues):.1f}\n'
                stats_text += f'Median: {np.median(all_max_queues):.1f}\n'
                stats_text += f'Std: {np.std(all_max_queues):.1f}'
                
                ax.text(0.98, 0.97, stats_text, transform=ax.transAxes,
                       verticalalignment='top', horizontalalignment='right',
                       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
                       fontsize=9)
                
                plt.tight_layout()
                pdf.savefig(fig, bbox_inches='tight')
                plt.close()
            
            # Page 3: Time Series (if available)
            queue_history = result_data.get('sample_queue_history', [])
            if queue_history and len(queue_history) > 0:
                fig, ax = plt.subplots(figsize=(8.5, 6))
                
                time = range(1, len(queue_history) + 1)
                ax.plot(time, queue_history, linewidth=2, color='#FF5722', alpha=0.8)
                ax.fill_between(time, queue_history, alpha=0.3, color='#FF5722')
                
                ax.set_title('Queue Length Over Time (Sample)', 
                           fontsize=14, fontweight='bold', pad=15)
                ax.set_xlabel('Time (minutes)', fontsize=11)
                ax.set_ylabel('Queue Length (vehicles)', fontsize=11)
                ax.grid(True, alpha=0.3)
                
                plt.tight_layout()
                pdf.savefig(fig, bbox_inches='tight')
                plt.close()
            
            # Metadata
            d = pdf.infodict()
            d['Title'] = f'Traffic Simulation Report - {scenario_name}'
            d['Author'] = 'Monte Carlo Traffic Simulator'
            d['Subject'] = 'Traffic Analysis Report'
            d['CreationDate'] = datetime.now()
        
        print(f"✅ PDF report created: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ PDF creation error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

def create_comparison_pdf(comparison_data, filename=None):
    """Create PDF report comparing multiple scenarios"""
    ensure_export_dir()
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"results/exports/comparison_report_{timestamp}.pdf"
    
    try:
        scenarios = list(comparison_data.keys())
        
        with PdfPages(filename) as pdf:
            
            # Page 1: Comparison Bar Charts
            fig, axes = plt.subplots(2, 2, figsize=(11, 8.5))
            fig.suptitle('Scenario Comparison Report', fontsize=16, fontweight='bold')
            
            # Average Max Queue
            avg_queues = [comparison_data[s].get('avg_max_queue', 0) for s in scenarios]
            axes[0, 0].bar(range(len(scenarios)), avg_queues, 
                          color='#2196F3', alpha=0.7, edgecolor='black')
            axes[0, 0].set_xticks(range(len(scenarios)))
            axes[0, 0].set_xticklabels(scenarios, rotation=45, ha='right', fontsize=8)
            axes[0, 0].set_title('Average Maximum Queue', fontweight='bold', fontsize=10)
            axes[0, 0].set_ylabel('Vehicles', fontsize=9)
            axes[0, 0].grid(True, alpha=0.3, axis='y')
            
            # Waiting Time
            wait_times = [comparison_data[s].get('avg_waiting_time', 0) for s in scenarios]
            axes[0, 1].bar(range(len(scenarios)), wait_times, 
                          color='#FF5722', alpha=0.7, edgecolor='black')
            axes[0, 1].set_xticks(range(len(scenarios)))
            axes[0, 1].set_xticklabels(scenarios, rotation=45, ha='right', fontsize=8)
            axes[0, 1].set_title('Average Waiting Time', fontweight='bold', fontsize=10)
            axes[0, 1].set_ylabel('Minutes', fontsize=9)
            axes[0, 1].grid(True, alpha=0.3, axis='y')
            
            # Service Rate
            service_rates = [comparison_data[s].get('avg_service_rate', 0)*100 for s in scenarios]
            axes[1, 0].bar(range(len(scenarios)), service_rates, 
                          color='#4CAF50', alpha=0.7, edgecolor='black')
            axes[1, 0].set_xticks(range(len(scenarios)))
            axes[1, 0].set_xticklabels(scenarios, rotation=45, ha='right', fontsize=8)
            axes[1, 0].set_title('Average Service Rate', fontweight='bold', fontsize=10)
            axes[1, 0].set_ylabel('Percentage (%)', fontsize=9)
            axes[1, 0].grid(True, alpha=0.3, axis='y')
            
            # Severe Jam Probability
            severe_probs = [comparison_data[s].get('prob_severe_jam', 0)*100 for s in scenarios]
            axes[1, 1].bar(range(len(scenarios)), severe_probs, 
                          color='#F44336', alpha=0.7, edgecolor='black')
            axes[1, 1].set_xticks(range(len(scenarios)))
            axes[1, 1].set_xticklabels(scenarios, rotation=45, ha='right', fontsize=8)
            axes[1, 1].set_title('Severe Jam Probability', fontweight='bold', fontsize=10)
            axes[1, 1].set_ylabel('Percentage (%)', fontsize=9)
            axes[1, 1].grid(True, alpha=0.3, axis='y')
            
            plt.tight_layout()
            pdf.savefig(fig, bbox_inches='tight')
            plt.close()
        
        print(f"✅ Comparison PDF created: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Comparison PDF error: {str(e)}")
        raise

if __name__ == "__main__":
    # Example usage
    print("Testing export functions...")
    
    # Mock data
    mock_result = {
        'avg_max_queue': 45.2,
        'std_max_queue': 12.3,
        'median_max_queue': 43.0,
        'percentile_95': 65.5,
        'percentile_99': 78.2,
        'avg_final_queue': 10.5,
        'avg_waiting_time': 8.5,
        'max_waiting_time': 15.2,
        'avg_service_rate': 0.85,
        'min_service_rate': 0.70,
        'prob_severe_jam': 0.12,
        'prob_moderate_jam': 0.35,
        'prob_light_traffic': 0.53,
        'avg_accidents_per_hour': 1.5,
        'all_max_queues': [float(x) for x in range(40, 60)],
        'sample_queue_history': [float(x) for x in range(0, 60)]
    }
    
    print("\n1. Testing Excel export...")
    try:
        excel_file = export_to_excel(mock_result, "test_scenario")
        print(f"   Success: {excel_file}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n2. Testing PDF export...")
    try:
        pdf_file = create_pdf_report(mock_result, "test_scenario")
        print(f"   Success: {pdf_file}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n✅ Export tests completed!")