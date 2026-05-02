"""Sandboxed execution environment using RestrictedPython."""

from RestrictedPython import compile_restricted

from app.logger import log


class SandboxExecutor:
    """Execute code safely in a restricted environment."""

    @staticmethod
    def execute_code(code: str, context: dict = None) -> str:
        """Execute code in a sandboxed environment.
        
        Compiles code using RestrictedPython and executes in an isolated
        namespace. Returns the 'result' variable from the executed code.
        
        Args:
            code: Python code to execute (must have 'result' variable)
            context: Optional initial context dictionary
            
        Returns:
            The value of the 'result' variable after execution
            
        Raises:
            ValueError: If code compilation fails
            NameError: If 'result' variable not defined in code
            Exception: Any exception raised during code execution
        """
        context = context or {}

        try:
            log.info("sandbox.compiling", code_length=len(code))

            # Compile code with RestrictedPython
            byte_code = compile_restricted(code, "<string>", "exec")

            if byte_code.errors:
                log.error("sandbox.compilation_failed", errors=byte_code.errors)
                raise ValueError(
                    f"Code compilation failed: {byte_code.errors}"
                )

            # Execute in restricted environment
            exec(byte_code.code, context)

            # Extract result variable
            if "result" not in context:
                raise NameError(
                    "Code did not assign to 'result' variable"
                )

            result = context["result"]
            log.info(
                "sandbox.execution_success",
                result_type=type(result).__name__,
            )

            return result

        except SyntaxError as e:
            log.error("sandbox.syntax_error", error=str(e))
            raise
        except Exception as e:
            log.error(
                "sandbox.execution_error",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise


def execute_python_code(python_code: str):
    """Execute generated Python code and return result.
    
    This function is designed to be executor-safe for use with
    asyncio.loop.run_in_executor().
    
    Args:
        python_code: Python code with 'result' variable
        
    Returns:
        The value of the 'result' variable
        
    Raises:
        ValueError: If code compilation fails
        NameError: If 'result' not defined
        Exception: If execution fails
    """
    executor = SandboxExecutor()
    return executor.execute_code(python_code)


# Global instance for synchronous access
sandbox = SandboxExecutor()
