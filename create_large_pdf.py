from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import random

# Sample content for variety
titles = [
    "Technical Specifications", "User Manual", "API Documentation", 
    "System Architecture", "Security Guidelines", "Performance Metrics",
    "Installation Guide", "Troubleshooting", "Best Practices", "FAQ"
]

content_templates = [
    "This section covers important aspects of {topic}.",
    "Understanding {topic} is crucial for system optimization.",
    "Key considerations when implementing {topic} in production.",
    "Advanced techniques for managing {topic} effectively.",
    "Common challenges and solutions related to {topic}."
]

topics = [
    "database optimization", "API rate limiting", "caching strategies",
    "load balancing", "security protocols", "error handling",
    "performance tuning", "scalability", "monitoring", "logging"
]

# Create PDF
print("Creating 100-page PDF...")
c = canvas.Canvas("large_document.pdf", pagesize=letter)
width, height = letter

for page_num in range(1, 101):
    # Page header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(inch, height - inch, f"Page {page_num} of 100")
    
    # Random title
    title = random.choice(titles)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(inch, height - 1.5*inch, f"{title}")
    
    # Generate content
    c.setFont("Helvetica", 12)
    y_position = height - 2.5*inch
    
    # Add 5-8 paragraphs per page
    for para in range(random.randint(5, 8)):
        topic = random.choice(topics)
        template = random.choice(content_templates)
        text = template.format(topic=topic)
        
        c.drawString(inch, y_position, f"• {text}")
        y_position -= 0.5*inch
        
        if y_position < 2*inch:
            break
    
    # Page footer
    c.setFont("Helvetica", 10)
    c.drawString(inch, 0.5*inch, f"PRISMY Translation System - Document ID: DOC-2024-{page_num:03d}")
    
    c.showPage()
    
    if page_num % 10 == 0:
        print(f"Generated {page_num} pages...")

c.save()
print("✅ Created large_document.pdf with 100 pages!")
print("File size:", round(len(open("large_document.pdf", "rb").read()) / 1024 / 1024, 2), "MB")
