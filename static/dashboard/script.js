// --- CONFIGURATION ---
const API_BASE = ""; // Use relative paths to avoid CORS/Origin issues
const MAX_DATA_POINTS = 30; // Keep 30 points for rolling window

// --- STATE ---
let trafficChart;
let scatterChart;
let zkpChart;
let isAutoRefresh = true;
let refreshRate = 1000;
let refreshTimer = null;

// --- INITIALIZATION ---
document.addEventListener('DOMContentLoaded', () => {

    if (typeof Chart === 'undefined') {
        const errorMsg = "CRITICAL: Chart.js library is NOT loaded. Check Internet Connection or CDN.";

        document.getElementById('system-status-box').className = 'status-critical';
        document.getElementById('system-status-box').innerHTML = `<b>${errorMsg}</b>`;
        return;
    }


    try {
        initCharts();
        setupControls();
        fetchData(); // Initial fetch
        startPolling();

    } catch (e) {
        console.error('[Dashboard Init Error]', e);
        document.getElementById('system-status-box').className = 'status-critical';
        document.getElementById('system-status-box').innerHTML = `<b>Initialization Error: ${e.message}</b>`;
    }
});

function setupControls() {
    const autoCheck = document.getElementById('auto-refresh');
    const rateRange = document.getElementById('refresh-rate');
    const rateDisp = document.getElementById('freq-val');

    autoCheck.addEventListener('change', (e) => {
        isAutoRefresh = e.target.checked;
        if (isAutoRefresh) startPolling();
        else stopPolling();
    });

    rateRange.addEventListener('input', (e) => {
        refreshRate = parseFloat(e.target.value) * 1000;
        rateDisp.textContent = e.target.value;
        if (isAutoRefresh) {
            stopPolling();
            startPolling();
        }
    });

    // Security toggle event listeners
    const zkpToggle = document.getElementById('zkp-toggle');
    const mlToggle = document.getElementById('ml-toggle');

    zkpToggle.addEventListener('change', async (e) => {
        const enabled = e.target.checked;
        await updateSecurityConfig('zkp_enabled', enabled);
        updateStatusBadge('zkp-status', enabled);
    });

    mlToggle.addEventListener('change', async (e) => {
        const enabled = e.target.checked;
        await updateSecurityConfig('ml_enabled', enabled);
        updateStatusBadge('ml-status', enabled);
    });

    // Load initial security config
    loadSecurityConfig();
}

async function updateSecurityConfig(key, value) {
    try {
        const response = await fetch('/security/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ [key]: value })
        });
        const config = await response.json();
        console.log('Security config updated:', config);
    } catch (error) {
        console.error('Failed to update security config:', error);
    }
}

function updateStatusBadge(elementId, enabled) {
    const badge = document.getElementById(elementId);
    if (enabled) {
        badge.textContent = 'ON';
        badge.className = 'status-badge enabled';
    } else {
        badge.textContent = 'OFF';
        badge.className = 'status-badge disabled';
    }
}

async function loadSecurityConfig() {
    try {
        const response = await fetch('/security/config');
        const config = await response.json();

        document.getElementById('zkp-toggle').checked = config.zkp_enabled;
        document.getElementById('ml-toggle').checked = config.ml_enabled;
        updateStatusBadge('zkp-status', config.zkp_enabled);
        updateStatusBadge('ml-status', config.ml_enabled);
    } catch (error) {
        console.error('Failed to load security config:', error);
    }
}

function startPolling() {
    if (refreshTimer) clearInterval(refreshTimer);
    refreshTimer = setInterval(fetchData, refreshRate);
}

function stopPolling() {
    if (refreshTimer) clearInterval(refreshTimer);
}

// --- CHARTS ---
function initCharts() {

    try {
        // 1. Traffic Line Chart
        const ctxTraffic = document.getElementById('trafficChart').getContext('2d');
        trafficChart = new Chart(ctxTraffic, {
            type: 'line',
            data: {
                labels: [], // Will use string labels (HH:mm:ss)
                datasets: [{
                    label: 'Requests/Min',
                    data: [],
                    borderColor: '#1b4e9b',
                    backgroundColor: 'rgba(27, 78, 155, 0.1)',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true,
                    pointRadius: 3,
                    pointHoverRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { maxTicksLimit: 8 }
                    },
                    y: {
                        beginAtZero: true,
                        min: 0,
                        suggestedMax: 10,
                        grid: { borderDash: [5, 5] },
                        title: { display: true, text: 'Req/Min' }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: { intersect: false, mode: 'index' },
                    zoom: {
                        limits: {
                            x: { min: 0 },   // Never show negative x (time index)
                            y: { min: 0 }    // Never show negative request counts
                        },
                        zoom: {
                            wheel: { enabled: true },
                            pinch: { enabled: true },
                            mode: 'xy',
                        },
                        pan: {
                            enabled: true,
                            mode: 'xy'
                        }
                    }
                },
                animation: false // Disable animation for smooth real-time updates
            }
        });

        // 2. Anomaly Scatter Chart
        const ctxScatter = document.getElementById('scatterChart').getContext('2d');
        scatterChart = new Chart(ctxScatter, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Requests',
                    data: [],
                    backgroundColor: (ctx) => {
                        const val = ctx.raw?.status;
                        return val === 'BLOCKED' ? '#dc3545' : '#28a745'; // Red for blocked, Green for allowed
                    },
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        type: 'linear',
                        position: 'bottom',
                        title: { display: true, text: 'AI Risk Score (< 0 = Anomaly)' },
                        min: -1.0, // Expanded range for IsolationForest scores
                        max: 1.0,
                        grid: { color: (ctx) => ctx.tick.value === 0 ? '#666' : '#eee' } // Highlight 0 line
                    },
                    y: {
                        type: 'linear',
                        title: { display: true, text: 'Payload (KB)' },
                        beginAtZero: true,
                        min: 0,              // Payload can never be negative
                        suggestedMax: 100
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                const p = context.raw;
                                return `${p.status}: Payload ${p.y}KB, Score ${p.x.toFixed(3)}`;
                            }
                        }
                    },
                    legend: { display: false },
                    zoom: {
                        limits: {
                            y: { min: 0 }    // Payload (KB) can never be negative
                        },
                        zoom: {
                            wheel: { enabled: true },
                            pinch: { enabled: true },
                            mode: 'xy',
                        },
                        pan: {
                            enabled: true,
                            mode: 'xy'
                        }
                    }
                },
                animation: false
            }
        });

        // 3. ZKP Authentication Pie Chart
        const ctxZKP = document.getElementById('zkpChart').getContext('2d');
        zkpChart = new Chart(ctxZKP, {
            type: 'pie',
            data: {
                labels: ['ZKP-Enabled', 'Legacy (No ZKP)'],
                datasets: [{
                    data: [0, 0],
                    backgroundColor: ['#28a745', '#6c757d'],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 15,
                            font: { size: 12 }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });

    } catch (e) {
        console.error('[Chart Init Error]', e);
        const statusBox = document.getElementById('system-status-box');
        if (statusBox) {
            statusBox.className = 'status-critical';
            statusBox.innerHTML = `<b>Chart Initialization Error: ${e.message}</b>`;
        }
    }
}

// --- DATA FETCHING ---
async function fetchData() {
    try {
        // Fetch stats and logs from backend
        const [statsRes, logsRes] = await Promise.all([
            fetch(`${API_BASE}/stats`),
            fetch(`${API_BASE}/logs`)
        ]);

        if (!statsRes.ok || !logsRes.ok) throw new Error(`HTTP Error: ${statsRes.status}`);

        const stats = await statsRes.json();
        const logs = await logsRes.json();



        // Update connection status to ONLINE
        const connStatus = document.getElementById('connection-status');
        if (connStatus) {
            connStatus.style.background = '#e9f7ef';
            connStatus.style.borderLeft = '4px solid #28a745';
            connStatus.style.color = '#155724';
            connStatus.textContent = 'Status: ONLINE';
        }

        updateUI(stats, logs);
        updateCharts(logs);

    } catch (err) {


        // Update connection status to OFFLINE
        const connStatus = document.getElementById('connection-status');
        if (connStatus) {
            connStatus.style.background = '#f8d7da';
            connStatus.style.borderLeft = '4px solid #dc3545';
            connStatus.style.color = '#721c24';
            connStatus.textContent = 'Status: OFFLINE';
        }

        const statusBox = document.getElementById('system-status-box');
        if (statusBox) {
            statusBox.className = 'status-critical';
            statusBox.textContent = "SYSTEM STATUS: BACKEND CONNECTION FAILED";
        }
    }
}

function updateUI(stats, logs) {
    // Update Metrics
    document.getElementById('m-total').textContent = stats.total_requests;
    document.getElementById('m-blocked').textContent = stats.blocked_requests;

    // Update Pass Rate
    const passRate = stats.pass_rate || 1.0;
    document.getElementById('m-pass-rate').textContent = `${(passRate * 100).toFixed(1)}%`;

    // Update ZKP Pie Chart
    const zkpEnabled = stats.zkp_enabled_requests || 0;
    const legacyRequests = stats.total_requests - zkpEnabled;
    zkpChart.data.datasets[0].data = [zkpEnabled, legacyRequests];
    zkpChart.update('none'); // Update without animation

    // Threat Level Assessment
    const failRate = (stats.blocked_requests / Math.max(1, stats.total_requests));

    // Logic: Check last 15 logs for blocks
    const recentLogs = logs.slice(-15);
    const recentBlocks = recentLogs.filter(l => l.status === 'BLOCKED').length;

    const statusBox = document.getElementById('system-status-box');
    const attackIndicator = document.getElementById('attack-indicator');

    if (recentBlocks > 2) {
        statusBox.className = 'status-critical'; // Uses style.css class
        statusBox.textContent = "SYSTEM STATUS: CRITICAL ALERT - INTRUSION DETECTED";

        // Update attack indicator
        if (attackIndicator) {
            attackIndicator.style.background = '#f8d7da';
            attackIndicator.style.borderLeft = '4px solid #dc3545';
            attackIndicator.style.color = '#721c24';
            attackIndicator.innerHTML = '<b>WARNING: UNDER ATTACK</b><br><small>' + recentBlocks + ' threats in last 15 requests</small>';
        }
    } else {
        statusBox.className = 'status-normal';
        statusBox.textContent = "SYSTEM STATUS: OPERATIONAL - ALL SYSTEMS NOMINAL";

        // Update attack indicator
        if (attackIndicator) {
            attackIndicator.style.background = '#e9f7ef';
            attackIndicator.style.borderLeft = '4px solid #28a745';
            attackIndicator.style.color = '#155724';
            attackIndicator.innerHTML = 'NO ACTIVE ATTACK';
        }
    }

    // Table
    const tbody = document.getElementById('log-table-body');
    tbody.innerHTML = '';
    // Show last 8 logs, newest first
    const displayLogs = [...logs].reverse().slice(0, 8);

    displayLogs.forEach(log => {
        const row = document.createElement('tr');
        if (log.status === 'BLOCKED') row.className = 'row-blocked';

        const date = new Date(log.timestamp * 1000);
        const timeStr = date.toLocaleTimeString('en-GB'); // HH:MM:SS format

        // ZKP Status Badge
        let zkpBadge = '<span class="zkp-badge-none" style="opacity: 0.5;">N/A</span>';
        if (log.zkp_verified === true) {
            zkpBadge = '<span class="zkp-badge">✓ VERIFIED</span>';
        } else if (log.zkp_verified === false) {
            zkpBadge = '<span class="zkp-failed">✗ FAILED</span>';
        }

        // Blocked By Badge
        let blockedByBadge = '<span style="color: #6c757d;">--</span>';
        if (log.blocked_by) {
            const layerColor = log.blocked_by === 'ZKP' ? '#dc3545' : '#ff9933';
            blockedByBadge = `<span style="color: ${layerColor}; font-weight: 600;">${log.blocked_by}</span>`;
        }

        row.innerHTML = `
            <td>${timeStr}</td>
            <td><b>${log.status}</b></td>
            <td>${log.endpoint}</td>
            <td>${log.geo}</td>
            <td>${log.risk_score.toFixed(3)}</td>
            <td>${zkpBadge}</td>
            <td>${blockedByBadge}</td>
        `;
        tbody.appendChild(row);
    });
}

function updateCharts(logs) {
    // 1. Line Chart Data
    // Ensure we have data, otherwise clear chart
    if (!logs || logs.length === 0) return;

    // Sort logs by time just in case, though usually sorted
    const sortedLogs = [...logs].sort((a, b) => a.timestamp - b.timestamp);

    // Filter to last MAX_DATA_POINTS
    const recent = sortedLogs.slice(-MAX_DATA_POINTS);

    // X-Axis: Time Strings
    // Y-Axis: Rate
    const labels = recent.map(l => new Date(l.timestamp * 1000).toLocaleTimeString('en-GB'));
    const dataRate = recent.map(l => l.rate);

    trafficChart.data.labels = labels;
    trafficChart.data.datasets[0].data = dataRate;
    trafficChart.update('none'); // No animation for smooth real-time updates

    // 2. Scatter Data
    // Map logs to {x: score, y: payload, status: status}
    // Filter out nulls/NaNs
    const scatterData = recent.map(l => ({
        x: l.risk_score,
        y: l.payload,
        status: l.status
    }));

    scatterChart.data.datasets[0].data = scatterData;
    scatterChart.update('none'); // No animation for smooth real-time updates
}
