from ai_agent.modules.db import MySQLDatabase
from ai_agent.modules.llm import add_cap_ref, prompt
import os
import dotenv

dotenv.load_dotenv()
assert os.environ.get("DATABASE_URL"), "DB_URL not found in .env file"
assert os.environ.get("AZURE_OPENAI_KEY"), "key not found in .env file"
assert os.environ.get("AZURE_OPENAI_ENDPOINT"), "endpoint not found in .env file"

DB_URL = os.environ.get("DATABASE_URL")
AZURE_OPENAI_KEY = os.environ.get("AZURE_OPENAI_KEY")
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")


def main():
    # parse prompt param using arg parse

    # connect to db using with statement and create a db_manager
    with MySQLDatabase() as db:
        db.connect_with_url(DB_URL)
        user_table = db.get_all("CUSTOMER")
        print("user_tables", user_table)
        
        # call db_manager-get_table_definition_for_prompt() to get tables in prompt ready form
        tables_prompt = db.get_table_definitions_for_prompt()
        
        # create two blank calls to llm.add_cap_ref() that update our current prompt passed in from cli
        prompt_with_tables = add_cap_ref(prompt, "", "TABLES", tables_prompt)
        prompt_with_tables_and_sql = add_cap_ref(prompt_with_tables, "", "SQL", "")
        
        # call llm.prompt to get a prompt_response variable
        prompt_response = prompt(prompt_with_tables_and_sql)
        
        # parse sql response from prompt_response using SQL_QUERY_DELIMITER
        sql_queries = prompt_response.split(SQL_QUERY_DELIMITER)
        
        # call db_manager.run_sql() with the parsed sql
        for query in sql_queries:
            db.run_sql(query.strip())
            
    pass


if __name__ == "__main__":
    main()
