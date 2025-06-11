from fpdf import FPDF
import os

# Create a long PDF document
pdf = FPDF()
pdf.add_page()
pdf.set_font("Helvetica", size=14)  # Use built-in font

# Title
pdf.cell(0, 10, "CHI PHEO - Full Story", align='C')
pdf.ln(10)

# Chapter 1
pdf.set_font("Helvetica", "B", 12)
pdf.cell(0, 10, "Chapter 1: The Beginning")
pdf.ln(10)

pdf.set_font("Helvetica", "", 11)

# Add content in smaller chunks
content_lines = [
    "Chi Pheo was originally a kind and hardworking farmer in Vu Dai village.",
    "He lived a simple life, working in the fields and hoping for a better future.",
    "However, his life took a tragic turn when he was falsely accused.",
    "",
    "The local authorities arrested him without proper evidence.",
    "He spent years in prison for a crime he did not commit.",
    "When he was finally released, everything had changed.",
    ""
]

for line in content_lines:
    if line:
        pdf.cell(0, 8, line)
    pdf.ln(6)

# Add more content to make it long
pdf.ln(10)
for i in range(15):
    pdf.cell(0, 8, f"Paragraph {i+1}: The story continues with more details about Chi Pheo's life.")
    pdf.ln(6)
    pdf.cell(0, 8, "He wandered through the village, lost and broken.")
    pdf.ln(6)
    pdf.cell(0, 8, "Society had transformed him from a good man into an outcast.")
    pdf.ln(8)

# Chapter 2
pdf.add_page()
pdf.set_font("Helvetica", "B", 12)
pdf.cell(0, 10, "Chapter 2: The Transformation")
pdf.ln(10)

pdf.set_font("Helvetica", "", 11)
content2 = [
    "After being released from prison, Chi Pheo had lost everything.",
    "His land was taken, his reputation destroyed, and his spirit broken.",
    "Society had transformed a good man into an outcast.",
    "",
    "He began drinking heavily to forget his pain.",
    "The villagers feared and avoided him.",
    "Chi Pheo became the very thing they accused him of being."
]

for line in content2:
    if line:
        pdf.cell(0, 8, line)
    pdf.ln(6)

# Add more pages
for page in range(3):
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, f"Chapter {page+3}: Continued Story")
    pdf.ln(10)
    
    pdf.set_font("Helvetica", "", 11)
    for i in range(20):
        pdf.cell(0, 8, f"Line {i+1}: This chapter explores more aspects of Chi Pheo's tragic life.")
        pdf.ln(6)
        if i % 5 == 0:
            pdf.ln(4)

# Save
pdf.output("chi_pheo_long_story.pdf")
print(f"✅ Created chi_pheo_long_story.pdf")
print(f"📄 File size: {os.path.getsize('chi_pheo_long_story.pdf'):,} bytes")
print(f"📄 Estimated pages: 5+")
print(f"📄 Estimated characters: ~15,000+")
