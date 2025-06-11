"""
Table Extractor
Extracts tables while maintaining document context
"""
import logging
from typing import Dict, Any, List, Optional
import pandas as pd

from ..base_extractor import BaseExtractor

logger = logging.getLogger(__name__)

class TableExtractor(BaseExtractor):
    """
    Extract tables from PDF with structure preservation
    Integrates with document structure analysis
    """
    
    VERSION = "1.0.0"
    CAPABILITIES = ["table_detection", "cell_extraction", "header_detection"]
    
    def validate_config(self):
        """Validate configuration"""
        defaults = {
            "method": "camelot",  # or "pdfplumber"
            "flavor": "lattice",  # lattice for bordered, stream for borderless
            "accuracy_threshold": 0.8,
            "max_tables_per_page": 10
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
                
    async def extract(self, pdf_path: str, document_structure: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract tables from PDF
        
        Integration points:
        - Uses document_structure to optimize extraction
        - Returns standardized format for downstream processing
        - Preserves page context for layout reconstruction
        """
        try:
            logger.info(f"Starting table extraction from {pdf_path}")
            
            # Check if document has tables
            if not self.can_process(document_structure):
                logger.info("No tables detected in document structure")
                return {"tables": [], "metadata": {"skipped": True}}
                
            tables = []
            errors = []
            
            # Get pages with tables from structure analysis
            pages_with_tables = document_structure.get("pages_with_tables", [])
            
            if self.config["method"] == "camelot":
                tables_data = await self._extract_with_camelot(
                    pdf_path, 
                    pages_with_tables
                )
            else:
                tables_data = await self._extract_with_pdfplumber(
                    pdf_path,
                    pages_with_tables
                )
                
            # Process and standardize tables
            for idx, table_data in enumerate(tables_data):
                try:
                    processed_table = self._process_table(table_data, idx)
                    tables.append(processed_table)
                except Exception as e:
                    logger.error(f"Error processing table {idx}: {e}")
                    errors.append(f"Table {idx}: {str(e)}")
                    
            return {
                "tables": tables,
                "metadata": {
                    "total_tables": len(tables),
                    "extraction_method": self.config["method"],
                    "pages_processed": len(pages_with_tables),
                    "errors": errors
                }
            }
            
        except Exception as e:
            logger.error(f"Table extraction failed: {e}")
            return {
                "tables": [],
                "metadata": {"error": str(e)}
            }
            
    async def _extract_with_camelot(self, pdf_path: str, pages: List[int]) -> List[Dict]:
        """Extract using Camelot library"""
        try:
            import camelot
            
            tables_data = []
            
            for page_num in pages:
                # Extract tables from specific page
                tables = camelot.read_pdf(
                    pdf_path,
                    pages=str(page_num),
                    flavor=self.config["flavor"]
                )
                
                for table in tables:
                    if table.accuracy >= self.config["accuracy_threshold"]:
                        tables_data.append({
                            "data": table.df,
                            "page": page_num,
                            "accuracy": table.accuracy,
                            "bbox": table._bbox  # Bounding box for layout
                        })
                        
            return tables_data
            
        except ImportError:
            logger.error("Camelot not installed")
            return []
            
    async def _extract_with_pdfplumber(self, pdf_path: str, pages: List[int]) -> List[Dict]:
        """Extract using pdfplumber"""
        try:
            import pdfplumber
            
            tables_data = []
            
            with pdfplumber.open(pdf_path) as pdf:
                for page_num in pages:
                    if page_num <= len(pdf.pages):
                        page = pdf.pages[page_num - 1]
                        tables = page.extract_tables()
                        
                        for idx, table in enumerate(tables):
                            if table:  # Not empty
                                df = pd.DataFrame(table[1:], columns=table[0])
                                tables_data.append({
                                    "data": df,
                                    "page": page_num,
                                    "accuracy": 0.9,  # pdfplumber doesn't provide accuracy
                                    "bbox": None
                                })
                                
            return tables_data
            
        except ImportError:
            logger.error("pdfplumber not installed")
            return []
            
    def _process_table(self, table_data: Dict, idx: int) -> Dict[str, Any]:
        """
        Process and standardize table data
        Ensures consistent format for integration
        """
        df = table_data["data"]
        
        # Clean data
        df = df.dropna(how='all')  # Remove empty rows
        df = df.dropna(axis=1, how='all')  # Remove empty columns
        
        # Standardized format for integration
        return {
            "id": f"table_{idx}",
            "page": table_data["page"],
            "data": df.to_dict('records'),  # List of dicts
            "csv": df.to_csv(index=False),   # CSV format
            "shape": df.shape,
            "headers": df.columns.tolist(),
            "accuracy": table_data.get("accuracy", 0),
            "bbox": table_data.get("bbox"),  # For layout preservation
            "context": {
                "before_table": None,  # Text before table
                "after_table": None    # Text after table
            }
        }
        
    def can_process(self, document_structure: Dict[str, Any]) -> bool:
        """Check if document has tables to extract"""
        return document_structure.get("has_tables", False) or \
               len(document_structure.get("pages_with_tables", [])) > 0
               
    def get_dependencies(self) -> List[str]:
        """Get required dependencies"""
        if self.config["method"] == "camelot":
            return ["camelot-py[cv]", "pandas"]
        else:
            return ["pdfplumber", "pandas"]
