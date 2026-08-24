import re
import os
from typing import List, Dict, Any
from agents.coding.exceptions import CodeGenerationError, PathTraversalError
from backend.schemas.enums import ArtifactType

class MarkdownParser:
    """
    Deterministic Markdown parser for extracting CodingAgent artifacts from LLM responses.
    Expects HTML path markers immediately followed by fenced code blocks.
    Example:
    <!-- path: src/main.py -->
    ```python
    print("hello")
    ```
    """
    
    @staticmethod
    def _validate_path(path: str) -> None:
        if not path or not path.strip():
            raise PathTraversalError("File path cannot be empty.")
            
        normalized = path.replace("\\", "/")
        
        if normalized.startswith("/") or normalized.startswith("~"):
            raise PathTraversalError(f"Absolute paths are not allowed: {path}")
            
        # Detect Windows drives e.g. C:/ or C:\
        if re.match(r"^[a-zA-Z]:[/|\\]", normalized):
            raise PathTraversalError(f"Windows absolute paths are not allowed: {path}")
            
        # Detect UNC paths e.g. //server/share
        if normalized.startswith("//"):
            raise PathTraversalError(f"UNC paths are not allowed: {path}")

        parts = normalized.split("/")
        if ".." in parts:
            raise PathTraversalError(f"Path traversal is not allowed: {path}")

    @staticmethod
    def parse(markdown_text: str) -> List[Dict[str, Any]]:
        if not markdown_text or not markdown_text.strip():
            raise CodeGenerationError("LLM returned empty response.")
            
        # We need a robust deterministic parser rather than simple regex since regex is fragile on unclosed fences.
        # However, a robust regex handles 99% if strictly defined. Let's use string manipulation state machine.
        
        files = []
        lines = markdown_text.split("\n")
        
        current_path = None
        current_lang = None
        current_content = []
        in_code_block = False
        
        # We look for path markers: <!-- path: src/main.py -->
        path_pattern = re.compile(r"<!--\s*path:\s*(.*?)\s*-->", re.IGNORECASE)
        
        for line in lines:
            if not in_code_block:
                path_match = path_pattern.search(line)
                if path_match:
                    if current_path is not None:
                        # Found a new path marker before closing the previous block or finding its block
                        raise CodeGenerationError(f"Found new path marker before code block for {current_path}")
                    current_path = path_match.group(1).strip()
                    continue
                
                if current_path is not None and line.strip().startswith("```"):
                    in_code_block = True
                    current_lang = line.strip()[3:].strip()
                    current_content = []
                    continue
            else:
                if line.strip() == "```":
                    # Close code block
                    files.append({
                        "path": current_path,
                        "language": current_lang or "text",
                        "content": "\n".join(current_content),
                        "artifact_type": ArtifactType.CODE
                    })
                    current_path = None
                    current_lang = None
                    current_content = []
                    in_code_block = False
                else:
                    current_content.append(line)
                    
        if in_code_block:
            raise CodeGenerationError(f"Unclosed code block for path {current_path}")
            
        if current_path is not None and not in_code_block:
            raise CodeGenerationError(f"Missing code block for path {current_path}")
            
        if not files:
            raise CodeGenerationError("No files found in output. Ensure you use <!-- path: filename --> followed by a fenced code block.")
            
        # Validate paths
        seen_paths = set()
        for f in files:
            MarkdownParser._validate_path(f["path"])
            if f["path"] in seen_paths:
                raise CodeGenerationError(f"Duplicate path found: {f['path']}")
            seen_paths.add(f["path"])
            
            if not f["content"].strip():
                raise CodeGenerationError(f"Generated file '{f['path']}' is empty.")
                
        return files
