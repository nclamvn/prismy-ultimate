from fpdf import FPDF
import os

# Create PDF with basic font
pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=16)

# Title
pdf.cell(0, 10, txt="CHI PHEO - Nam Cao", ln=1, align='C')
pdf.ln(10)

# Content (ASCII version for compatibility)
pdf.set_font("Arial", size=11)
content = """Chi Pheo dung day, lu lu di ra. Han di nhu mot con vat bi thuong.
Han lao dao buoc ra khoi cua ngo, khong biet di dau, cu mac cho hai cai chan
dan han di. Troi da sang han. Mat troi chua moc, nhung lang Vu Dai da thuc.

Han di lang thang trong lang. Nha ai cung dong cua. Con cho chay ra sua.
Han cui nhat mot hon gach nem cho. Cho chay, keu ang ang. Co tieng nguoi mang:
- Thang chet tiet nao day?

Chi Pheo cuoi henh hech. Roi han lai buon. Han nho den bat ruou.
Han nho den thi Ba. Han muon gap thi Ba lam. Nhung thi Ba dau?"""

# Add content line by line
for line in content.split('\n'):
    pdf.cell(0, 8, txt=line.strip(), ln=1)

# Save PDF
pdf.output("chi_pheo_final.pdf")
print("✅ Created chi_pheo_final.pdf")
print("📄 File size:", os.path.getsize("chi_pheo_final.pdf"), "bytes")
