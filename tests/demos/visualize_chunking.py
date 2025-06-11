from src.modules.chunking.smart_chunker import SmartChunker

def visualize_chunks():
    # Sample text
    text = """Chí Phèo là tác phẩm nổi tiếng của Nam Cao. Câu chuyện kể về một người nông dân bị xã hội đẩy vào con đường tha hóa.

Nhân vật Chí Phèo vốn là người hiền lành. Sau khi bị hãm hại và ngồi tù oan, hắn trở thành kẻ vô loại.

Tác phẩm phản ánh hiện thực xã hội Việt Nam trước 1945. Nam Cao đã vẽ nên bức tranh bi thảm về số phận người nông dân."""
    
    print("📄 ORIGINAL TEXT:")
    print("="*60)
    print(text)
    print(f"\nLength: {len(text)} characters")
    
    # Create chunks with small size to see the effect
    chunker = SmartChunker(chunk_size=150, overlap_size=30, language="vi")
    chunks = chunker.chunk_text(text, preserve_paragraphs=True)
    
    print(f"\n📊 SMART CHUNKS: {len(chunks)} chunks")
    print("="*60)
    
    for i, chunk in enumerate(chunks):
        print(f"\n🔖 Chunk {i+1}:")
        print(f"Position: {chunk['position']}")
        print(f"Length: {len(chunk['text'])} chars")
        
        # Show overlap visually
        if i > 0 and chunk.get('overlap_start', 0) > 0:
            overlap_text = chunk['text'][:chunk['overlap_start']]
            main_text = chunk['text'][chunk['overlap_start']:]
            print(f"Text: [{overlap_text}] + {main_text}")
        else:
            print(f"Text: {chunk['text']}")
        
        print("-"*40)

if __name__ == "__main__":
    visualize_chunks()
