from dataclasses import dataclass
import sys
from dotenv import load_dotenv
import os
from typing import Any, Dict, List, Callable
from openai import AzureOpenAI


load_dotenv()

assert os.getenv("AZURE_OPENAI_KEY"), "AZURE_OPENAI_KEY not found in .env file"
assert os.getenv(
    "AZURE_OPENAI_ENDPOINT"
), "AZURE_OPENAI_ENDPOINT not found in .env file"


azure_client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version="2023-05-15",
)
deployment_name = os.getenv("AZURE_DEPLOYMENT_NAME")

# ------------------ helpers ------------------


def safe_get(data, dot_chained_keys):
    """
    {'a': {'b': [{'c': 1}]}}
    safe_get(data, 'a.b.0.c') -> 1
    """
    keys = dot_chained_keys.split(".")
    for key in keys:
        try:
            if isinstance(data, list):
                data = data[int(key)]
            else:
                data = data[key]
        except (KeyError, TypeError, IndexError):
            return None
    return data


def response_parser(response: Dict[str, Any]):
    return safe_get(response, "choices.0.message.content")


# ------------------ content generators ------------------


def prompt(prompt: str, model: str = deployment_name) -> str:

    response = azure_client.chat.completions.create(
        model=model,
        messages=[
            # {"role": "system", "content": instructions},
            {"role": "user", "content": prompt}
        ],
    )

    return response.choices[0].message.content


def add_cap_ref(
    prompt: str, prompt_suffix: str, cap_ref: str, cap_ref_content: str
) -> str:
    """
    Attaches a capitalized reference to the prompt.
    Example
        prompt = 'Refactor this code.'
        prompt_suffix = 'Make it more readable using this EXAMPLE.'
        cap_ref = 'EXAMPLE'
        cap_ref_content = 'def foo():\n    return True'
        returns 'Refactor this code. Make it more readable using this EXAMPLE.\n\nEXAMPLE\n\ndef foo():\n    return True'
    """

    new_prompt = f"""{prompt} {prompt_suffix}\n\n{cap_ref}\n\n{cap_ref_content}"""

    return new_prompt
