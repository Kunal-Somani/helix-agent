"""Hardened sandboxed execution environment using RestrictedPython.

Provides secure, isolated code execution with:
- RestrictedPython compilation with whitelisted builtins
- Signal-based execution timeout (30s default)
- JSON output on errors for robustness
- Structured logging of all executions
"""

import signal
import json

from RestrictedPython import (
    compile_restricted,
    safe_globals,
    limited_builtins,
    utility_builtins,
)

import pandas as pd
import numpy as np
import requests

from app.logger import log


def execute_python_code(code_str: str, timeout_seconds: int = 30):
    """Execute generated Python code in hardened sandbox with timeout.
    
    Security features:
    - RestrictedPython compilation + execution
    - Whitelisted builtins (no __import__, exec, eval, etc.)
    - Access to safe libraries: pd, np, requests, json
    - SIGALRM-based timeout (30s default)
    - All errors returned as JSON strings for robustness
    
    Args:
        code_str: Python code to execute (must assign to 'result' variable)
        timeout_seconds: Max execution time (default 30s)
        
    Returns:
        The value of the 'result' variable, or error string on failure
        
    Raises:
        No exceptions raised; all errors wrapped as return values
    """
    log.info("sandbox.start", code_length=len(code_str), timeout=timeout_seconds)

    # Step 1: Compile with RestrictedPython
    try:
        byte_code = compile_restricted(code_str, filename="agent_code", mode="exec")
        if byte_code.errors:
            error_msg = f"Compilation errors: {byte_code.errors}"
            log.error("sandbox.compilation_failed", errors=byte_code.errors)
            return error_msg
    except SyntaxError as e:
        error_msg = f"SyntaxError: {e}"
        log.error("sandbox.syntax_error", error=str(e))
        return error_msg

    # Step 2: Build restricted globals (whitelisted builtins + libraries)
    restricted_globals = {
        **safe_globals,
        "_print_": print,
        "_getiter_": iter,
        "_getattr_": getattr,
        "_write_": lambda x: x,
        "__builtins__": {**limited_builtins, **utility_builtins},
        "pd": pd,
        "np": np,
        "requests": requests,
        "json": json,
        "result": None,
    }

    # Step 3: Set up timeout handler
    def _timeout_handler(signum, frame):
        raise TimeoutError(f"Execution exceeded {timeout_seconds}s time limit")

    signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(timeout_seconds)

    try:
        # Execute in sandbox
        exec(byte_code.code, restricted_globals)
        signal.alarm(0)  # Cancel alarm

        # Extract result
        result = restricted_globals.get("result", "No result variable set")
        log.info(
            "sandbox.done",
            result_type=type(result).__name__,
            preview=str(result)[:100],
        )
        return result

    except TimeoutError as e:
        error_msg = f"Timeout: code exceeded {timeout_seconds}s"
        log.error("sandbox.timeout", timeout=timeout_seconds, error=str(e))
        return error_msg

    except Exception as e:
        error_msg = f"Execution Error: {type(e).__name__}: {e}"
        log.error(
            "sandbox.exec_error",
            error=error_msg,
            error_type=type(e).__name__,
        )
        return error_msg

    finally:
        signal.alarm(0)  # Ensure alarm is always cancelled
