import os

content = '''import pytest
from agents.coding.parser import MarkdownParser
from agents.coding.exceptions import CodeGenerationError, PathTraversalError

def test_single_file_extraction():
    md = \"\"\"Some intro text.
<!-- path: src/main.py -->
```python
print("hello world")
```
Some outro text.
\"\"\"
    files = MarkdownParser.parse(md)
    assert len(files) == 1
    assert files[0]["path"] == "src/main.py"
    assert files[0]["language"] == "python"
    assert files[0]["content"] == 'print("hello world")'

def test_multi_file_extraction():
    md = \"\"\"
<!-- path: src/main.py -->
```python
def main(): pass
```
<!-- path: tests/test_main.py -->
```python
def test_main(): pass
```
\"\"\"
    files = MarkdownParser.parse(md)
    assert len(files) == 2
    assert files[0]["path"] == "src/main.py"
    assert files[1]["path"] == "tests/test_main.py"

def test_missing_path_marker():
    md = \"\"\"
```python
print("no path")
```
\"\"\"
    with pytest.raises(CodeGenerationError, match="No files found"):
        MarkdownParser.parse(md)

def test_empty_files_rejected():
    md = "Just some text without any code blocks."
    with pytest.raises(CodeGenerationError, match="No files found"):
        MarkdownParser.parse(md)

def test_unclosed_fence():
    md = \"\"\"
<!-- path: src/main.py -->
```python
print("unclosed")
\"\"\"
    with pytest.raises(CodeGenerationError, match="Unclosed code block"):
        MarkdownParser.parse(md)

def test_duplicate_path():
    md = \"\"\"
<!-- path: src/main.py -->
```python
print("1")
```
<!-- path: src/main.py -->
```python
print("2")
```
\"\"\"
    with pytest.raises(CodeGenerationError, match="Duplicate path found: src/main.py"):
        MarkdownParser.parse(md)

def test_path_traversal():
    bad_paths = [
        "../secret.py",
        "../../secret.py",
        "/etc/passwd",
        "~/secret",
        "C:/secret.py",
        "C:\\\\secret.py",
        "//server/share"
    ]
    for p in bad_paths:
        md = f\"\"\"
<!-- path: {p} -->
```python
print("hacked")
```
\"\"\"
        with pytest.raises(PathTraversalError):
            MarkdownParser.parse(md)

def test_exact_content_preservation():
    code = 'def foo():\\n    print("indented")\\n    return \"\"\"triple\\nquotes\"\"\"'
    md = f\"\"\"
<!-- path: test.py -->
```python
{code}
```
\"\"\"
    files = MarkdownParser.parse(md)
    assert files[0]["content"] == code

def test_empty_path():
    md = \"\"\"
<!-- path:   -->
```python
print("empty path")
```
\"\"\"
    with pytest.raises(PathTraversalError):
        MarkdownParser.parse(md)
'''

with open(r"c:\Users\KARTHIK\Downloads\FYP1\SEAM\tests\agents\coding\test_parser.py", "w", encoding="utf-8") as f:
    f.write(content)
