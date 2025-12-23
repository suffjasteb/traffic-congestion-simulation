import json
import sqlite3
from datetime import datetime
import os
import pandas as pd

class SimulationHistory:
    """Manage simulation history and storage"""
    
    def __init__(self, db_path="results/simulation_history.db"):
        self.db_path = db_path
        self._ensure_db_dir()
        self._init_database()
    
    def _ensure_db_dir(self):
        """Ensure database directory exists"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def _init_database(self):
        """Initialize database with tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Simulations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS simulations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                scenario_name TEXT NOT NULL,
                num_simulations INTEGER,
                avg_max_queue REAL,
                std_max_queue REAL,
                median_max_queue REAL,
                percentile_95 REAL,
                percentile_99 REAL,
                avg_waiting_time REAL,
                max_waiting_time REAL,
                avg_service_rate REAL,
                prob_severe_jam REAL,
                prob_moderate_jam REAL,
                prob_light_traffic REAL,
                avg_accidents_per_hour REAL,
                traffic_level TEXT,
                parameters TEXT
            )
        ''')
        
        # Comparison runs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comparison_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                scenario_names TEXT NOT NULL,
                num_simulations INTEGER,
                best_scenario TEXT,
                worst_scenario TEXT,
                results_json TEXT
            )
        ''')
        
        # Daily summaries table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                total_simulations INTEGER,
                avg_queue_length REAL,
                most_used_scenario TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_simulation(self, scenario_name, result_data, parameters=None):
        """Save a single simulation run"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO simulations (
                timestamp, scenario_name, num_simulations,
                avg_max_queue, std_max_queue, median_max_queue,
                percentile_95, percentile_99,
                avg_waiting_time, max_waiting_time,
                avg_service_rate, prob_severe_jam, prob_moderate_jam,
                prob_light_traffic, avg_accidents_per_hour,
                traffic_level, parameters
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp,
            scenario_name,
            len(result_data.get('all_max_queues', [])),
            result_data.get('avg_max_queue'),
            result_data.get('std_max_queue'),
            result_data.get('median_max_queue'),
            result_data.get('percentile_95'),
            result_data.get('percentile_99'),
            result_data.get('avg_waiting_time'),
            result_data.get('max_waiting_time'),
            result_data.get('avg_service_rate'),
            result_data.get('prob_severe_jam'),
            result_data.get('prob_moderate_jam'),
            result_data.get('prob_light_traffic'),
            result_data.get('avg_accidents_per_hour'),
            result_data.get('traffic_level', 'unknown'),
            json.dumps(parameters) if parameters else None
        ))
        
        simulation_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"✅ Simulation saved (ID: {simulation_id})")
        return simulation_id
    
    def save_comparison(self, scenario_names, comparison_data, num_simulations):
        """Save a comparison run"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        
        # Find best and worst scenarios
        avg_queues = {name: data['avg_max_queue'] 
                     for name, data in comparison_data.items()}
        best_scenario = min(avg_queues, key=avg_queues.get)
        worst_scenario = max(avg_queues, key=avg_queues.get)
        
        cursor.execute('''
            INSERT INTO comparison_runs (
                timestamp, scenario_names, num_simulations,
                best_scenario, worst_scenario, results_json
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            timestamp,
            ','.join(scenario_names),
            num_simulations,
            best_scenario,
            worst_scenario,
            json.dumps(comparison_data, default=str)
        ))
        
        comparison_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"✅ Comparison saved (ID: {comparison_id})")
        return comparison_id
    
    def get_recent_simulations(self, limit=10):
        """Get most recent simulation runs"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM simulations
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    def get_simulations_by_scenario(self, scenario_name):
        """Get all simulations for a specific scenario"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM simulations
            WHERE scenario_name = ?
            ORDER BY timestamp DESC
        ''', (scenario_name,))
        
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    def get_statistics_summary(self):
        """Get overall statistics summary"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total simulations
        cursor.execute('SELECT COUNT(*) FROM simulations')
        total_sims = cursor.fetchone()[0]
        
        # Average metrics
        cursor.execute('''
            SELECT 
                AVG(avg_max_queue) as avg_queue,
                AVG(avg_waiting_time) as avg_wait,
                AVG(avg_service_rate) as avg_service,
                scenario_name,
                COUNT(*) as run_count
            FROM simulations
            GROUP BY scenario_name
            ORDER BY run_count DESC
        ''')
        
        scenario_stats = cursor.fetchall()
        
        # Recent trend (last 7 days)
        cursor.execute('''
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as count,
                AVG(avg_max_queue) as avg_queue
            FROM simulations
            WHERE timestamp >= datetime('now', '-7 days')
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
        ''')
        
        recent_trend = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_simulations': total_sims,
            'scenario_statistics': scenario_stats,
            'recent_trend': recent_trend
        }
    
    def export_history_to_excel(self, filename=None):
        """Export entire history to Excel"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"results/exports/history_{timestamp}.xlsx"
        
        conn = sqlite3.connect(self.db_path)
        
        # Read all tables
        df_simulations = pd.read_sql_query("SELECT * FROM simulations", conn)
        df_comparisons = pd.read_sql_query("SELECT * FROM comparison_runs", conn)
        
        conn.close()
        
        # Write to Excel
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df_simulations.to_excel(writer, sheet_name='All_Simulations', index=False)
            df_comparisons.to_excel(writer, sheet_name='Comparisons', index=False)
            
            # Summary statistics
            summary_stats = self.get_statistics_summary()
            df_stats = pd.DataFrame(summary_stats['scenario_statistics'],
                                   columns=['Avg_Queue', 'Avg_Wait', 'Avg_Service', 
                                           'Scenario', 'Run_Count'])
            df_stats.to_excel(writer, sheet_name='Statistics', index=False)
        
        print(f"✅ History exported to: {filename}")
        return filename
    
    def get_trend_analysis(self, scenario_name, days=30):
        """Analyze trends for a specific scenario"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                DATE(timestamp) as date,
                AVG(avg_max_queue) as avg_queue,
                AVG(avg_waiting_time) as avg_wait,
                AVG(avg_service_rate) as avg_service,
                COUNT(*) as num_runs
            FROM simulations
            WHERE scenario_name = ?
              AND timestamp >= datetime('now', '-' || ? || ' days')
            GROUP BY DATE(timestamp)
            ORDER BY date
        ''', (scenario_name, days))
        
        results = cursor.fetchall()
        conn.close()
        
        return {
            'dates': [r[0] for r in results],
            'avg_queues': [r[1] for r in results],
            'avg_waits': [r[2] for r in results],
            'avg_services': [r[3] for r in results],
            'num_runs': [r[4] for r in results]
        }
    
    def compare_historical_performance(self, scenario_name):
        """Compare current scenario against historical average"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get historical average
        cursor.execute('''
            SELECT 
                AVG(avg_max_queue) as hist_avg_queue,
                AVG(avg_waiting_time) as hist_avg_wait,
                AVG(avg_service_rate) as hist_avg_service,
                MIN(avg_max_queue) as best_queue,
                MAX(avg_max_queue) as worst_queue
            FROM simulations
            WHERE scenario_name = ?
        ''', (scenario_name,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] is not None:
            return {
                'historical_avg_queue': result[0],
                'historical_avg_wait': result[1],
                'historical_avg_service': result[2],
                'best_performance_queue': result[3],
                'worst_performance_queue': result[4]
            }
        return None
    
    def clear_old_data(self, days_to_keep=90):
        """Clear simulation data older than specified days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM simulations
            WHERE timestamp < datetime('now', '-' || ? || ' days')
        ''', (days_to_keep,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        print(f"✅ Deleted {deleted_count} old records")
        return deleted_count

# Global instance
history = SimulationHistory()

if __name__ == "__main__":
    # Example usage
    print("Testing History System...")
    
    # Mock result data
    mock_result = {
        'avg_max_queue': 45.2,
        'std_max_queue': 12.3,
        'median_max_queue': 43.0,
        'percentile_95': 65.5,
        'percentile_99': 78.2,
        'avg_waiting_time': 8.5,
        'max_waiting_time': 15.2,
        'avg_service_rate': 0.85,
        'prob_severe_jam': 0.12,
        'prob_moderate_jam': 0.35,
        'prob_light_traffic': 0.53,
        'avg_accidents_per_hour': 1.5,
        'traffic_level': 'moderate',
        'all_max_queues': list(range(100))
    }
    
    # Save simulation
    history.save_simulation('baseline', mock_result, {'test': True})
    
    # Get recent
    recent = history.get_recent_simulations(5)
    print(f"\nRecent simulations: {len(recent)}")
    
    # Get stats
    stats = history.get_statistics_summary()
    print(f"\nTotal simulations in DB: {stats['total_simulations']}")
    
    print("\n✅ History system working!")