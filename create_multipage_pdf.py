from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# Create PDF
c = canvas.Canvas("multipage_test.pdf", pagesize=letter)
width, height = letter

# Page 1
c.setFont("Helvetica-Bold", 24)
c.drawString(inch, height - inch, "PRISMY Multi-Page Test")
c.setFont("Helvetica", 14)
c.drawString(inch, height - 2*inch, "Page 1: Introduction")
c.drawString(inch, height - 2.5*inch, "This document tests multi-page PDF translation.")
c.drawString(inch, height - 3*inch, "Each page contains different content to translate.")
c.showPage()

# Page 2
c.setFont("Helvetica-Bold", 18)
c.drawString(inch, height - inch, "Technical Documentation")
c.setFont("Helvetica", 12)
c.drawString(inch, height - 2*inch, "Page 2: System Requirements")
c.drawString(inch, height - 2.5*inch, "• Python 3.8 or higher")
c.drawString(inch, height - 3*inch, "• Redis server for queue management")
c.drawString(inch, height - 3.5*inch, "• API keys for translation services")
c.drawString(inch, height - 4*inch, "• Sufficient memory for PDF processing")
c.showPage()

# Page 3
c.setFont("Helvetica-Bold", 18)
c.drawString(inch, height - inch, "User Guide")
c.setFont("Helvetica", 12)
c.drawString(inch, height - 2*inch, "Page 3: How to Use")
c.drawString(inch, height - 2.5*inch, "1. Upload your PDF file")
c.drawString(inch, height - 3*inch, "2. Select target language")
c.drawString(inch, height - 3.5*inch, "3. Choose translation tier (Basic/Standard/Premium)")
c.drawString(inch, height - 4*inch, "4. Wait for processing to complete")
c.drawString(inch, height - 4.5*inch, "5. Download translated document")
c.showPage()

# Page 4
c.setFont("Helvetica-Bold", 18)
c.drawString(inch, height - inch, "Conclusion")
c.setFont("Helvetica", 12)
c.drawString(inch, height - 2*inch, "Page 4: Summary")
c.drawString(inch, height - 2.5*inch, "PRISMY provides high-quality translation services")
c.drawString(inch, height - 3*inch, "Supporting multiple languages and document formats")
c.drawString(inch, height - 3.5*inch, "Thank you for using our system!")

c.save()
print("Created multipage_test.pdf with 4 pages")
