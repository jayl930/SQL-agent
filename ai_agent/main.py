from ai_agent.modules.db import MySQLDatabase
from ai_agent.modules import llm
import os
import dotenv
import argparse
from autogen import (
    AssistantAgent,
    UserProxyAgent,
    GroupChat,
    GroupChatManager,
    config_list_from_json,
    config_list_from_models,
)


dotenv.load_dotenv()
assert os.environ.get("DATABASE_URL"), "DB_URL not found in .env file"
assert os.environ.get("AZURE_OPENAI_KEY"), "key not found in .env file"
assert os.environ.get("AZURE_OPENAI_ENDPOINT"), "endpoint not found in .env file"

DB_URL = os.environ.get("DATABASE_URL")
AZURE_OPENAI_KEY = os.environ.get("AZURE_OPENAI_KEY")
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")

TABLE_DEFINITIONS_CAP_REF = "TABLE_DEFINITIONS"
RESPONSE_FORMAT_CAP_REF = "RESPONSE_FORMAT"

SQL_DELIMITER = "---------"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", help="The prompt for the AI")
    args = parser.parse_args()

    if not args.prompt:
        print("Please provide a prompt")
        return

    prompt = f"Fulfill this database query: {args.prompt}. "

    with MySQLDatabase() as db:
        db.connect_with_url(DB_URL)

        tables_prompt = db.get_table_definitions_for_prompt()

        prompt = llm.add_cap_ref(
            prompt,
            f"Use these {TABLE_DEFINITIONS_CAP_REF} to satisfy the database query.",
            TABLE_DEFINITIONS_CAP_REF,
            tables_prompt,
        )

        prompt = llm.add_cap_ref(
            prompt,
            f"\n\nRespond in this format {RESPONSE_FORMAT_CAP_REF}. Replace the text between <> with it's request. I need to be able to easily parse the sql query from your response.",
            RESPONSE_FORMAT_CAP_REF,
            f"""<explanation of the sql query>
{SQL_DELIMITER}
<sql query exclusively as raw text>""",
        )

        print("\n\n-------- PROMPT --------")
        print(prompt)

        prompt_response = llm.prompt(prompt)

        print("\n\n-------- PROMPT RESPONSE --------")
        print(prompt_response)

        sql_start_index = prompt_response.find("SELECT")
        explanation_keywords = ["This query", "Please note"]
        sql_end_index = min(
            [
                prompt_response.find(kw, sql_start_index)
                for kw in explanation_keywords
                if prompt_response.find(kw, sql_start_index) != -1
            ]
            + [len(prompt_response)]
        )

        if sql_start_index != -1 and sql_end_index != -1:
            sql_query = prompt_response[sql_start_index:sql_end_index].strip()
        else:
            print("SQL query format not found in prompt_response")
            sql_query = None

        print(f"\n\n-------- PARSED SQL QUERY --------")
        print(sql_query)

        if sql_query is not None:
            result = db.run_sql(sql_query)
            print("\n\n======== AI AGENT RESPONSE ========")
            print(result)
        else:
            print("No SQL query to run")

    pass


if __name__ == "__main__":
    main()
