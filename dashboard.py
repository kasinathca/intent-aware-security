import streamlit as st
import pandas as pd
import requests
import time
import altair as alt

# Config
st.set_page_config(
    page_title="Intent-Aware Security Dashboard",
    page_icon="🛡️",
    layout="wide"
)

# Constants
API_URL = "http://127.0.0.1:8000"
REFRESH_RATE = 1  # seconds

# Custom CSS for "Defense Center" theme
st.markdown("""
<style>
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    .metric-card {
        background-color: #262730;
        padding: 15px;
        border-radius: 5px;
        border: 1px solid #4F4F4F;
        text-align: center;
    }
    .status-ok {
        color: #00FF94;
        font-weight: bold;
        font-size: 24px;
        padding: 10px;
        border: 2px solid #00FF94;
        border-radius: 5px;
        text-align: center;
    }
    .status-alert {
        color: #FF4B4B;
        font-weight: bold;
        font-size: 24px;
        padding: 10px;
        border: 2px solid #FF4B4B;
        border-radius: 5px;
        text-align: center;
        animation: blinker 1s linear infinite;
    }
    @keyframes blinker {
        50% { opacity: 0.5; }
    }
</style>
""", unsafe_allow_html=True)

# Sidebar with Explanations
with st.sidebar:
    st.header("📚 Presentation Guide")
    st.markdown("""
    **What is this?**
    This dashboard represents the **Government/UIDAI Security Operations Center (SOC)**. It monitors all incoming verification requests in real-time.
    
    **Glossary:**
    - **Total Requests:** All API hits.
    - **Blocked Attacks:** Requests denied by our AI model.
    - **Risk Score:** 
        - < 0 = 🔴 Anomaly (Attack)
        - > 0 = 🟢 Normal Behavior
    
    **How to Demo:**
    1. Open **Attacker Terminal** alongside this.
    2. Run **Normal Sim** -> Watch lines stay flat/green.
    3. Run **Attack Sim** -> Watch red lines spike & status turn ALERT.
    """)
    st.markdown("---")
    st.info("System Status: Online")

# Application Header
st.title("🛡️ Intent-Aware Identity Verification System")
st.markdown("### 🇮🇳 Government of India / UIDAI Security Division")
st.markdown("---")

# Placeholder for real-time metrics
status_placeholder = st.empty()
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
            # Determine Threat Level
            # If > 5 blocked requests in last few seconds (approx), show ALERT
            # For simplicity, we just check total blocked count change or recent logs
            # Here we just look at the last 5 logs
            recent_blocks = 0
            if logs_data:
                recent_blocks = sum(1 for l in list(logs_data)[-10:] if l['status'] == 'BLOCKED')

            # 1. System Status Banner
            with status_placeholder.container():
                if recent_blocks > 2:
                    st.markdown('<div class="status-alert">🚨 SYSTEM UNDER ATTACK 🚨</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="status-ok">✅ SYSTEM SECURE - NORMAL OPERATION</div>', unsafe_allow_html=True)

            # 2. Key Metrics Row
            with metrics_placeholder.container():
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Total Traffic", stats['total_requests'], help="Total API hits received")
                c2.metric("Threats Blocked", stats['blocked_requests'], delta_color="inverse", help="Malicious requests stopped by AI")
                
                pass_rate = stats.get('pass_rate', 0) * 100
                c3.metric("Legitimacy Rate", f"{pass_rate:.1f}%", help="% of traffic that is genuine")
                
                avg_risk = "N/A"
                if logs_data:
                    # Calculate avg risk of last 10 requests
                    last_10 = list(logs_data)[-10:]
                    avg_score = sum(l['risk_score'] for l in last_10) / len(last_10)
                    avg_risk = f"{avg_score:.2f}"
                c4.metric("Avg Risk Score", avg_risk, help="Lower score = Higher Risk")

            # 3. Live Charts (Time Series)
            if logs_data:
                df = pd.DataFrame(logs_data)
                # Ensure we have a numeric index for x-axis
                df = df.reset_index()

                with charts_placeholder.container():
                    col_chart1, col_chart2 = st.columns(2)
                    
                    with col_chart1:
                        st.subheader("📈 Traffic Velocity (Requests/Min)")
                        # Simple line chart of Rate over time
                        chart = alt.Chart(df).mark_line(point=True).encode(
                            x=alt.X('index', title='Recent Requests'),
                            y=alt.Y('rate', title='Requests per Minute'),
                            color=alt.Color('status', scale=alt.Scale(domain=['ALLOWED', 'BLOCKED'], range=['#00FF94', '#FF4B4B'])),
                            tooltip=['rate', 'status', 'endpoint']
                        ).properties(height=300)
                        st.altair_chart(chart, use_container_width=True)
                    
                    with col_chart2:
                        st.subheader("📦 Payload Size Analysis")
                        # Bar/Line chart of Payload Size
                        chart2 = alt.Chart(df).mark_bar().encode(
                            x=alt.X('index', title='Recent Requests'),
                            y=alt.Y('payload', title='Data Size (KB)'),
                            color=alt.condition(
                                alt.datum.status == 'BLOCKED',
                                alt.value('#FF4B4B'),  # Red for blocked
                                alt.value('#00FF94')   # Green for allowed
                            ),
                            tooltip=['payload', 'status', 'geo']
                        ).properties(height=300)
                        st.altair_chart(chart2, use_container_width=True)

            # 4. Recent Alerts Log
            with logs_placeholder.container():
                st.subheader("🛡️ Security Audit Log")
                if logs_data:
                    # Filter for just the columns we want to show
                    display_df = pd.DataFrame(logs_data)[['timestamp', 'status', 'geo', 'endpoint', 'risk_score', 'rate']]
                    # Convert timestamp to readable time
                    display_df['timestamp'] = pd.to_datetime(display_df['timestamp'], unit='s').dt.strftime('%H:%M:%S')
                    
                    # Style the dataframe: Highlight BLOCKED rows
                    st.dataframe(
                        display_df.sort_index(ascending=False).head(10), # Show last 10 reversed
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("Waiting for traffic to begin...")

        else:
            st.error("⚠️ Connection Error: Cannot reach API Gateway. Please run 'python app.py' in a separate terminal.")
        
        time.sleep(REFRESH_RATE)
        # st.rerun() # Handled automatically by Streamlit loop now
