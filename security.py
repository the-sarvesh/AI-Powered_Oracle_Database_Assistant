import re
from cx_Oracle import DatabaseError

class SecurityManager:
    @staticmethod
    def sanitize_input(sql: str) -> bool:
        # """
        # Sanitizes input SQL by checking for forbidden patterns.
        # Allows SELECT queries and blocks potentially harmful operations.
        # """
        # sql_upper = sql.upper().strip()

        # # Allow only SELECT statements
        # if not sql_upper.startswith("SELECT"):
        #     print("Only SELECT statements are allowed.")
        #     return False

        # # Block dangerous patterns
        # forbidden_patterns = [
        #     r";\s*--",        # Inline comment after a semicolon
        #     r"EXEC\s",        # EXEC calls
        #     r"XP_",           # Extended stored procedures (irrelevant to Oracle)
        #     r"\b(DROP|DELETE|UPDATE|INSERT)\b"  # DDL and DML commands
        # ]
        
        # if any(re.search(pattern, sql, re.IGNORECASE) for pattern in forbidden_patterns):
        #     print("Query contains forbidden patterns.")
        #     return False

        return True
