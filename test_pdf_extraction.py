import sys
sys.path.append('/Users/mac/prismy-ultimate')

from src.celery_tasks.prismy_tasks import pdf_processor

pdf_path = './test.pdf'
print(f"Testing PDF extraction on: {pdf_path}")
print("-" * 50)

result = pdf_processor.process_pdf(pdf_path)

print(f"Total pages: {result['total_pages']}")
print(f"Total characters: {result['total_characters']}")
print(f"Extraction methods: {result['extraction_methods']}")
print(f"Number of chunks: {len(result.get('chunks', []))}")

if result.get('pages'):
    print("\nFirst page preview:")
    first_page = result['pages'][0]
    print(f"Page {first_page['page']} ({first_page['method']}): {first_page['text'][:200]}...")
