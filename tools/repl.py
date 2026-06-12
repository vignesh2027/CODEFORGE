import os
import subprocess
import sys
import tempfile
from typing import Tuple


def execute_python_code(code: str, timeout: int = 30) -> Tuple[bool, str]:
    """Run code in an isolated subprocess and return (success, output)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        tmp = f.name

    try:
        result = subprocess.run(
            [sys.executable, tmp],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode == 0:
            return True, result.stdout.strip() or "(no output)"
        error = (result.stderr or result.stdout or "unknown error").strip()
        return False, error
    except subprocess.TimeoutExpired:
        return False, f"Execution timed out after {timeout}s"
    except Exception as e:
        return False, str(e)
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass
