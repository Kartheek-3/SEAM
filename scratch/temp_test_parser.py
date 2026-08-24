import pytest
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
    md = md.replace("\\\"\\\"\\\"", '\"\"\"') # Fix syntax manually for now, actually I'll just use standard strings

