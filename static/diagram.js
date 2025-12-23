// Global variables
let currentScenarios = {};
let histogramChart = null;
let timeSeriesChart = null;
let comparisonChart = null;

// Scenario descriptions
const scenarioDescriptions = {
    baseline: "Current traffic light configuration with standard timing and capacity",
    optimized: "Enhanced green light timing with increased capacity for better flow",
    heavy_traffic: "Extended rush hour with significantly higher vehicle arrival rates",
    accident_prone: "High accident frequency scenario with longer incident durations",
    ideal_conditions: "Best case scenario with light traffic and minimal disruptions",
    weekend: "Typical weekend traffic patterns with reduced volume throughout",
    custom: "Custom parameters - adjust values to test your own scenario"
};

// Load scenario data
function loadScenario() {
    const scenario = document.getElementById('scenarioSelect').value;
    const customParams = document.getElementById('customParams');
    const descText = document.getElementById('descText');
    
    descText.textContent = scenarioDescriptions[scenario] || "Select a scenario";
    
    if (scenario === 'custom') {
        customParams.style.display = 'block';
    } else {
        customParams.style.display = 'none';
    }
}

// Get parameters from form
function getParameters() {
    const scenario = document.getElementById('scenarioSelect').value;
    const simCount = parseInt(document.getElementById('simCount').value);
    
    if (scenario === 'custom') {
        return {
            rush_hour_rate: [
                parseInt(document.getElementById('rushMin').value),
                parseInt(document.getElementById('rushMax').value)
            ],
            normal_rate: [
                parseInt(document.getElementById('normalMin').value),
                parseInt(document.getElementById('normalMax').value)
            ],
            green_capacity_normal: parseInt(document.getElementById('greenCapacity').value),
            green_capacity_accident: 2,
            accident_probability: parseFloat(document.getElementById('accidentProb').value) / 100,
            accident_duration_range: [5, 15],
            rush_hour_minutes: parseInt(document.getElementById('rushDuration').value),
            simulation_minutes: 60,
            simulations: simCount
        };
    } else {
        return { simulations: simCount };
    }
}

// Run simulation
async function runSimulation() {
    const scenario = document.getElementById('scenarioSelect').value;
    const params = getParameters();
    
    // Show loading
    document.getElementById('loading').style.display = 'block';
    document.getElementById('results').style.display = 'none';
    document.getElementById('comparisonResults').style.display = 'none';
    
    // Disable button
    const btn = document.querySelector('.btn-primary');
    btn.disabled = true;
    document.getElementById('btnText').innerHTML = '⏳ Running...';
    
    try {
        let response;
        
        if (scenario === 'custom') {
            response = await fetch('/simulate/enhanced', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(params)
            });
        } else {
            response = await fetch(`/scenarios/${scenario}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ simulations: params.simulations })
            });
        }
        
        const data = await response.json();
        displayResults(data);
        
    } catch (error) {
        console.error('Error:', error);
        alert('Simulation failed. Please try again.');
    } finally {
        // Hide loading, re-enable button
        document.getElementById('loading').style.display = 'none';
        btn.disabled = false;
        document.getElementById('btnText').innerHTML = '▶ Run Simulation';
    }
}

// Display results
function displayResults(data) {
    // Show results panel
    document.getElementById('results').style.display = 'block';
    
    // Update metrics cards
    document.getElementById('avgQueue').textContent = data.avg_max_queue.toFixed(1);
    document.getElementById('avgWait').textContent = data.avg_waiting_time.toFixed(2);
    document.getElementById('serviceRate').textContent = (data.avg_service_rate * 100).toFixed(1);
    
    // Update traffic level card
    const levelCard = document.getElementById('trafficLevelCard');
    levelCard.className = 'metric-card traffic-' + data.traffic_level;
    document.getElementById('trafficLevel').textContent = data.traffic_level.toUpperCase();
    document.getElementById('trafficDesc').textContent = data.traffic_level_description;
    
    // Update probabilities
    updateProbability('probLight', 'probLightVal', data.prob_light_traffic);
    updateProbability('probModerate', 'probModerateVal', data.prob_moderate_jam);
    updateProbability('probSevere', 'probSevereVal', data.prob_severe_jam);
    
    // Create charts
    createHistogram(data.all_max_queues);
    createTimeSeries(data.sample_queue_history);
    
    // Generate recommendations
    generateRecommendations(data);
}

// Update probability bar
function updateProbability(barId, valueId, probability) {
    const percentage = (probability * 100).toFixed(1);
    document.getElementById(barId).style.width = percentage + '%';
    document.getElementById(valueId).textContent = percentage + '%';
}

// Create histogram chart
function createHistogram(data) {
    const ctx = document.getElementById('histogramChart');
    
    // Destroy existing chart
    if (histogramChart) {
        histogramChart.destroy();
    }
    
    // Create histogram bins
    const bins = 20;
    const min = Math.min(...data);
    const max = Math.max(...data);
    const binWidth = (max - min) / bins;
    
    const histogram = new Array(bins).fill(0);
    const labels = [];
    
    for (let i = 0; i < bins; i++) {
        const binStart = min + i * binWidth;
        const binEnd = binStart + binWidth;
        labels.push(binStart.toFixed(0) + '-' + binEnd.toFixed(0));
        
        histogram[i] = data.filter(x => x >= binStart && x < binEnd).length;
    }
    
    histogramChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Frequency',
                data: histogram,
                backgroundColor: 'rgba(33, 150, 243, 0.7)',
                borderColor: 'rgba(33, 150, 243, 1)',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false },
                title: {
                    display: true,
                    text: 'Distribution of Maximum Queue Length'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Frequency' }
                },
                x: {
                    title: { display: true, text: 'Queue Length (vehicles)' }
                }
            }
        }
    });
}

// Create time series chart
function createTimeSeries(data) {
    const ctx = document.getElementById('timeSeriesChart');
    
    // Destroy existing chart
    if (timeSeriesChart) {
        timeSeriesChart.destroy();
    }
    
    const labels = data.map((_, i) => i + 1);
    
    timeSeriesChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Queue Length',
                data: data,
                borderColor: 'rgba(255, 87, 34, 1)',
                backgroundColor: 'rgba(255, 87, 34, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false },
                title: {
                    display: true,
                    text: 'Queue Evolution (Sample Simulation)'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Queue Length (vehicles)' }
                },
                x: {
                    title: { display: true, text: 'Time (minutes)' }
                }
            }
        }
    });
}

// Generate recommendations
function generateRecommendations(data) {
    const container = document.getElementById('recommendationsList');
    container.innerHTML = '';
    
    const recommendations = [];
    
    // Queue length recommendations
    if (data.avg_max_queue > 100) {
        recommendations.push({
            type: 'critical',
            title: '🚨 Critical: Very High Queue Length',
            text: `Average maximum queue of ${data.avg_max_queue.toFixed(1)} vehicles is critically high. Consider increasing green light capacity or duration by 30-50%.`
        });
    } else if (data.avg_max_queue > 60) {
        recommendations.push({
            type: 'warning',
            title: '⚠️ Warning: Moderate Congestion',
            text: `Queue length of ${data.avg_max_queue.toFixed(1)} vehicles indicates congestion. Traffic light optimization could improve flow by 15-25%.`
        });
    }
    
    // Service rate recommendations
    if (data.avg_service_rate < 0.7) {
        recommendations.push({
            type: 'critical',
            title: '🚨 Critical: Low Service Rate',
            text: `Service rate of ${(data.avg_service_rate * 100).toFixed(1)}% indicates system cannot handle current demand. Capacity expansion needed.`
        });
    }
    
    // Waiting time recommendations
    if (data.avg_waiting_time > 10) {
        recommendations.push({
            type: 'warning',
            title: '⏱️ High Waiting Time',
            text: `Average waiting time of ${data.avg_waiting_time.toFixed(2)} minutes is high. Implement adaptive traffic light timing for 20-30% improvement.`
        });
    }
    
    // Accident recommendations
    if (data.avg_accidents_per_hour > 2) {
        recommendations.push({
            type: 'info',
            title: '🚑 High Accident Frequency',
            text: `${data.avg_accidents_per_hour.toFixed(2)} accidents per hour detected. Improve road safety measures and emergency response protocols.`
        });
    }
    
    // Severe jam probability
    if (data.prob_severe_jam > 0.2) {
        recommendations.push({
            type: 'critical',
            title: '📊 High Severe Jam Probability',
            text: `${(data.prob_severe_jam * 100).toFixed(1)}% chance of severe congestion. Immediate intervention needed - consider alternative routes.`
        });
    }
    
    // Display recommendations
    if (recommendations.length === 0) {
        container.innerHTML = '<p style="color: #4CAF50; font-weight: 600;">✅ No critical issues detected. Traffic flow is optimal.</p>';
    } else {
        recommendations.forEach(rec => {
            const div = document.createElement('div');
            div.className = `recommendation-item ${rec.type}`;
            div.innerHTML = `<strong>${rec.title}</strong><p>${rec.text}</p>`;
            container.appendChild(div);
        });
    }
}

// Compare scenarios
async function compareScenarios() {
    // Show loading
    document.getElementById('loading').style.display = 'block';
    document.getElementById('results').style.display = 'none';
    document.getElementById('comparisonResults').style.display = 'none';
    
    const simCount = parseInt(document.getElementById('simCount').value);
    
    try {
        const response = await fetch('/scenarios/compare', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                scenarios: ['baseline', 'optimized', 'heavy_traffic', 'ideal_conditions'],
                simulations: simCount
            })
        });
        
        const data = await response.json();
        displayComparison(data);
        
    } catch (error) {
        console.error('Error:', error);
        alert('Comparison failed. Please try again.');
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
}

// Display comparison results
function displayComparison(data) {
    document.getElementById('comparisonResults').style.display = 'block';
    
    // Prepare data for chart
    const scenarios = Object.keys(data);
    const avgQueues = scenarios.map(s => data[s].avg_max_queue);
    const waitTimes = scenarios.map(s => data[s].avg_waiting_time);
    const serviceRates = scenarios.map(s => data[s].avg_service_rate * 100);
    
    // Create comparison chart
    const ctx = document.getElementById('comparisonChart');
    
    if (comparisonChart) {
        comparisonChart.destroy();
    }
    
    comparisonChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: scenarios,
            datasets: [
                {
                    label: 'Avg Max Queue',
                    data: avgQueues,
                    backgroundColor: 'rgba(33, 150, 243, 0.7)',
                    yAxisID: 'y'
                },
                {
                    label: 'Avg Waiting Time',
                    data: waitTimes,
                    backgroundColor: 'rgba(255, 87, 34, 0.7)',
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Scenario Comparison'
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: { display: true, text: 'Queue Length (vehicles)' }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: { display: true, text: 'Waiting Time (min)' },
                    grid: { drawOnChartArea: false }
                }
            }
        }
    });
    
    // Create comparison table
    createComparisonTable(data);
}

// Create comparison table
function createComparisonTable(data) {
    const container = document.getElementById('comparisonTable');
    
    let html = '<div class="comparison-table"><table>';
    html += '<thead><tr>';
    html += '<th>Scenario</th>';
    html += '<th>Avg Max Queue</th>';
    html += '<th>Waiting Time</th>';
    html += '<th>Service Rate</th>';
    html += '<th>Severe Jam Prob</th>';
    html += '</tr></thead><tbody>';
    
    for (const [scenario, result] of Object.entries(data)) {
        html += '<tr>';
        html += `<td><strong>${scenario}</strong></td>`;
        html += `<td>${result.avg_max_queue.toFixed(1)} vehicles</td>`;
        html += `<td>${result.avg_waiting_time.toFixed(2)} min</td>`;
        html += `<td>${(result.avg_service_rate * 100).toFixed(1)}%</td>`;
        html += `<td>${(result.prob_severe_jam * 100).toFixed(1)}%</td>`;
        html += '</tr>';
    }
    
    html += '</tbody></table></div>';
    container.innerHTML = html;
}

// ============ ADVANCED FEATURES ============

// Export to Excel
async function exportToExcel(resultData, scenarioName) {
    try {
        const response = await fetch('/export/excel', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                result_data: resultData,
                scenario_name: scenarioName
            })
        });
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${scenarioName}_${Date.now()}.xlsx`;
        a.click();
        
        alert('Excel file downloaded successfully!');
    } catch (error) {
        console.error('Export error:', error);
        alert('Export failed. Please try again.');
    }
}

// Export to PDF
async function exportToPDF(resultData, scenarioName) {
    try {
        const response = await fetch('/export/pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                result_data: resultData,
                scenario_name: scenarioName
            })
        });
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${scenarioName}_report_${Date.now()}.pdf`;
        a.click();
        
        alert('PDF report downloaded successfully!');
    } catch (error) {
        console.error('Export error:', error);
        alert('Export failed. Please try again.');
    }
}

// View History
async function viewHistory() {
    try {
        const response = await fetch('/history/recent?limit=20');
        const history = await response.json();
        
        // Create modal or new section to display history
        let html = '<div class="history-modal"><h3>Recent Simulations</h3><table>';
        html += '<tr><th>Time</th><th>Scenario</th><th>Avg Queue</th><th>Service Rate</th></tr>';
        
        history.forEach(record => {
            const timestamp = new Date(record.timestamp).toLocaleString();
            html += `<tr>
                <td>${timestamp}</td>
                <td>${record.scenario_name}</td>
                <td>${record.avg_max_queue.toFixed(1)}</td>
                <td>${(record.avg_service_rate * 100).toFixed(1)}%</td>
            </tr>`;
        });
        
        html += '</table><button onclick="closeHistory()">Close</button></div>';
        
        document.body.insertAdjacentHTML('beforeend', html);
    } catch (error) {
        console.error('History error:', error);
        alert('Failed to load history.');
    }
}

function closeHistory() {
    const modal = document.querySelector('.history-modal');
    if (modal) modal.remove();
}

// Network Simulation
async function simulateNetwork() {
    const networkType = prompt('Enter network type: simple_two_intersection, four_way_grid, or highway_corridor', 'simple_two_intersection');
    
    if (!networkType) return;
    
    document.getElementById('loading').style.display = 'block';
    
    try {
        const response = await fetch(`/network/simulate/${networkType}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ simulations: 100 })
        });
        
        const data = await response.json();
        displayNetworkResults(data);
        
    } catch (error) {
        console.error('Error:', error);
        alert('Network simulation failed.');
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
}

function displayNetworkResults(data) {
    let html = '<div class="network-results"><h3>Network Simulation Results</h3>';
    
    // Per intersection
    html += '<h4>Individual Intersections:</h4>';
    for (const [intId, metrics] of Object.entries(data.intersections)) {
        html += `<div class="intersection-card">
            <strong>Intersection ${intId}</strong><br>
            Avg Max Queue: ${metrics.avg_max_queue.toFixed(1)} vehicles<br>
            Waiting Time: ${metrics.avg_waiting_time.toFixed(2)} min<br>
            Service Rate: ${(metrics.avg_service_rate * 100).toFixed(1)}%
        </div>`;
    }
    
    // Network summary
    html += '<h4>Network Summary:</h4>';
    html += `<p>Total Avg Max Queue: ${data.network_summary.avg_total_max_queue.toFixed(1)}</p>`;
    html += `<p>Network Service Rate: ${(data.network_summary.avg_network_service_rate * 100).toFixed(1)}%</p>`;
    
    html += '<button onclick="closeNetworkResults()">Close</button></div>';
    
    document.body.insertAdjacentHTML('beforeend', html);
}

function closeNetworkResults() {
    const modal = document.querySelector('.network-results');
    if (modal) modal.remove();
}

// Advanced Pattern Simulation
async function simulateAdvancedPattern() {
    const scenarioType = prompt('Enter scenario: surabaya_morning, rainy_season, weekend_mall, concert_venue, or road_construction', 'surabaya_morning');
    
    if (!scenarioType) return;
    
    document.getElementById('loading').style.display = 'block';
    
    try {
        const response = await fetch(`/advanced/simulate/${scenarioType}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                simulations: 1000,
                simulation_minutes: 240
            })
        });
        
        const data = await response.json();
        displayResults(data);
        
    } catch (error) {
        console.error('Error:', error);
        alert('Advanced simulation failed.');
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
}

// Store current result globally for export
let currentResult = null;
let currentScenarioName = null;

// Modified displayResults to store data
const originalDisplayResults = displayResults;
displayResults = function(data) {
    currentResult = data;
    currentScenarioName = data.scenario_name || 'simulation';
    originalDisplayResults(data);
    
    // Add export buttons if not present
    if (!document.getElementById('exportButtons')) {
        const exportDiv = document.createElement('div');
        exportDiv.id = 'exportButtons';
        exportDiv.className = 'button-group';
        exportDiv.style.marginTop = '20px';
        exportDiv.innerHTML = `
            <button class="btn btn-secondary" onclick="exportToExcel(currentResult, currentScenarioName)">
                📊 Export to Excel
            </button>
            <button class="btn btn-secondary" onclick="exportToPDF(currentResult, currentScenarioName)">
                📄 Export to PDF
            </button>
        `;
        document.getElementById('results').appendChild(exportDiv);
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadScenario();
    
    // Add advanced feature buttons
    const controlPanel = document.querySelector('.controls-panel');
    if (controlPanel) {
        const advancedDiv = document.createElement('div');
        advancedDiv.className = 'control-group';
        advancedDiv.innerHTML = `
            <h3 style="margin-top: 30px; color: #2196F3;">Advanced Features</h3>
            <button class="btn btn-secondary" onclick="viewHistory()" style="width: 100%; margin-bottom: 10px;">
                📜 View History
            </button>
            <button class="btn btn-secondary" onclick="simulateNetwork()" style="width: 100%; margin-bottom: 10px;">
                🌐 Network Simulation
            </button>
            <button class="btn btn-secondary" onclick="simulateAdvancedPattern()" style="width: 100%; margin-bottom: 10px;">
                🚀 Advanced Patterns
            </button>
        `;
        controlPanel.appendChild(advancedDiv);
    }
});