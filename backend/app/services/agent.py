"""LLM Agent service for data analysis quiz solving.

Uses Claude (Anthropic) with tool-based orchestration to:
1. Extract task info (submission URL, problem description, data files)
2. Generate Python code that solves the problem
3. Return orchestration results for execution
"""

import anthropic
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.config import settings
from app.logger import log


client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

# Tool schema for data extraction
EXTRACT_TOOL = {
    "name": "extract_task_info",
    "description": "Extract the submission URL and structured problem details from raw webpage text.",
    "input_schema": {
        "type": "object",
        "properties": {
            "submission_url": {
                "type": "string",
                "description": "The full absolute URL to POST the answer to.",
            },
            "problem_description": {
                "type": "string",
                "description": "Clean natural language description of what must be solved.",
            },
            "data_file_url": {
                "type": "string",
                "description": "URL of any CSV or data file to download. Empty string if none.",
            },
            "expected_answer_type": {
                "type": "string",
                "enum": ["number", "string", "json"],
                "description": "The type of the final answer value.",
            },
        },
        "required": ["submission_url", "problem_description", "expected_answer_type"],
    },
}

# Tool schema for code generation
CODE_TOOL = {
    "name": "generate_solution_code",
    "description": "Write Python code that solves the data analysis problem and stores the answer in a variable named result.",
    "input_schema": {
        "type": "object",
        "properties": {
            "python_code": {
                "type": "string",
                "description": "Complete, self-contained Python code. Must assign the final answer to a variable named result.",
            },
            "explanation": {
                "type": "string",
                "description": "One sentence describing the approach taken.",
            },
        },
        "required": ["python_code", "explanation"],
    },
}


def _parse_tool_result(response, tool_name: str) -> dict:
    """Extract tool use block from Anthropic response.
    
    Args:
        response: The response from client.messages.create()
        tool_name: Name of the tool to find in the response
        
    Returns:
        The input dictionary from the tool use block
        
    Raises:
        ValueError: If the tool was not called in the response
    """
    for block in response.content:
        if block.type == "tool_use" and block.name == tool_name:
            return block.input
    raise ValueError(f"Tool {tool_name} was not called in response")


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(
        (anthropic.APIError, anthropic.RateLimitError)
    ),
)
def _extract_task(task_text: str, current_url: str) -> dict:
    """Extract task information from webpage text using Claude.
    
    Uses Claude with the extract_task_info tool to parse:
    - Submission URL
    - Problem description
    - Data file URLs
    - Expected answer type
    
    Args:
        task_text: Raw HTML/text content of the task page
        current_url: Current page URL for context and relative URL resolution
        
    Returns:
        Dictionary with keys: submission_url, problem_description, 
        data_file_url, expected_answer_type
        
    Raises:
        ValueError: If extraction tool was not called
        anthropic.APIError: If API call fails (retried up to 3 times)
    """
    from urllib.parse import urlparse

    base = f"{urlparse(current_url).scheme}://{urlparse(current_url).netloc}"

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        tools=[EXTRACT_TOOL],
        tool_choice={"type": "tool", "name": "extract_task_info"},
        system=(
            "You are a precise data extraction agent. Extract structured information "
            "from raw webpage text. The page contains a data analysis quiz. "
            f"Current page URL: {current_url}. "
            f"Base domain: {base}. "
            "For any relative URL starting with /, prepend the base domain."
        ),
        messages=[
            {
                "role": "user",
                "content": f"Extract task info from this page:\n\n{task_text[:8000]}",
            }
        ],
    )

    return _parse_tool_result(response, "extract_task_info")


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(
        (anthropic.APIError, anthropic.RateLimitError)
    ),
)
def _generate_code(
    problem_description: str, data_file_url: str, expected_type: str
) -> dict:
    """Generate Python code to solve the data analysis problem.
    
    Uses Claude with the generate_solution_code tool to write runnable
    Python code that:
    - Imports required libraries (pandas, numpy, requests, json)
    - Downloads any remote data files
    - Solves the problem
    - Stores the answer in a variable named 'result'
    
    Args:
        problem_description: Natural language description of what to solve
        data_file_url: URL of CSV/data file to download (empty string if none)
        expected_type: Expected answer type ('number', 'string', or 'json')
        
    Returns:
        Dictionary with keys: python_code, explanation
        
    Raises:
        ValueError: If code generation tool was not called
        anthropic.APIError: If API call fails (retried up to 3 times)
    """
    user_content = f"Problem: {problem_description}"
    if data_file_url:
        user_content += f"\n\nData file URL to download: {data_file_url}"
    user_content += f"\n\nExpected answer type: {expected_type}"

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        tools=[CODE_TOOL],
        tool_choice={"type": "tool", "name": "generate_solution_code"},
        system=(
            "You are an expert Python data analyst. "
            "Rules: always import pandas as pd, numpy as np, requests, json at the top. "
            "Always download remote files with requests.get() before reading them. "
            "Always save the final answer into a variable named result. "
            "The result must be a primitive value (int, float, str), not a DataFrame or list."
        ),
        messages=[{"role": "user", "content": user_content}],
    )

    return _parse_tool_result(response, "generate_solution_code")


def solve_quiz_task(task_text: str, current_url: str) -> tuple[str, str, str]:
    """Orchestrate task solving: extract info and generate code.
    
    Two-phase approach:
    1. Extract task information using _extract_task()
       - Gets submission URL, problem description, data files
    2. Generate solution code using _generate_code()
       - Creates runnable Python code with result variable
    
    With metrics:
    - AGENT_LLM_LATENCY tracks Anthropic API call duration
    
    Args:
        task_text: Raw HTML/text content of the task page
        current_url: Current page URL
        
    Returns:
        Tuple of (submission_url, python_code, explanation)
        
    Raises:
        ValueError: If extraction or code generation fails
        anthropic.APIError: If API calls fail (retried internally)
    """
    from app.main import AGENT_LLM_LATENCY
    
    # Phase 1: Extract task information
    log.info("agent.extracting", url=current_url)
    with AGENT_LLM_LATENCY.labels(call_type="extract").time():
        task_info = _extract_task(task_text, current_url)
    
    submission_url = task_info["submission_url"]
    problem_description = task_info["problem_description"]
    data_file_url = task_info.get("data_file_url", "")
    expected_type = task_info.get("expected_answer_type", "string")
    
    log.info(
        "agent.extraction_done",
        submission_url=submission_url,
        answer_type=expected_type,
    )

    # Phase 2: Generate solution code
    log.info("agent.generating_code", problem=problem_description[:80])
    with AGENT_LLM_LATENCY.labels(call_type="code_gen").time():
        code_info = _generate_code(problem_description, data_file_url, expected_type)
    
    python_code = code_info["python_code"]
    explanation = code_info["explanation"]
    
    log.info("agent.code_ready", explanation=explanation)

    return submission_url, python_code, explanation
