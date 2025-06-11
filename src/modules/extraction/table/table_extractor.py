# src/modules/extraction/table/table_extractor.py
import logging
from typing import List, Dict, Any, Optional, Tuple
import camelot
import pandas as pd
from pathlib import Path
import tempfile
import json

logger = logging.getLogger(__name__)

class TableExtractor:
    """Advanced table extraction using Camelot"""
    
    def __init__(self):
        self.supported_formats = ['csv', 'json', 'html', 'excel']
        
    def extract_tables_from_page(
        self, 
        pdf_path: str, 
        page_num: int,
        method: str = 'lattice'
    ) -> List[Dict[str, Any]]:
        """Extract tables from a specific page"""
        try:
            # Use camelot to extract tables
            # lattice: for tables with lines
            # stream: for tables without lines
            tables = camelot.read_pdf(
                pdf_path,
                pages=str(page_num),
                flavor=method,
                suppress_stdout=True
            )
            
            extracted_tables = []
            
            for i, table in enumerate(tables):
                # Get table data
                df = table.df
                
                # Get table metadata
                table_data = {
                    'table_id': f'page_{page_num}_table_{i+1}',
                    'page': page_num,
                    'method': method,
                    'accuracy': table.accuracy,
                    'bbox': self._get_bbox(table),
                    'shape': df.shape,
                    'data': df.to_dict('records'),
                    'html': df.to_html(index=False),
                    'csv': df.to_csv(index=False),
                    'has_header': self._detect_header(df),
                    'column_count': len(df.columns),
                    'row_count': len(df)
                }
                
                extracted_tables.append(table_data)
                
            return extracted_tables
            
        except Exception as e:
            logger.error(f"Error extracting tables from page {page_num}: {e}")
            return []
    
    def extract_all_tables(
        self, 
        pdf_path: str,
        pages: Optional[List[int]] = None
    ) -> Dict[int, List[Dict[str, Any]]]:
        """Extract tables from all pages or specified pages"""
        results = {}
        
        if pages is None:
            # Try to extract from all pages
            pages = 'all'
        else:
            pages = ','.join(map(str, pages))
        
        try:
            # Try lattice method first (for bordered tables)
            logger.info(f"Extracting tables using lattice method from pages: {pages}")
            lattice_tables = camelot.read_pdf(
                pdf_path,
                pages=pages,
                flavor='lattice',
                suppress_stdout=True
            )
            
            # Process lattice tables
            for table in lattice_tables:
                page_num = table.page
                if page_num not in results:
                    results[page_num] = []
                
                table_data = self._process_table(table, 'lattice')
                results[page_num].append(table_data)
            
            # Try stream method for borderless tables
            logger.info(f"Extracting tables using stream method from pages: {pages}")
            stream_tables = camelot.read_pdf(
                pdf_path,
                pages=pages,
                flavor='stream',
                suppress_stdout=True
            )
            
            # Process stream tables (avoid duplicates)
            for table in stream_tables:
                page_num = table.page
                if page_num not in results:
                    results[page_num] = []
                
                table_data = self._process_table(table, 'stream')
                
                # Check if similar table already exists
                if not self._is_duplicate_table(results[page_num], table_data):
                    results[page_num].append(table_data)
            
        except Exception as e:
            logger.error(f"Error extracting tables: {e}")
        
        return results
    
    def _process_table(self, table, method: str) -> Dict[str, Any]:
        """Process a single table"""
        df = table.df
        
        # Clean empty rows and columns
        df = df.dropna(how='all', axis=0)
        df = df.dropna(how='all', axis=1)
        
        return {
            'table_id': f'page_{table.page}_table_{method}_{id(table)}',
            'page': table.page,
            'method': method,
            'accuracy': table.accuracy,
            'bbox': self._get_bbox(table),
            'shape': df.shape,
            'data': df.to_dict('records'),
            'html': df.to_html(index=False, classes='table table-bordered'),
            'csv': df.to_csv(index=False),
            'json': df.to_json(orient='records'),
            'has_header': self._detect_header(df),
            'column_count': len(df.columns),
            'row_count': len(df),
            'is_empty': df.empty
        }
    
    def _get_bbox(self, table) -> Dict[str, float]:
        """Get table bounding box"""
        try:
            return {
                'x1': table._bbox[0],
                'y1': table._bbox[1],
                'x2': table._bbox[2],
                'y2': table._bbox[3]
            }
        except:
            return {'x1': 0, 'y1': 0, 'x2': 0, 'y2': 0}
    
    def _detect_header(self, df: pd.DataFrame) -> bool:
        """Detect if first row is header"""
        if df.empty or len(df) < 2:
            return False
        
        # Check if first row has different data types than rest
        first_row = df.iloc[0]
        
        # Simple heuristic: header usually has strings
        return all(isinstance(val, str) for val in first_row)
    
    def _is_duplicate_table(
        self, 
        existing_tables: List[Dict], 
        new_table: Dict,
        threshold: float = 0.8
    ) -> bool:
        """Check if table is duplicate based on content similarity"""
        if not existing_tables:
            return False
        
        new_data = new_table.get('csv', '')
        
        for existing in existing_tables:
            existing_data = existing.get('csv', '')
            
            # Simple similarity check
            if existing_data == new_data:
                return True
            
            # Check bbox overlap
            if self._bbox_overlap(existing.get('bbox'), new_table.get('bbox')) > threshold:
                return True
        
        return False
    
    def _bbox_overlap(self, bbox1: Dict, bbox2: Dict) -> float:
        """Calculate bbox overlap ratio"""
        if not bbox1 or not bbox2:
            return 0.0
        
        # Calculate intersection
        x1 = max(bbox1['x1'], bbox2['x1'])
        y1 = max(bbox1['y1'], bbox2['y1'])
        x2 = min(bbox1['x2'], bbox2['x2'])
        y2 = min(bbox1['y2'], bbox2['y2'])
        
        if x2 < x1 or y2 < y1:
            return 0.0
        
        intersection = (x2 - x1) * (y2 - y1)
        area1 = (bbox1['x2'] - bbox1['x1']) * (bbox1['y2'] - bbox1['y1'])
        area2 = (bbox2['x2'] - bbox2['x1']) * (bbox2['y2'] - bbox2['y1'])
        
        return intersection / min(area1, area2)
    
    def format_table_for_translation(self, table_data: Dict[str, Any]) -> str:
        """Format table for translation while preserving structure"""
        df = pd.DataFrame(table_data['data'])
        
        # Create markdown table for better translation
        markdown_table = df.to_markdown(index=False)
        
        # Add table metadata
        formatted = f"""
[TABLE_START id="{table_data['table_id']}"]
{markdown_table}
[TABLE_END]
"""
        return formatted
    
    def reconstruct_translated_table(
        self, 
        translated_text: str, 
        original_table: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Reconstruct table from translated text"""
        try:
            # Extract translated table content
            import re
            pattern = r'\[TABLE_START.*?\](.*?)\[TABLE_END\]'
            match = re.search(pattern, translated_text, re.DOTALL)
            
            if match:
                table_content = match.group(1).strip()
                
                # Parse markdown table back to dataframe
                # This is simplified - in production use proper markdown parser
                lines = table_content.split('\n')
                data = []
                
                for line in lines:
                    if '|' in line and not line.strip().startswith('|--'):
                        cells = [cell.strip() for cell in line.split('|')[1:-1]]
                        data.append(cells)
                
                if data:
                    df = pd.DataFrame(data[1:], columns=data[0])
                    
                    # Update original table with translated data
                    translated_table = original_table.copy()
                    translated_table['data'] = df.to_dict('records')
                    translated_table['html'] = df.to_html(index=False, classes='table table-bordered')
                    translated_table['csv'] = df.to_csv(index=False)
                    translated_table['translated'] = True
                    
                    return translated_table
            
        except Exception as e:
            logger.error(f"Error reconstructing translated table: {e}")
        
        # Return original if reconstruction fails
        return original_table

# Singleton instance
_table_extractor = None

def get_table_extractor() -> TableExtractor:
    global _table_extractor
    if _table_extractor is None:
        _table_extractor = TableExtractor()
    return _table_extractor
