import streamlit as st
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
from groq_handler import GroqHandler
from oracle_manager import OracleManager
from health_monitor import HealthMonitor
from security import SecurityManager
import os
import numpy as np

load_dotenv()

# Initialize components
groq = GroqHandler()
security = SecurityManager()
monitor = HealthMonitor()

# App Configuration
st.set_page_config(page_title="AI Oracle Assistant", layout="wide")

def init_session_state():
    if "oracle" not in st.session_state:
        st.session_state.oracle = OracleManager(os.getenv("ORACLE_DSN"))
    if "generated_sql" not in st.session_state:
        st.session_state.generated_sql = None

def connection_form():
    with st.form("connection"):
        st.subheader("Database Connection")
        username = st.text_input("Username", "HR")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Connect"):
            if st.session_state.oracle.connect(username, password):
                st.success("Connected successfully")
                st.experimental_rerun() # Refresh the page
            else:
                st.error("Connection failed")

def main_interface():
    st.title("AI-Powered Oracle Database Assistant")
    
    tabs = st.tabs(["NL2SQL", "Optimizer", "Health Monitor"])
    
    with tabs[0]:
        handle_nl2sql()
    
    with tabs[1]:
        handle_optimization()
    
    with tabs[2]:
        handle_health_monitor()

def handle_nl2sql():
    col1, col2 = st.columns([3, 2])


    
    with col1:
        query = st.text_area("Enter your request:", height=150)
        if st.button("Generate SQL"):
            if query:
                with st.spinner("Generating..."):
                    generated = groq.generate_sql(query)
                    st.session_state.generated_sql = generated
                    st.session_state.edited_sql = generated  # Initialize edited version
    with col2:
        if st.session_state.generated_sql:
            st.subheader("Generated SQL")
            st.code(st.session_state.generated_sql)
            exe_gen_sql = st.button("Execute Generated SQL")

            # Add execute button for generated SQL


    # Add editable SQL section in full screen
    st.subheader("Edit & Execute SQL")
    edited_sql = st.text_area(
        "Modify the SQL below:",
        value=st.session_state.generated_sql,
        height=150,
        key="edited_sql"
    )

    if st.button("Execute Edited SQL"):
        execute_query(edited_sql)

    if exe_gen_sql:
        execute_query(st.session_state.generated_sql)

def execute_query(sql):
    try:
        if security.sanitize_input(sql):
            df = st.session_state.oracle.execute_query(sql)
            if not df.empty:
                st.dataframe(df)
                # Uncomment to add visualization
                # st.plotly_chart(px.bar(df, title="Query Results"))
            else:
                st.warning("Query executed successfully but returned no rows.")
        else:
            st.error("Query blocked by security rules")
    except Exception as e:
        st.error(f"Execution error: {str(e)}")

def handle_optimization():
    if st.button("Analyze Slow Queries"):
        queries = st.session_state.oracle.get_performance_data()
        for q in queries:
            with st.expander(f"Query {q['sql_id']}"):
                st.code(q["sql_text"])
                optimized = groq.optimize_sql(q["sql_text"])
                st.markdown(f"**Optimization Suggestions:**\n{optimized}")

def handle_health_monitor():
    if st.button("Run Health Check"):
        data = np.random.rand(100, 1)  # Replace with real metrics
        monitor.train_model(data)
        anomalies = monitor.detect_anomalies(data)
        st.write("Anomaly Detection Results:", anomalies)

if __name__ == "__main__":
    init_session_state()
    
    if not st.session_state.oracle.conn:
        connection_form()
    else:
        main_interface()
        if st.button("Disconnect"):
            st.session_state.oracle.close()
            st.experimental_rerun()