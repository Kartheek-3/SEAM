"""
Document Chunker
"""

import re
from typing import List

class Chunker:
    """
    Handles splitting text into manageable chunks.
    Currently implements a simple recursive character-based strategy.
    """

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def clean_text(self, text: str) -> str:
        """Sanitizes text by normalizing whitespace and removing null bytes."""
        text = text.replace("\x00", "")
        # Normalize whitespace (replace multiple newlines/spaces with max two newlines or one space)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def split_text(self, text: str) -> List[str]:
        """
        Splits text into chunks respecting the chunk_size and overlap.
        For simplicity, this splits by words rather than strict tokens.
        """
        text = self.clean_text(text)
        if not text:
            return []

        # Simple word-based splitting (approximate tokenization)
        words = text.split()
        chunks = []
        i = 0
        
        while i < len(words):
            # Take chunk_size words
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = " ".join(chunk_words)
            chunks.append(chunk_text)
            
            # Advance by chunk_size - overlap
            step = max(1, self.chunk_size - self.chunk_overlap)
            i += step
            
        return chunks
