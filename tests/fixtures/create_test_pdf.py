from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)
pdf.cell(200, 10, txt="PRISMY Test Document", ln=1, align='C')
pdf.cell(200, 10, txt="This is a test PDF for translation.", ln=2)
pdf.output("test.pdf")
print("Created test.pdf")
