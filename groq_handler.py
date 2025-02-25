import os
import re
import streamlit as st
from groq import Groq
from dotenv import load_dotenv
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


load_dotenv()

class GroqHandler:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.system_prompt =  """
**System Instructions for SQL Query Generation**

1. **Purpose**: You are an Oracle SQL expert specializing in Oracle Database 21c.

2. **Guidelines**:
   - Use **strict Oracle 21c SQL syntax**.
   - Always use the schema name prefix (e.g., `<schema_name>.<table_name>`).
   - Always write keywords in **UPPERCASE**.
   - End every query with a semicolon (`;`).
   - Only generate **SELECT** statements (no INSERT, UPDATE, DELETE, or DDL queries).
   - Use **ANSI SQL JOIN syntax** when applicable.
   - Do not include any explanations, comments, or non-SQL text in your output. Only output valid Oracle SQL.

3. **Formatting Rules**:
   - Use consistent indentation for readability:
     - Each clause (e.g., SELECT, FROM, WHERE) starts on a new line.
     - Use proper indentation for nested queries or complex clauses.
   - Ensure queries are syntactically valid and executable in an Oracle 21c environment.

4. **Examples**:
   - Simple query:  
     ```sql
     SELECT * 
     FROM HR.EMPLOYEES;
     ```
   - Query with WHERE condition:  
     ```sql
     SELECT EMPLOYEE_ID, FIRST_NAME, LAST_NAME 
     FROM HR.EMPLOYEES 
     WHERE DEPARTMENT_ID = 10;
     ```
   - Query with JOIN:  
     ```sql
     SELECT E.EMPLOYEE_ID, E.FIRST_NAME, D.DEPARTMENT_NAME 
     FROM HR.EMPLOYEES E 
     INNER JOIN HR.DEPARTMENTS D 
     ON E.DEPARTMENT_ID = D.DEPARTMENT_ID 
     WHERE E.SALARY > 5000;
     ```

5. **Prohibited Output**:
   - Avoid explanations such as "Here is the SQL query for your input".
   - Avoid unnecessary metadata, headers, or annotations.
   - Avoid any query or syntax that is not compliant with Oracle 21c.

6. **Output Behavior**:
   - Always ensure the query matches the intent provided by the user in natural language.
   - If a specific schema or table is not provided, assume `<schema_name>` and `<table_name>` as placeholders.
   - For ambiguous inputs, make reasonable assumptions and generate valid SQL.
   
7Rule Update: "Do not add backslashes (\) before special characters like underscores (_) in SQL queries unless required by Oracle syntax.

"""

    def generate_sql(self, natural_language: str) -> Optional[str]:
        try:
            logging.info(f"Received natural language input: {natural_language}")
            response = self.client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Convert to Oracle SQL: {natural_language}"}
                ],
                temperature=0.2
            )
            raw_output = response.choices[0].message.content.strip()
            logging.info(f"Received SQL output: {raw_output}")
            clean_sql = self._clean_output(raw_output)
            return clean_sql
        except Exception as e:
            logging.error(f"Error in generate_sql: {str(e)}")
            st.error(f"API Error: {str(e)}")
            return None

    
    def analyze_data(self, data_prompt: str) -> Optional[str]:
        try:
            logging.info("Sending request to Groq API with prompt:")
            logging.info(data_prompt)
            response = self.client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[
                    {"role": "system", "content": (
                        "You are a Oracle database 21 assistant. Analyze the provided data and provide insights, recommendations, "
                        "and new SQL queries to explore further. Avoid any query or syntax that is not compliant with Oracle 21c."
                    )},
                    {"role": "user", "content": data_prompt}
                ],
                temperature=0.2
            )
            raw_output = response.choices[0].message.content.strip()
            logging.info("Received raw output from Groq API:")
            logging.info(raw_output)
            if not raw_output:
                st.error("Empty response from Groq API.")
                return None
            # Clean and return the output
            clean_output = self._clean_output(raw_output)
            logging.info("Cleaned output:")
            logging.info(clean_output)
            return clean_output
        except Exception as e:
            st.error(f"API Error: {str(e)}")
            logging.error("Exception in analyze_data:", exc_info=True)
            return None



    def _clean_output(self, raw_output: str) -> str:
        # Remove unwanted backslashes from the raw output
        return raw_output.replace("\\", "")
