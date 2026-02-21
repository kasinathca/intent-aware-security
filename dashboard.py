import streamlit as st
import pandas as pd
import requests
import time
import altair as alt
import config

# Config
st.set_page_config(
    page_title="Intent-Aware Security Dashboard",
    page_icon="🛡️",
    layout="wide"
)

# Constants
API_URL = "http://127.0.0.1:8000"
REFRESH_RATE = 1  # seconds

# Custom CSS for "Hacker" theme
st.markdown("""
<style>
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    .metric-card {
        background-color: #262730;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #4F4F4F;
    }
    h1, h2, h3 {
        color: #00FF94 !important; 
        font-family: 'Courier New', monospace;
    }
</style>
""", unsafe_allow_html=True)

# Application Header
st.title("🛡️ Intent-Aware Identity Verification System")
st.markdown("**Project by Group 4 (PHY1901) - Initial Prototype**")
st.markdown("---")

# Layout
col1, col2 = st.columns([2, 1])

# Placeholder for real-time metrics
metrics_placeholder = st.empty()
charts_placeholder = st.empty()
logs_placeholder = st.empty()

def fetch_data():
    try:
        stats = requests.get(f"{API_URL}/stats").json()
        logs = requests.get(f"{API_URL}/logs").json()
        return stats, logs
    except:
        return None, None

# Main Loop
if st.checkbox("🔴 Start Live Monitoring", value=True):
    while True:
        stats, logs_data = fetch_data()
        
        if stats:
            # 1. Update Metrics
            with metrics_placeholder.container():
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Total Requests", stats['total_requests'])
                c2.metric("Blocked Attacks", stats['blocked_requests'], delta_color="inverse")
                
                pass_rate = stats.get('pass_rate', 0) * 100
                c3.metric("Pass Rate", f"{pass_rate:.1f}%")
                
                uptime = stats.get('uptime_seconds', 0)
                c4.metric("System Uptime", f"{uptime}s")

            # 2. Update Charts
            if logs_data:
                df = pd.DataFrame(logs_data)
                
                with charts_placeholder.container():
                    st.subheader("Live Traffic Analysis")
                    
                    # Scatter Plot: Request Rate vs Payload Size
                    scatter = alt.Chart(df).mark_circle(size=60).encode(
                        x='rate',
                        y='payload',
                        color=alt.Color('status', scale=alt.Scale(domain=['ALLOWED', 'BLOCKED'], range=['#00FF94', '#FF4B4B'])),
                        tooltip=['status', 'risk_score', 'geo', 'endpoint']
                    ).properties(
                        title="Anomaly Detection Map (Rate vs Payload)",
                        height=350
                    ).interactive()
                    
                    st.altair_chart(scatter, use_container_width=True)

            # 3. Update Logs (Alerts only)
            with logs_placeholder.container():
                st.subheader("🚨 Recent Security Alerts")
                if logs_data:
                    alerts = [l for l in logs_data if l['status'] == 'BLOCKED']
                    if alerts:
                        st.dataframe(
                            pd.DataFrame(alerts)[['timestamp', 'geo', 'endpoint', 'risk_score', 'rate']],
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.info("No active threats detected.")
                else:
                    st.info("Waiting for traffic...")

        else:
            st.error("Cannot connect to API Gateway. Is 'app.py' running?")
        
        time.sleep(REFRESH_RATE)

