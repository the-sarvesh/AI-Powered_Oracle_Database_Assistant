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
    if "executed_sql" not in st.session_state:
        st.session_state.executed_sql = None
    if "query_df" not in st.session_state:
        st.session_state.query_df = None
    # Initialize chat-related state variables
    if "chat_user_question" not in st.session_state:
        st.session_state.chat_user_question = ""
    if "chat_ai_response" not in st.session_state:
        st.session_state.chat_ai_response = ""
    if "chat_has_response" not in st.session_state:
        st.session_state.chat_has_response = False

def connection_form():
    with st.form("connection"):
        st.subheader("Database Connection")
        username = st.text_input("Username", "HR")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Connect"):
            if st.session_state.oracle.connect(username, password):
                st.success("Connected successfully")
                st.experimental_rerun()  # Refresh the page
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
    
    # Display query results, analysis, and chat only if a query has been executed
    if st.session_state.get("query_df") is not None and st.session_state.get("executed_sql") is not None:
        st.subheader("Query Results")
        st.dataframe(st.session_state.query_df)
        show_analysis_section()
        show_chat_section()

def handle_nl2sql():
    col1, col2 = st.columns([3, 2])

    with col1:
        query = st.text_area("Enter your request:", height=150)
        if st.button("Generate SQL"):
            if query:
                with st.spinner("Generating..."):
                    generated = groq.generate_sql(query)
                    st.session_state.generated_sql = generated
                    st.session_state.edited_sql = generated  # Initialize editable SQL
    with col2:
        if st.session_state.generated_sql:
            st.subheader("Generated SQL")
            st.code(st.session_state.generated_sql)
            exe_gen_sql = st.button("Execute Generated SQL")

    st.subheader("Edit & Execute SQL")
    edited_sql = st.text_area(
        "Modify the SQL below:",
        value=st.session_state.generated_sql if st.session_state.generated_sql else "",
        height=150,
        key="edited_sql"
    )

    if st.button("Execute Edited SQL"):
        execute_query(edited_sql)

    if 'exe_gen_sql' in locals() and exe_gen_sql:
        execute_query(st.session_state.generated_sql)

def execute_query(sql):
    """Execute SQL and persist results for further interactions."""
    try:
        if security.sanitize_input(sql):
            df = st.session_state.oracle.execute_query(sql)
            if not df.empty:
                # Store the query context in session state
                st.session_state.executed_sql = sql
                st.session_state.query_df = df
                # Rerun the app so that main_interface displays results once
                st.experimental_rerun()
            else:
                handle_empty_query(sql)
        else:
            st.error("Query blocked by security rules")
    except Exception as e:
        st.error(f"Execution error: {str(e)}")

def show_chat_section():
    """Displays the chat section for interacting with the AI."""
    st.subheader("Chat with AI About the Database Output")

    # Retrieve persisted query context
    if "executed_sql" not in st.session_state or "query_df" not in st.session_state:
        st.error("No query context available. Please execute a query first.")
        return

    sql = st.session_state.executed_sql
    df = st.session_state.query_df

    chat_container = st.container()
    
    with chat_container:
        with st.form(key="chat_form"):
            user_question = st.text_input(
                "Ask a question about the data:", 
                value=st.session_state.chat_user_question,
                key="chat_question_input"
            )
            submit_button = st.form_submit_button("Ask")
        
        if submit_button and user_question:
            st.session_state.chat_user_question = user_question
            chat_prompt = create_chat_prompt(sql, df, user_question)
            
            with st.spinner("Processing your question..."):
                try:
                    chat_response = groq.analyze_data(chat_prompt)
                    if chat_response:
                        st.session_state.chat_ai_response = chat_response
                        st.session_state.chat_has_response = True
                    else:
                        st.error("No response received from AI.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        # Display the chat response only if it is non-empty
        if st.session_state.chat_has_response and st.session_state.chat_ai_response.strip() != "":
            st.subheader("Chat Response")
            st.markdown(st.session_state.chat_ai_response)
            
            if st.button("Clear response", key="clear_chat"):
                st.session_state.chat_has_response = False
                st.session_state.chat_ai_response = ""
                st.experimental_rerun()

def show_analysis_section():
    """Generates and displays analysis and recommendations."""
    if "executed_sql" not in st.session_state or "query_df" not in st.session_state:
        st.error("No query context available for analysis.")
        return

    sql = st.session_state.executed_sql
    df = st.session_state.query_df

    analysis_prompt = create_analysis_prompt(sql, df)
    with st.spinner("Analyzing data and generating recommendations..."):
        analysis_result = groq.analyze_data(analysis_prompt)
        if analysis_result:
            st.subheader("Analysis and Recommendations")
            st.write(analysis_result)
        else:
            st.error("No analysis received from AI.")

def handle_empty_query(sql):
    """Handles the case where the query returns no rows."""
    metadata = st.session_state.oracle.get_table_metadata(sql)
    if metadata is not None:
        st.info("Query executed successfully but returned no rows. Displaying table metadata:")
        st.dataframe(metadata)
    else:
        st.warning("Query executed successfully but returned no rows, and no metadata was available.")

def create_chat_prompt(sql, df, user_question):
    """Creates the prompt for the AI chat based on the executed SQL and its results."""
    return f"""
    **Task**: Answer the user's question using the SQL query results below. Follow these steps:
    1. Directly answer the question in natural language.
    2. If relevant, provide an Oracle 21c SQL query to explore further.
    3. Format SQL with ```sql code blocks```.

    **Executed SQL**:
    {sql}

    **Query Results**:
    {df.to_string()}

    **Question**:
    {user_question}
    """

def create_analysis_prompt(sql, df):
    """Creates the analysis prompt for the AI based on the executed SQL and its results."""
    return f"""
    Here is the query {sql} executed in Oracle Database 21c, based on that:
    Here is the output from the database:
    {df.to_string()}

    Analyze this data and provide:
    1. Insights: Key trends, patterns, or anomalies.
    2. Recommendations: Suggestions for further exploration or actions.
    3. New SQL Queries: Additional queries to dig deeper into the data, along with a description of their purpose.
    """

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
        data = np.random.rand(100, 1)  # Replace with real metrics if available
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
