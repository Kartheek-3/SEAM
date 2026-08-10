"""
Tests for RAG Chunker
"""

from rag.chunker import Chunker

def test_clean_text():
    chunker = Chunker()
    dirty_text = "This is a \x00 test.\n\n\nToo many newlines."
    clean = chunker.clean_text(dirty_text)
    assert "\x00" not in clean
    assert "\n\n\n" not in clean
    assert "This is a  test" in clean or "This is a test" in clean

def test_split_text():
    chunker = Chunker(chunk_size=10, chunk_overlap=2)
    # Generate 24 words
    text = " ".join([f"word{i}" for i in range(24)])
    
    chunks = chunker.split_text(text)
    
    # 24 words, step=8, chunk_size=10
    # chunk 1: 0-10
    # chunk 2: 8-18
    # chunk 3: 16-24 (8 words)
    assert len(chunks) == 3
    assert len(chunks[0].split()) == 10
    assert len(chunks[1].split()) == 10
    assert len(chunks[2].split()) <= 10
    
    # Check overlap
    chunk1_words = chunks[0].split()
    chunk2_words = chunks[1].split()
    assert chunk1_words[-2:] == chunk2_words[:2]
