from typing import Any, Dict, List, Optional
import re

from pydantic import BaseModel

# Define input/output models for workflow steps
class WorkflowStepInput(BaseModel):
    session_id: Optional[str] = None
    form_data: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None

# Helper functions for code analysis
def count_lines(code: str) -> int:
    """Count non-empty lines of code."""
    return len([line for line in code.splitlines() if line.strip()])

def extract_input_data(input_data) -> Dict[str, Dict[str, Any]]:
    """Safely extract context and form_data from input data.
    This function handles different input types (WorkflowStepInput, dict, etc.)
    and safely extracts context and form_data, with proper default values.
    Args:
        input_data: The input data object, which can be WorkflowStepInput, dict, etc.
    Returns:
        Dict with 'context' and 'form_data' keys containing extracted data
    """
    # Initialize defaults
    result = {
        'context': {},
        'form_data': {},
        'session_id': None
    }
    # Log input data type for debugging
    logger.debug(f"Extracting data from input type: {type(input_data)}")
    # Handle WorkflowStepInput object
    if hasattr(input_data, 'context'):
        result['context'] = input_data.context or {}
    elif isinstance(input_data, dict) and 'context' in input_data:
        result['context'] = input_data['context'] or {}
    # Extract form_data
    if hasattr(input_data, 'form_data'):
        result['form_data'] = input_data.form_data or {}
    elif isinstance(input_data, dict) and 'form_data' in input_data:
        result['form_data'] = input_data['form_data'] or {}
    # Extract session_id
    if hasattr(input_data, 'session_id'):
        result['session_id'] = input_data.session_id
    elif isinstance(input_data, dict) and 'session_id' in input_data:
        result['session_id'] = input_data['session_id']
    # If input_data itself is a dict with no known structure, use it as form_data
    if isinstance(input_data, dict) and not (set(input_data.keys()) & {'context', 'form_data', 'session_id'}):
        result['form_data'] = input_data
    # Log extraction results for debugging
    logger.debug(f"Extracted data: context size={len(result['context'])}, form_data size={len(result['form_data'])}")
    return result

def analyze_function_complexity(code: str) -> Dict[str, Any]:
    """Analyze function complexity."""
    functions = {}
    lines = code.splitlines()
    current_func = None
    func_start = 0
    for i, line in enumerate(lines):
        if re.match(r'^\s*def\s+(\w+)', line):
            current_func = re.match(r'^\s*def\s+(\w+)', line).group(1)
            func_start = i
        elif current_func and (line.strip().startswith('return') or i == len(lines) - 1 or (re.match(r'^\s*def\s+(\w+)', line) and i > func_start)):
            if current_func not in functions:
                func_end = i
                func_code = '\n'.join(lines[func_start:func_end+1])
                # Calculate complexity (simple version)
                complexity = 1
                for ln in lines[func_start:func_end+1]:
                    if any(kw in ln for kw in ['if ', 'for ', 'while ', 'except', 'return']):
                        complexity += 1
                functions[current_func] = {
                    'lines': func_end - func_start + 1,
                    'complexity': complexity,
                    'has_docstring': any('"""' in ln or "'''" in ln for ln in lines[func_start:func_start+3]),
                    'has_typehints': ':' in lines[func_start]
                }
                if re.match(r'^\s*def\s+(\w+)', line):
                    current_func = re.match(r'^\s*def\s+(\w+)', line).group(1)
                    func_start = i
                else:
                    current_func = None
    return functions

def calculate_quality_metrics(code: str, language: str = "python") -> List[Dict[str, Any]]:
    """Calculate code quality metrics."""
    metrics = []
    # General metrics
    total_lines = count_lines(code)
    metrics.append({
        "metric": "Code Size",
        "score": f"{total_lines} lines",
        "description": "Total non-empty lines of code"
    })
    # PEP 8 compliance (simplified)
    pep8_violations = 0
    for line in code.splitlines():
        if len(line.rstrip()) > 100:  # Line too long
            pep8_violations += 1
        if "\t" in line:  # Tab character
            pep8_violations += 1
    pep8_score = max(0, 100 - (pep8_violations * 5))
    metrics.append({
        "metric": "Style Compliance",
        "score": f"{pep8_score}/100",
        "description": f"PEP 8 compliance score (approx)"
    })
    # Function analysis
    functions = analyze_function_complexity(code)
    avg_complexity = 0
    if functions:
        avg_complexity = sum(f['complexity'] for f in functions.values()) / max(1, len(functions))
    metrics.append({
        "metric": "Complexity",
        "score": f"{avg_complexity:.1f}",
        "description": "Average cyclomatic complexity"
    })
    # Documentation score
    doc_ratio = 0
    if functions:
        doc_ratio = sum(1 for f in functions.values() if f['has_docstring']) / max(1, len(functions))
    doc_score = int(doc_ratio * 100)

    metrics.append({
        "metric": "Documentation",
        "score": f"{doc_score}/100",
        "description": f"{doc_score}% of functions have docstrings"
    })
    # Type hints
    typehint_ratio = 0
    if functions:
        typehint_ratio = sum(1 for f in functions.values() if f['has_typehints']) / max(1, len(functions))
    typehint_score = int(typehint_ratio * 100)
    metrics.append({
        "metric": "Type Hints",
        "score": f"{typehint_score}/100",
        "description": f"{typehint_score}% of functions have type hints"
    })
    # Overall quality score
    overall = (pep8_score + (100 - min(avg_complexity * 10, 100)) + doc_score + typehint_score) / 4
    metrics.append({
        "metric": "Overall Quality",
        "score": f"{overall:.1f}/100",
        "description": "Combined quality score"
    })
    return metrics

def generate_improved_code(code: str, language: str = "python") -> str:
    """Generate improved version of the code with better practices."""
    # For demonstration purposes, we'll make some simple improvements
    improved = []
    functions = analyze_function_complexity(code)
    lines = code.splitlines()

    i = 0
    while i < len(lines):
        line = lines[i]
        # Add docstrings to functions without them
        if re.match(r'^\s*def\s+(\w+)', line):
            func_name = re.match(r'^\s*def\s+(\w+)', line).group(1)
            improved.append(line)
            i += 1
            # Check if next line is a docstring
            has_docstring = False
            if i < len(lines) and ('"""' in lines[i] or "'''" in lines[i]):
                has_docstring = True
            if not has_docstring and func_name in functions:
                indent = re.match(r'^(\s*)', line).group(1)
                improved.append(f"{indent}    \"\"\"Function {func_name} does...\n")
                improved.append(f"{indent}    \n")
                improved.append(f"{indent}    Returns:\n")
                improved.append(f"{indent}        Result of the function\n")
                improved.append(f"{indent}    \"\"\"\n")
        # Replace bare except with specific exception
        elif 'except:' in line:
            improved.append(line.replace('except:', 'except Exception:'))
        # Add comments to complex code blocks
        elif any(kw in line for kw in ['if ', 'for ', 'while ']):
            improved.append(line)
            # Add explanatory comment for complex conditions
            if line.count('and') > 1 or line.count('or') > 1:
                indent = re.match(r'^(\s*)', line).group(1)
                improved.append(f"{indent}# Complex condition to handle...")
        else:
            improved.append(line)
        i += 1
    return '\n'.join(improved)

def generate_improvements_summary(original_code: str, improved_code: str) -> str:
    """Generate a summary of improvements made to the code."""
    # Analyze both original and improved code
    original_metrics = calculate_quality_metrics(original_code)
    improved_metrics = calculate_quality_metrics(improved_code)
    # Extract key metrics
    original_doc_score = next((m for m in original_metrics if m["metric"] == "Documentation"), {}).get("score", "0/100")
    improved_doc_score = next((m for m in improved_metrics if m["metric"] == "Documentation"), {}).get("score", "0/100")
    original_quality = next((m for m in original_metrics if m["metric"] == "Overall Quality"), {}).get("score", "0/100")
    improved_quality = next((m for m in improved_metrics if m["metric"] == "Overall Quality"), {}).get("score", "0/100")
    # Generate summary markdown
    summary = f"""## Code Improvements Summary

### Changes Made

1. **Added Documentation**: Improved documentation coverage from {original_doc_score} to {improved_doc_score}
2. **Error Handling**: Replaced bare `except` clauses with specific exception handling
3. **Code Clarity**: Added explanatory comments to complex conditions
4. **Overall Quality**: Improved from {original_quality} to {improved_quality}

### Benefits

* Increased maintainability
* Better readability
* More robust error handling
* Easier to understand for other developers

Review the improved code and check if there are any additional changes you'd like to make.
"""
    return summary