"""
Create a test PDF with tables and images for testing
"""
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from PIL import Image as PILImage
import io

def create_test_pdf():
    """Create a PDF with mixed content"""
    
    # Create PDF
    pdf_path = "test_document_with_content.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title = Paragraph("Test Document with Tables and Images", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 0.5*inch))
    
    # Text paragraph
    text = """This is a test document created to verify the Advanced PDF Processing capabilities 
    of PRISMY. It contains tables, images, and formatted text to test extraction features."""
    para = Paragraph(text, styles['Normal'])
    elements.append(para)
    elements.append(Spacer(1, 0.3*inch))
    
    # Table 1: Simple data table
    data1 = [
        ['Product', 'Price', 'Quantity', 'Total'],
        ['Laptop', '$999', '2', '$1,998'],
        ['Mouse', '$25', '5', '$125'],
        ['Keyboard', '$75', '3', '$225'],
        ['Monitor', '$299', '2', '$598'],
        ['Total', '', '', '$2,946']
    ]
    
    table1 = Table(data1, colWidths=[2*inch, 1*inch, 1*inch, 1*inch])
    table1.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    
    elements.append(Paragraph("Table 1: Product Inventory", styles['Heading2']))
    elements.append(table1)
    elements.append(Spacer(1, 0.5*inch))
    
    # Create a simple test image
    img_buffer = io.BytesIO()
    img = PILImage.new('RGB', (300, 200), color='lightblue')
    # Draw something on the image
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 250, 150], fill='darkblue')
    draw.text((100, 90), "TEST IMAGE", fill='white')
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    # Save image for PDF
    with open('test_image.png', 'wb') as f:
        f.write(img_buffer.getvalue())
    
    # Add image to PDF
    elements.append(Paragraph("Figure 1: Test Image", styles['Heading2']))
    elements.append(Image('test_image.png', width=3*inch, height=2*inch))
    elements.append(Spacer(1, 0.3*inch))
    
    # Table 2: More complex table
    data2 = [
        ['Month', 'Sales', 'Expenses', 'Profit', 'Growth'],
        ['January', '$10,000', '$7,000', '$3,000', '+5%'],
        ['February', '$12,000', '$8,000', '$4,000', '+20%'],
        ['March', '$15,000', '$9,000', '$6,000', '+25%'],
        ['April', '$14,000', '$8,500', '$5,500', '-7%'],
    ]
    
    table2 = Table(data2)
    table2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(Paragraph("Table 2: Monthly Financial Report", styles['Heading2']))
    elements.append(table2)
    
    # Build PDF
    doc.build(elements)
    print(f"✅ Created {pdf_path}")
    
    # Cleanup
    import os
    if os.path.exists('test_image.png'):
        os.remove('test_image.png')
    
    return pdf_path

if __name__ == "__main__":
    pdf_path = create_test_pdf()
    
    # Show file info
    import os
    file_size = os.path.getsize(pdf_path)
    print(f"📄 File size: {file_size:,} bytes")
    print(f"📄 File path: {os.path.abspath(pdf_path)}")
