# src/processors/enhanced_pdf_output.py
from typing import Dict, Any, List
import logging
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import pandas as pd

from ..core.base import BaseProcessor

logger = logging.getLogger(__name__)

class EnhancedPDFOutput(BaseProcessor):
    """Enhanced PDF output with table rendering"""
    
    def __init__(self):
        super().__init__()
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
    def _setup_custom_styles(self):
        """Setup custom styles for better formatting"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30,
            alignment=1  # Center
        ))
        
        # Table caption style
        self.styles.add(ParagraphStyle(
            name='TableCaption',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#7f8c8d'),
            spaceBefore=6,
            spaceAfter=12,
            alignment=1  # Center
        ))
        
    async def process(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Process translated chunks into enhanced PDF"""
        chunks = data.get("chunks", [])
        output_path = context.get("output_path", "output.pdf")
        
        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )
        
        # Build story
        story = []
        
        # Add title page
        story.extend(self._create_title_page(context))
        
        # Process chunks
        for i, chunk in enumerate(chunks):
            if chunk.get('is_table_chunk'):
                # Render table
                story.extend(self._render_table_chunk(chunk))
            else:
                # Render text
                story.extend(self._render_text_chunk(chunk))
            
            # Add spacing between chunks
            if i < len(chunks) - 1:
                story.append(Spacer(1, 0.3*inch))
        
        # Build PDF
        doc.build(story)
        
        logger.info(f"Generated enhanced PDF: {output_path}")
        
        return {
            "output_path": output_path,
            "chunks_processed": len(chunks),
            "tables_rendered": sum(1 for c in chunks if c.get('is_table_chunk'))
        }
    
    def _render_table_chunk(self, chunk: Dict[str, Any]) -> List:
        """Render a table chunk"""
        story = []
        
        tables = chunk.get('tables', [])
        for table_data in tables:
            # Add table caption
            caption = f"Table {table_data.get('table_id', 'Unknown')} - Page {table_data.get('page', 'N/A')}"
            story.append(Paragraph(caption, self.styles['TableCaption']))
            
            # Convert table data to ReportLab table
            df = pd.DataFrame(table_data.get('data', []))
            
            if not df.empty:
                # Prepare table data
                table_list = [df.columns.tolist()] + df.values.tolist()
                
                # Create table
                t = Table(table_list, repeatRows=1)
                
                # Apply table style
                t.setStyle(TableStyle([
                    # Header style
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    
                    # Body style
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
                    
                    # Padding
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ]))
                
                story.append(t)
                
                # Add accuracy info if available
                if 'accuracy' in table_data:
                    accuracy_text = f"Extraction accuracy: {table_data['accuracy']:.1f}%"
                    story.append(Paragraph(
                        accuracy_text, 
                        ParagraphStyle(
                            'Accuracy',
                            parent=self.styles['Normal'],
                            fontSize=8,
                            textColor=colors.HexColor('#95a5a6'),
                            spaceAfter=12
                        )
                    ))
        
        return story
    
    def _render_text_chunk(self, chunk: Dict[str, Any]) -> List:
        """Render a text chunk"""
        story = []
        
        translated_text = chunk.get("translated_text", "")
        if translated_text:
            # Split into paragraphs
            paragraphs = translated_text.split('\n\n')
            
            for para_text in paragraphs:
                if para_text.strip():
                    # Check if it's a heading (simple heuristic)
                    if len(para_text) < 100 and not para_text.endswith('.'):
                        style = self.styles['Heading2']
                    else:
                        style = self.styles['Normal']
                    
                    para = Paragraph(para_text, style)
                    story.append(para)
                    story.append(Spacer(1, 0.1*inch))
        
        return story
    
    def _create_title_page(self, context: Dict[str, Any]) -> List:
        """Create title page"""
        story = []
        
        # Title
        story.append(Paragraph("TRANSLATED DOCUMENT", self.styles['CustomTitle']))
        story.append(Spacer(1, 0.5*inch))
        
        # Metadata box
        metadata_items = [
            f"<b>Original Document:</b> {context.get('original_filename', 'Unknown')}",
            f"<b>Translation:</b> {context.get('source_lang', 'Unknown')} → {context.get('target_lang', 'Unknown')}",
            f"<b>Translation Tier:</b> {context.get('tier', 'Standard')}",
            f"<b>Total Pages:</b> {context.get('total_pages', 'Unknown')}",
            f"<b>Processing Date:</b> {context.get('date', 'Unknown')}"
        ]
        
        for item in metadata_items:
            story.append(Paragraph(item, self.styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
        
        # Page break after title page
        story.append(PageBreak())
        
        return story
