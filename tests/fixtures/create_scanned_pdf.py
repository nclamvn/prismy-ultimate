"""
Create a scanned-style PDF with images containing text
"""
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io
import os

def create_scanned_pdf():
    """Create PDF with image-based pages (simulating scanned document)"""
    
    # Create images with text
    images = []
    
    # Page 1: Vietnamese text
    img1 = Image.new('RGB', (600, 800), color='#f8f8f8')
    draw1 = ImageDraw.Draw(img1)
    
    vietnamese_text = [
        "PRISMY - Hệ thống dịch thuật AI",
        "",
        "Giới thiệu:",
        "PRISMY là một nền tảng xử lý tài liệu",
        "thông minh với khả năng:",
        "",
        "• Trích xuất văn bản từ PDF",
        "• Nhận dạng chữ viết (OCR)",
        "• Dịch đa ngôn ngữ",
        "• Xử lý bảng biểu và hình ảnh",
        "",
        "Công nghệ sử dụng:",
        "- OpenAI GPT-4",
        "- Tesseract OCR",
        "- Smart Chunking",
        "",
        "Chi phí: $0.003/trang"
    ]
    
    y = 50
    for line in vietnamese_text:
        draw1.text((50, y), line, fill='black', size=14)
        y += 35
    
    # Add some noise to simulate scan
    for i in range(100):
        x = int(600 * (i % 10) / 10)
        y = int(800 * (i // 10) / 10)
        draw1.point((x, y), fill='gray')
    
    images.append(img1)
    
    # Page 2: English with formulas
    img2 = Image.new('RGB', (600, 800), color='#fafafa')
    draw2 = ImageDraw.Draw(img2)
    
    english_text = [
        "Mathematical Formulas in PRISMY",
        "",
        "1. Quadratic equation:",
        "   x = (-b ± √(b² - 4ac)) / 2a",
        "",
        "2. Cost calculation:",
        "   Total Cost = Pages × $0.003",
        "",
        "3. Accuracy formula:",
        "   Accuracy = (Correct / Total) × 100%",
        "",
        "Processing Performance:",
        "• OCR: 1-2 seconds/page",
        "• Translation: < 1 second/chunk",
        "• Total: < 5 seconds/page",
        "",
        "Contact: support@prismy.ai"
    ]
    
    y = 50
    for line in english_text:
        draw2.text((50, y), line, fill='black', size=14)
        y += 35
        
    images.append(img2)
    
    # Save images temporarily
    temp_images = []
    for i, img in enumerate(images):
        temp_path = f"temp_page_{i+1}.png"
        img.save(temp_path, 'PNG')
        temp_images.append(temp_path)
    
    # Create PDF from images
    pdf_path = "test_scanned_document.pdf"
    c = canvas.Canvas(pdf_path, pagesize=A4)
    
    for img_path in temp_images:
        c.drawImage(img_path, 50, 100, width=500, height=667)
        c.showPage()
    
    c.save()
    
    # Cleanup temp images
    for img_path in temp_images:
        os.remove(img_path)
    
    print(f"✅ Created {pdf_path} (2 pages)")
    return pdf_path

if __name__ == "__main__":
    create_scanned_pdf()
