"""Compare different chunking methods"""
from src.modules.chunking.smart_chunker import SmartChunker

def compare_methods():
    # Test text with complex structure
    text = """CHƯƠNG 1: GIỚI THIỆU

Chí Phèo là một tác phẩm văn học nổi tiếng. Câu chuyện kể về cuộc đời bi thảm của một người nông dân.

1.1 Bối cảnh xã hội
Việt Nam trước năm 1945 là một xã hội phong kiến lạc hậu. Người nông dân chiếm đa số dân số nhưng không có ruộng đất.

1.2 Nhân vật chính
Chí Phèo vốn là người hiền lành. Sau khi bị hãm hại, hắn trở thành kẻ vô loại.

CHƯƠNG 2: PHÂN TÍCH TÁC PHẨM

Tác phẩm thể hiện tài năng của Nam Cao trong việc khắc họa tâm lý nhân vật."""

    print("📊 CHUNKING METHOD COMPARISON")
    print("="*60)
    print(f"Original text: {len(text)} characters\n")
    
    # Method 1: Simple fixed-size chunks
    simple_chunks = []
    chunk_size = 200
    for i in range(0, len(text), chunk_size):
        simple_chunks.append(text[i:i+chunk_size])
    
    print("❌ SIMPLE FIXED-SIZE CHUNKING:")
    print(f"Chunks: {len(simple_chunks)}")
    print(f"Problem: Cuts in middle of sentences!")
    print(f"Example: '{simple_chunks[1][-20:]}...'")
    
    # Method 2: Smart chunking
    print("\n✅ SMART CHUNKING:")
    chunker = SmartChunker(chunk_size=200, overlap_size=30)
    smart_chunks = chunker.chunk_text(text, preserve_paragraphs=True)
    
    print(f"Chunks: {len(smart_chunks)}")
    print(f"Preserves: Paragraph boundaries, sentence integrity")
    
    for i, chunk in enumerate(smart_chunks[:3]):
        print(f"\nChunk {i+1}:")
        print(f"- Position: {chunk['position']}")
        print(f"- Clean start: '{chunk['text'][:30]}...'")
        print(f"- Clean end: '...{chunk['text'][-30:]}'")

if __name__ == "__main__":
    compare_methods()
