"""
Create PDF with mathematical formulas for testing
"""
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def create_math_pdf():
    pdf_path = "test_math_document.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title = Paragraph("Mathematical Formulas Test Document", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 20))
    
    # Add some formulas
    formulas = [
        "1. Quadratic Formula: x = (-b ± √(b² - 4ac)) / 2a",
        "2. Pythagorean Theorem: a² + b² = c²",
        "3. Euler's Identity: e^(iπ) + 1 = 0",
        "4. Integration: ∫ x² dx = x³/3 + C",
        "5. Summation: ∑(i=1 to n) i = n(n+1)/2",
        "6. Limit: lim(x→0) sin(x)/x = 1",
        "7. Derivative: d/dx(x^n) = nx^(n-1)",
        "8. Matrix: |a b| = ad - bc",
        "          |c d|"
    ]
    
    for formula in formulas:
        para = Paragraph(formula, styles['Normal'])
        elements.append(para)
        elements.append(Spacer(1, 10))
    
    doc.build(elements)
    print(f"✅ Created {pdf_path}")
    return pdf_path

if __name__ == "__main__":
    create_math_pdf()
