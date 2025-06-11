"""
Advanced PDF Processing Monitoring
Real-time metrics and health checks
"""
import time
import psutil
import logging
from typing import Dict, Any
from collections import defaultdict
import json

logger = logging.getLogger(__name__)

class PDFProcessingMonitor:
    """Monitor Advanced PDF processing metrics"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.current_processing = {}
        
    def start_processing(self, pdf_id: str, pdf_path: str, page_count: int):
        """Start monitoring a PDF processing job"""
        self.current_processing[pdf_id] = {
            "path": pdf_path,
            "page_count": page_count,
            "start_time": time.time(),
            "memory_start": psutil.Process().memory_info().rss / 1024 / 1024
        }
        
    def end_processing(self, pdf_id: str, result: Dict[str, Any]):
        """End monitoring and record metrics"""
        if pdf_id not in self.current_processing:
            return
            
        job = self.current_processing[pdf_id]
        duration = time.time() - job["start_time"]
        memory_used = psutil.Process().memory_info().rss / 1024 / 1024 - job["memory_start"]
        
        metrics = {
            "pdf_id": pdf_id,
            "duration": duration,
            "duration_per_page": duration / job["page_count"],
            "memory_used_mb": memory_used,
            "page_count": job["page_count"],
            "tables_extracted": len(result.get("tables", [])),
            "images_extracted": len(result.get("images", [])),
            "formulas_extracted": len(result.get("formulas", [])),
            "errors": len(result.get("errors", [])),
            "timestamp": time.time()
        }
        
        self.metrics["processing_jobs"].append(metrics)
        del self.current_processing[pdf_id]
        
        # Log if performance targets not met
        if metrics["duration_per_page"] > 5:
            logger.warning(f"Performance target missed: {metrics['duration_per_page']:.2f}s/page")
            
        if metrics["memory_used_mb"] > 500:
            logger.warning(f"Memory target exceeded: {metrics['memory_used_mb']:.2f}MB")
            
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        if not self.metrics["processing_jobs"]:
            return {"status": "no_data"}
            
        jobs = self.metrics["processing_jobs"]
        
        return {
            "total_jobs": len(jobs),
            "avg_duration_per_page": sum(j["duration_per_page"] for j in jobs) / len(jobs),
            "avg_memory_mb": sum(j["memory_used_mb"] for j in jobs) / len(jobs),
            "total_tables": sum(j["tables_extracted"] for j in jobs),
            "total_images": sum(j["images_extracted"] for j in jobs),
            "total_errors": sum(j["errors"] for j in jobs),
            "success_rate": sum(1 for j in jobs if j["errors"] == 0) / len(jobs) * 100
        }
        
    def export_metrics(self, filepath: str):
        """Export metrics to file"""
        with open(filepath, 'w') as f:
            json.dump({
                "summary": self.get_metrics_summary(),
                "detailed": self.metrics
            }, f, indent=2)

# Global monitor instance
pdf_monitor = PDFProcessingMonitor()
