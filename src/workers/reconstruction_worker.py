# src/workers/reconstruction_worker.py - Improved Layout Version

import asyncio
import json
import logging
from typing import Dict, Any, List
import redis.asyncio as redis
import os
from datetime import datetime
from src.storage.storage_manager import get_storage_manager
import os
from pathlib import Path

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, 
    Paragraph, 
    Spacer, 
    Table, 
    TableStyle,
    PageBreak,
    PageTemplate,
    Frame,
    BaseDocTemplate
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas

import redis.asyncio as redis

logger = logging.getLogger(__name__)

class NumberedCanvas(canvas.Canvas):
    """Canvas with page numbers"""
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        """Add page numbers to each page."""
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        """Draw page number at bottom of page"""
        self.setFont("Helvetica", 9)
        self.drawRightString(
            A4[0] - inch,
            0.5 * inch,
            f"Page {self._pageNumber} of {page_count}"
        )
        self.drawString(
            inch,
            0.5 * inch,
            "PRISMY Translation System"
        )

class PDFReconstructionWorker:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        self.output_dir = Path("./output/reconstructed")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    async def connect(self):
        """Connect to Redis"""
        self.redis_client = await redis.from_url(self.redis_url)
        logger.info("Connected to Redis")
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
    
    async def get_job_data(self, job_id: str) -> Dict[str, Any]:
        """Get job data from Redis"""
        job_key = f"prismy:job:{job_id}"
        job_data = await self.redis_client.hgetall(job_key)
        
        if not job_data:
            raise ValueError(f"Job not found: {job_id}")
        
        # Get original filename from file_path
        file_path = job_data.get(b'file_path', b'').decode('utf-8')
        original_filename = os.path.basename(file_path) if file_path else 'document.pdf'
        
        return {
            'job_id': job_id,
            'file_path': file_path,
            'original_filename': original_filename,
            'source_lang': job_data.get(b'source_lang', b'vi').decode('utf-8'),
            'target_lang': job_data.get(b'target_lang', b'en').decode('utf-8'),
            'tier': job_data.get(b'tier', b'standard').decode('utf-8')
        }
    
    async def process_reconstruction_job(self, job_id: str):
        """Process a single reconstruction job"""
        logger.info(f"Processing reconstruction job: {job_id}")
        
        try:
            # Get job data
            job_data = await self.get_job_data(job_id)
            
            # Update status
            await self._update_job_status(job_id, "reconstruction", "processing")
            
            # Try to get translated chunks first
            translated_chunks = await self._get_translated_chunks(job_id)
            
            if translated_chunks:
                # Generate PDF from translated chunks
                output_path = await self._generate_pdf_from_chunks(job_id, translated_chunks, job_data)
            else:
                # Fallback to batches if no chunks
                logger.warning(f"No translated chunks found for {job_id}, using batches")
                batches = await self._get_batches(job_id)
                output_path = await self._generate_pdf_from_batches(job_id, batches, job_data)
            
            # Store result
            await self._store_result(job_id, output_path)
            
            # Update status
            await self._update_job_status(job_id, "reconstruction", "completed")
            
            logger.info(f"Reconstruction completed for job {job_id}")
            
        except Exception as e:
            logger.error(f"Reconstruction failed for job {job_id}: {str(e)}")
            await self._update_job_status(job_id, "reconstruction", "failed", str(e))
    
    async def _get_translated_chunks(self, job_id: str) -> List[Dict]:
        """Get all translated chunks from Redis"""
        chunks = []
        cursor = '0'
        
        while cursor != 0:
            cursor, keys = await self.redis_client.scan(
                cursor,
                match=f"translated:{job_id}:*",
                count=100
            )
            
            if keys:
                values = await self.redis_client.mget(keys)
                for value in values:
                    if value:
                        chunks.append(json.loads(value))
        
        return chunks
    
    async def _get_batches(self, job_id: str) -> List[Dict]:
        """Get all batches from Redis"""
        batches = []
        cursor = '0'
        
        while cursor != 0:
            cursor, keys = await self.redis_client.scan(
                cursor,
                match=f"batch:{job_id}:*",
                count=100
            )
            
            if keys:
                values = await self.redis_client.mget(keys)
                for value in values:
                    if value:
                        batches.append(json.loads(value))
        
        return batches
    
    def _create_custom_styles(self):
        """Create custom styles for better formatting"""
        styles = getSampleStyleSheet()
        
        # Custom title style
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Title'],
            fontSize=28,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=40,
            alignment=TA_CENTER
        ))
        
        # Custom heading styles
        styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2c3e50'),
            spaceBefore=20,
            spaceAfter=12,
            borderColor=colors.HexColor('#3498db'),
            borderWidth=2,
            borderPadding=(0, 0, 3, 0),
            leftIndent=0
        ))
        
        # Table header style
        styles.add(ParagraphStyle(
            name='TableHeader',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.whitesmoke,
            alignment=TA_CENTER
        ))
        
        # Table cell style
        styles.add(ParagraphStyle(
            name='TableCell',
            parent=styles['Normal'],
            fontSize=9,
            alignment=TA_CENTER
        ))
        
        return styles
    
    async def _generate_pdf_from_chunks(self, job_id: str, chunks: List[Dict], job_data: Dict) -> str:
        """Generate PDF from translated chunks with improved layout"""
        output_path = self.output_dir / f"{job_id}_translated.pdf"
        
        # Create PDF document with custom canvas
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )
        
        # Get custom styles
        styles = self._create_custom_styles()
        
        # Container for PDF elements
        story = []
        
        # Add title page
        story.extend(self._create_title_page(job_data, styles))
        story.append(PageBreak())
        
        # Add translation note
        translation_note = f"Document translated from {job_data['source_lang']} to {job_data['target_lang']}"
        story.append(Paragraph(translation_note, styles['Italic']))
        story.append(Spacer(1, 24))
        
        # Sort chunks by chunk_id
        chunks.sort(key=lambda x: x.get('chunk_id', 0))
        
        # Process chunks
        for i, chunk in enumerate(chunks):
            chunk_type = chunk.get('type', 'text')
            translated_text = chunk.get('translated_text', chunk.get('text', ''))
            
            # Remove translation prefix from text for cleaner output
            translated_text = self._clean_translation_prefix(translated_text, job_data)
            
            if chunk_type == 'table':
                # Add table heading
                story.append(Paragraph(f"Table {i + 1}", styles['SectionHeading']))
                story.append(Spacer(1, 12))
                
                # Parse and render table
                try:
                    table_data = json.loads(chunk.get('text', '[]'))
                    if isinstance(table_data, list) and table_data:
                        # Clean translation prefixes from table data
                        cleaned_table = self._clean_table_data(table_data, job_data)
                        
                        # Create table with better column widths
                        col_count = len(cleaned_table[0]) if cleaned_table else 4
                        col_width = (A4[0] - 144) / col_count  # Distribute width evenly
                        
                        t = Table(cleaned_table, colWidths=[col_width] * col_count)
                        
                        # Improved table style
                        t.setStyle(TableStyle([
                            # Header row
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 11),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            
                            # Data rows
                            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
                            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                            ('FONTSIZE', (0, 1), (-1, -1), 10),
                            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            
                            # Grid
                            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
                            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#2c3e50')),
                            
                            # Alternating row colors
                            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
                        ]))
                        
                        story.append(t)
                        story.append(Spacer(1, 24))
                except Exception as e:
                    # Fallback to text
                    story.append(Paragraph(f"[Table data could not be rendered]", styles['Normal']))
                    story.append(Spacer(1, 12))
            
            elif chunk_type == 'formula':
                # Render formula with special formatting
                story.append(Paragraph("Formula:", styles['SectionHeading']))
                story.append(Spacer(1, 8))
                story.append(Paragraph(translated_text, styles['Code']))
                story.append(Spacer(1, 16))
            
            else:
                # Regular text with better paragraph handling
                if translated_text:
                    # Split by paragraphs and add proper spacing
                    paragraphs = translated_text.split('\n\n')
                    for para in paragraphs:
                        if para.strip():
                            # Check if it's a heading (simple heuristic)
                            if len(para) < 100 and not para.endswith('.'):
                                story.append(Paragraph(para.strip(), styles['Heading3']))
                                story.append(Spacer(1, 12))
                            else:
                                story.append(Paragraph(para.strip(), styles['Normal']))
                                story.append(Spacer(1, 8))
                    
                    # Add section spacing
                    story.append(Spacer(1, 16))
        
        # Build PDF with custom canvas for page numbers
        doc.build(story, canvasmaker=NumberedCanvas)
        
        logger.info(f"Generated PDF with improved layout: {output_path}")
        return str(output_path)
    
    def _clean_translation_prefix(self, text: str, job_data: Dict) -> str:
        """Remove translation prefix for cleaner output"""
        prefix = f"[TRANSLATED from {job_data['source_lang']} to {job_data['target_lang']}]: "
        if text.startswith(prefix):
            return text[len(prefix):]
        return text
    
    def _clean_table_data(self, table_data: List[List[str]], job_data: Dict) -> List[List[str]]:
        """Clean translation prefixes from table cells"""
        prefix = f"[TRANSLATED from {job_data['source_lang']} to {job_data['target_lang']}]: "
        cleaned_data = []
        
        for row in table_data:
            cleaned_row = []
            for cell in row:
                if isinstance(cell, str) and cell.startswith(prefix):
                    cleaned_row.append(cell[len(prefix):])
                else:
                    cleaned_row.append(cell)
            cleaned_data.append(cleaned_row)
        
        return cleaned_data
    
    async def _generate_pdf_from_batches(self, job_id: str, batches: List[Dict], job_data: Dict) -> str:
        """Generate PDF from batches (fallback) with improved layout"""
        output_path = self.output_dir / f"{job_id}_translated.pdf"
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )
        
        # Get custom styles
        styles = self._create_custom_styles()
        
        # Container for PDF elements
        story = []
        
        # Add title
        story.append(Paragraph("EXTRACTED DOCUMENT", styles['CustomTitle']))
        story.append(Spacer(1, 30))
        
        # Process batches
        table_count = 0
        for batch in batches:
            # Handle nested structure
            content_data = batch.get('data', {}).get('content', []) if 'data' in batch else batch.get('content', [])
            
            for page_data in content_data:
                for element in page_data.get('elements', []):
                    if element['type'] == 'text':
                        text = element.get('content', '')
                        # Add text with proper paragraph handling
                        paragraphs = text.split('\n\n')
                        for para in paragraphs:
                            if para.strip():
                                story.append(Paragraph(para.strip(), styles['Normal']))
                                story.append(Spacer(1, 8))
                        story.append(Spacer(1, 16))
                        
                    elif element['type'] == 'table':
                        table_count += 1
                        # Add table heading
                        story.append(Paragraph(f"Table {table_count}", styles['SectionHeading']))
                        story.append(Spacer(1, 12))
                        
                        # Render table
                        table_data = element.get('data', [])
                        if table_data:
                            col_count = len(table_data[0]) if table_data else 4
                            col_width = (A4[0] - 144) / col_count
                            
                            t = Table(table_data, colWidths=[col_width] * col_count)
                            t.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('FONTSIZE', (0, 0), (-1, 0), 11),
                                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
                                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
                                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
                            ]))
                            story.append(t)
                            story.append(Spacer(1, 24))
        
        # Build PDF
        doc.build(story, canvasmaker=NumberedCanvas)
        
        logger.info(f"Generated PDF from batches with improved layout: {output_path}")
        return str(output_path)
    
    def _create_title_page(self, job_data: Dict, styles) -> List:
        """Create improved title page elements"""
        elements = []
        
        # Add spacing at top
        elements.append(Spacer(1, 2*inch))
        
        # Main title
        elements.append(Paragraph("TRANSLATED DOCUMENT", styles['CustomTitle']))
        elements.append(Spacer(1, 40))
        
        # Document info box
        info_text = f"""
        <para align="center">
        <b>Original Document:</b><br/>
        {job_data.get('original_filename', 'Unknown')}<br/>
        <br/>
        <b>Translation:</b><br/>
        {job_data.get('source_lang', 'auto').upper()} → {job_data.get('target_lang', 'en').upper()}<br/>
        <br/>
        <b>Processing Date:</b><br/>
        {datetime.now().strftime("%B %d, %Y at %I:%M %p")}<br/>
        <br/>
        <b>Translation Tier:</b><br/>
        {job_data.get('tier', 'standard').title()}
        </para>
        """
        
        # Create info box style
        info_style = ParagraphStyle(
            'InfoBox',
            parent=styles['Normal'],
            fontSize=12,
            alignment=TA_CENTER,
            borderColor=colors.HexColor('#3498db'),
            borderWidth=1,
            borderPadding=20,
            backColor=colors.HexColor('#f8f9fa')
        )
        
        elements.append(Paragraph(info_text, info_style))
        
        return elements
    
    async def _update_job_status(self, job_id: str, stage: str, status: str, error: str = None):
        """Update job status in Redis"""
        status_data = {
            'job_id': job_id,
            'stage': stage,
            'status': status,
            'updated_at': datetime.now().isoformat()
        }
        
        if error:
            status_data['error'] = error
        
        await self.redis_client.hset(
            f"job:{job_id}",
            stage,
            json.dumps(status_data)
        )
    
    async def _store_result(self, job_id: str, output_path: str):
        """Store reconstruction result"""
        result = {
            'job_id': job_id,
            'output_path': output_path,
            'completed_at': datetime.now().isoformat(),
            'file_size': os.path.getsize(output_path)
        }
        
        # Update job status to completed
        
        await self.redis_client.hset(
        
            f"prismy:job:{job_id}",
        
            mapping={
        
                "status": "completed",
        
                "progress": "100.0",
        
                "output_path": output_path
        
            }
        
        )
        
        
        
        await self.redis_client.setex(
            f"result:{job_id}",
            86400,  # 24 hours
            json.dumps(result)
        )
    
    async def run(self):
        """Main worker loop"""
        await self.connect()
        
        logger.info("Reconstruction worker started")
        
        try:
            while True:
                # Get job_id from queue
                result = await self.redis_client.blpop("prismy:reconstruct", timeout=5)
                
                if result:
                    _, job_id_bytes = result
                    job_id = job_id_bytes.decode('utf-8')
                    
                    try:
                        await self.process_reconstruction_job(job_id)
                    except Exception as e:
                        logger.error(f"Failed to process job {job_id}: {e}")
                        
        except KeyboardInterrupt:
            logger.info("Worker stopped by user")
        finally:
            await self.disconnect()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    worker = PDFReconstructionWorker()
    asyncio.run(worker.run())
