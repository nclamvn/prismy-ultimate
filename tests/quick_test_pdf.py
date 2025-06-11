import asyncio
from src.modules.extraction.advanced import AdvancedPDFProcessor

async def test():
    processor = AdvancedPDFProcessor({
        "extract_tables": True,
        "extract_images": True
    })
    
    # Test với PDF đã tạo
    result = await processor.process("test_document_with_content.pdf")
    
    print(f"Tables: {len(result.get('tables', []))}")
    print(f"Images: {len(result.get('images', []))}")
    
    # Show first table
    if result.get('tables'):
        print(f"\nFirst table headers: {result['tables'][0].get('headers')}")

asyncio.run(test())
