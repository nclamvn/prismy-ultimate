"""
Document Structure Analyzer
Analyzes PDF structure for optimal extraction
"""
import logging
from typing import Dict, Any, List, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class DocumentStructureAnalyzer:
    """Analyze document structure and layout"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
    async def analyze(self, pdf_path: str) -> Dict[str, Any]:
        """
        Analyze PDF structure
        Returns information about pages, layout, content types
        """
        try:
            import pdfplumber
            
            structure = {
                "page_count": 0,
                "pages": [],
                "has_tables": False,
                "has_images": False,
                "has_multi_columns": False,
                "dominant_font": None,
                "text_blocks": []
            }
            
            with pdfplumber.open(pdf_path) as pdf:
                structure["page_count"] = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages):
                    page_info = {
                        "page_number": page_num + 1,
                        "width": page.width,
                        "height": page.height,
                        "has_tables": bool(page.find_tables()),
                        "has_images": bool(page.images),
                        "text_bbox": [],
                        "layout": "single_column"  # default
                    }
                    
                    # Analyze text blocks
                    if page.chars:
                        text_blocks = self._analyze_text_blocks(page.chars)
                        page_info["text_blocks"] = text_blocks
                        page_info["layout"] = self._detect_layout(text_blocks)
                        
                    # Check for tables
                    if page_info["has_tables"]:
                        structure["has_tables"] = True
                        
                    # Check for images
                    if page_info["has_images"]:
                        structure["has_images"] = True
                        
                    structure["pages"].append(page_info)
                    
            return structure
            
        except Exception as e:
            logger.error(f"Structure analysis failed: {e}")
            return {"error": str(e), "page_count": 0}
            
    def _analyze_text_blocks(self, chars: List[Dict]) -> List[Dict[str, Any]]:
        """Analyze character data to identify text blocks"""
        if not chars:
            return []
            
        # Group characters into blocks based on position
        blocks = []
        current_block = {
            "bbox": [chars[0]["x0"], chars[0]["top"], chars[0]["x1"], chars[0]["bottom"]],
            "chars": [chars[0]],
            "text": chars[0].get("text", "")
        }
        
        for char in chars[1:]:
            # Check if character belongs to current block
            if (abs(char["top"] - current_block["bbox"][1]) < 5 and  # Same line
                char["x0"] - current_block["bbox"][2] < 20):  # Close horizontally
                # Add to current block
                current_block["chars"].append(char)
                current_block["text"] += char.get("text", "")
                current_block["bbox"][2] = char["x1"]  # Extend right
                current_block["bbox"][3] = max(current_block["bbox"][3], char["bottom"])
            else:
                # Start new block
                blocks.append(current_block)
                current_block = {
                    "bbox": [char["x0"], char["top"], char["x1"], char["bottom"]],
                    "chars": [char],
                    "text": char.get("text", "")
                }
                
        blocks.append(current_block)
        return blocks
        
    def _detect_layout(self, text_blocks: List[Dict]) -> str:
        """Detect if page has multi-column layout"""
        if not text_blocks:
            return "empty"
            
        # Analyze x-coordinates to detect columns
        x_positions = [block["bbox"][0] for block in text_blocks]
        
        # Simple heuristic: if text starts at very different x positions, might be multi-column
        if len(set(x_positions)) > 10:  # Many different x positions
            x_clusters = self._cluster_positions(x_positions)
            if len(x_clusters) > 1:
                return "multi_column"
                
        return "single_column"
        
    def _cluster_positions(self, positions: List[float], threshold: float = 50) -> List[List[float]]:
        """Cluster positions to detect columns"""
        if not positions:
            return []
            
        clusters = [[positions[0]]]
        
        for pos in positions[1:]:
            added = False
            for cluster in clusters:
                if abs(pos - cluster[0]) < threshold:
                    cluster.append(pos)
                    added = True
                    break
            if not added:
                clusters.append([pos])
                
        return clusters
