"""LLM Agent service for data analysis quiz solving.

Uses Hugging Face Inference API to:
1. Extract task info (submission URL, problem description, data files)
2. Generate Python code that solves the problem
3. Return orchestration results for execution
"""

import json
import re

import requests
from huggingface_hub import InferenceClient
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.config import settings
from app.logger import log

client = InferenceClient(token=settings.HF_API_TOKEN, model=settings.HF_MODEL_ID)


def _extract_json_from_response(text: str) -> dict:
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        text = match.group(1)
    
    text = text.strip()
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        text = text[start:end+1]
        
    return json.loads(text)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(requests.HTTPError),
)
def _extract_task(task_text: str, current_url: str) -> dict:
    from urllib.parse import urlparse

    base = f"{urlparse(current_url).scheme}://{urlparse(current_url).netloc}"
    
    system_prompt = (
        "You are a precise data extraction agent. "
        "Extract structured information from the raw webpage text. "
        f"The page contains a data analysis quiz. Current page URL: {current_url}. "
        f"Base domain: {base}. For any relative URL starting with /, prepend the base domain. "
        "You must output ONLY valid JSON with exactly the following keys: "
        '"submission_url", "problem_description", "data_file_url", "expected_answer_type". '
        'If there is no data file, set "data_file_url" to an empty string. '
        '"expected_answer_type" must be one of: "number", "string", "json". '
        "Do not include any other text or explanation."
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Extract task info from this page:\n\n{task_text[:8000]}"}
    ]
    
    response = client.chat_completion(messages=messages, max_tokens=1024)
    content = response.choices[0].message.content
    
    return _extract_json_from_response(content)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(requests.HTTPError),
)
def _generate_code(
    problem_description: str, data_file_url: str, expected_type: str
) -> dict:
    system_prompt = (
        "You are an expert Python data analyst. "
        "Rules: always import pandas as pd, numpy as np, requests, json at the top. "
        "Always download remote files with requests.get() before reading them. "
        "Always save the final answer into a variable named result. "
        "The result must be a primitive value (int, float, str), not a DataFrame or list. "
        "You must output ONLY valid JSON with exactly the following keys: "
        '"python_code" (containing the complete runnable code) and "explanation" '
        '(one sentence describing the approach). Do not include any other text or explanation.'
    )
    
    user_content = f"Problem: {problem_description}"
    if data_file_url:
        user_content += f"\n\nData file URL to download: {data_file_url}"
    user_content += f"\n\nExpected answer type: {expected_type}"
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]
    
    response = client.chat_completion(messages=messages, max_tokens=2048)
    content = response.choices[0].message.content
    
    return _extract_json_from_response(content)


def solve_quiz_task(task_text: str, current_url: str) -> tuple[str, str, str]:
    from app.main import AGENT_LLM_LATENCY
    
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

    log.info("agent.generating_code", problem=problem_description[:80])
    with AGENT_LLM_LATENCY.labels(call_type="code_gen").time():
        code_info = _generate_code(problem_description, data_file_url, expected_type)
    
    python_code = code_info["python_code"]
    explanation = code_info["explanation"]
    
    log.info("agent.code_ready", explanation=explanation)

    return submission_url, python_code, explanation
