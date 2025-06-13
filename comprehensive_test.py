#!/usr/bin/env python3
"""
🧪 SIMPLE PIPELINE TEST SUITE
Tests the PRISMY translation pipeline

Usage:
    python comprehensive_test.py --quick
    python comprehensive_test.py --api-only
"""

import requests
import json
import time
import os
import sys
from pathlib import Path
from typing import Dict, List
import logging
from datetime import datetime
import argparse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PipelineTestSuite:
    """Simple test suite for PRISMY translation pipeline"""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.temp_dir = Path("test_temp")
        self.temp_dir.mkdir(exist_ok=True)
        
        # Test content
        self.test_content = """Bản quyền © Đại học Stanford

ĐÁNH GIÁ CÁC ỨNG DỤNG AI TRONG CHĂM SÓC SỨC KHỎE

Tài liệu này trình bày về việc ứng dụng trí tuệ nhân tạo trong y tế.
Các nghiên cứu cho thấy AI có thể cải thiện chẩn đoán và điều trị bệnh nhân.
Hệ thống học máy được sử dụng để phân tích dữ liệu y tế phức tạp.

Thách thức chính bao gồm:
- Đảm bảo tính chính xác của model
- Bảo vệ quyền riêng tư bệnh nhân
- Giảm thiểu thiên kiến trong thuật toán
- Tuân thủ các quy định y tế

Kết luận: AI có tiềm năng lớn trong chăm sóc sức khỏe nhưng cần được triển khai cẩn thận."""
        
    def create_test_file(self) -> Path:
        """Create a test file"""
        logger.info("🔧 Creating test file...")
        
        test_file = self.temp_dir / "test_vietnamese.txt"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(self.test_content)
            
        logger.info(f"📁 Created test file: {test_file}")
        return test_file
        
    def test_api_health(self) -> bool:
        """Test API health endpoint"""
        logger.info("🏥 Testing API health...")
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            if response.status_code == 200:
                logger.info("✅ API health check passed")
                return True
            else:
                logger.error(f"❌ API health check failed: {response.status_code}")
                return False
        except requests.RequestException as e:
            logger.error(f"❌ API health check failed: {e}")
            return False
            
    def test_api_endpoints(self) -> Dict[str, bool]:
        """Test basic API endpoints"""
        logger.info("🔌 Testing API endpoints...")
        results = {}
        
        endpoints = [
            ("GET", "/", "Root endpoint"),
            ("GET", "/health", "Health check"),
        ]
        
        for method, endpoint, description in endpoints:
            try:
                response = requests.get(f"{self.api_url}{endpoint}", timeout=10)
                success = response.status_code in [200, 307]  # 307 for redirects
                results[endpoint] = success
                status = "✅" if success else "❌"
                logger.info(f"{status} {description}: {response.status_code}")
            except Exception as e:
                results[endpoint] = False
                logger.error(f"❌ {description}: {e}")
                
        return results
            
    def test_translation_pipeline(self, source_lang: str = "vi", target_lang: str = "en", tier: str = "basic") -> Dict:
        """Test complete translation pipeline"""
        scenario_name = f"{source_lang}→{target_lang} ({tier})"
        logger.info(f"🔄 Testing: {scenario_name}")
        
        result = {
            "scenario": scenario_name,
            "success": False,
            "errors": [],
            "job_id": None
        }
        
        try:
            # Create test file
            test_file = self.create_test_file()
            
            # Step 1: Upload and start translation
            logger.info(f"📤 Step 1: Uploading file {test_file.name}")
            
            with open(test_file, 'rb') as f:
                files = {'file': (test_file.name, f, 'application/octet-stream')}
                data = {
                    'source_lang': source_lang,
                    'target_lang': target_lang,
                    'tier': tier
                }
                
                response = requests.post(
                    f"{self.api_url}/api/v1/large/translate",
                    files=files,
                    data=data,
                    timeout=30
                )
                
            if response.status_code != 200:
                result["errors"].append(f"Upload failed: {response.status_code}")
                logger.error(f"❌ Upload failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return result
                
            upload_result = response.json()
            result["job_id"] = upload_result.get("job_id")
            logger.info(f"✅ Upload successful: {result['job_id']}")
            
            # Step 2: Monitor job progress
            logger.info("⏳ Step 2: Monitoring job progress")
            max_wait = 120  # 2 minutes max
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                status_response = requests.get(
                    f"{self.api_url}/api/v1/large/status/{result['job_id']}",
                    timeout=10
                )
                
                if status_response.status_code != 200:
                    result["errors"].append(f"Status check failed: {status_response.status_code}")
                    break
                    
                status_data = status_response.json()
                job_status = status_data.get("status")
                progress = status_data.get("progress", 0)
                
                logger.info(f"📊 Job status: {job_status} ({progress}%)")
                
                if job_status == "completed":
                    logger.info("✅ Job completed successfully")
                    result["success"] = True
                    break
                elif job_status == "failed":
                    result["errors"].append(f"Job failed: {status_data.get('error', 'Unknown error')}")
                    logger.error(f"❌ Job failed: {status_data.get('error')}")
                    break
                    
                time.sleep(3)
            else:
                result["errors"].append("Job timeout - took longer than 2 minutes")
                logger.error("❌ Job timeout")
                return result
                
            # Step 3: Download result (if completed)
            if result["success"]:
                logger.info("📥 Step 3: Downloading result")
                
                download_response = requests.get(
                    f"{self.api_url}/api/v1/large/download/{result['job_id']}",
                    timeout=30
                )
                
                if download_response.status_code == 200:
                    # Save downloaded file
                    download_file = self.temp_dir / f"result_{result['job_id']}.txt"
                    with open(download_file, 'wb') as f:
                        f.write(download_response.content)
                    logger.info(f"✅ Download successful: {download_file}")
                    
                    # Validate content
                    with open(download_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    target_lang_name = self._get_language_name(target_lang)
                    expected_format = f"[MOCK-TRANSLATED to {target_lang_name}]:"
                    
                    if expected_format in content:
                        logger.info(f"✅ Translation format validated: {expected_format}")
                        logger.info(f"📄 Content preview: {content[:200]}...")
                    else:
                        result["errors"].append(f"Invalid translation format. Expected: {expected_format}")
                        result["success"] = False
                        logger.error(f"❌ Invalid translation format")
                        logger.error(f"📄 Actual content: {content[:200]}...")
                else:
                    result["errors"].append(f"Download failed: {download_response.status_code}")
                    result["success"] = False
                    logger.error(f"❌ Download failed: {download_response.status_code}")
                    
        except Exception as e:
            result["errors"].append(f"Unexpected error: {str(e)}")
            logger.error(f"❌ {scenario_name} failed: {e}")
            
        status = "✅" if result["success"] else "❌"
        logger.info(f"{status} {scenario_name} {'completed' if result['success'] else 'failed'}")
        
        return result
        
    def _get_language_name(self, lang_code: str) -> str:
        """Get language name from code"""
        lang_names = {
            'en': 'English', 'vi': 'Vietnamese', 'zh': 'Chinese', 'ja': 'Japanese',
            'ko': 'Korean', 'fr': 'French', 'de': 'German', 'es': 'Spanish',
            'ar': 'Arabic', 'hi': 'Hindi', 'th': 'Thai', 'ru': 'Russian'
        }
        return lang_names.get(lang_code.lower(), lang_code.capitalize())
        
    def run_quick_test(self) -> Dict:
        """Run quick test with basic scenarios"""
        logger.info("⚡ Starting quick pipeline test...")
        start_time = time.time()
        
        test_summary = {
            "start_time": datetime.now().isoformat(),
            "test_type": "quick",
            "api_health": False,
            "api_endpoints": {},
            "translation_test": {},
            "overall_success": False,
            "total_time": 0
        }
        
        try:
            # 1. Test API health
            test_summary["api_health"] = self.test_api_health()
            if not test_summary["api_health"]:
                logger.error("❌ API health check failed - stopping tests")
                return test_summary
                
            # 2. Test API endpoints
            test_summary["api_endpoints"] = self.test_api_endpoints()
            
            # 3. Test translation pipeline
            logger.info("🌍 Testing translation pipeline...")
            test_summary["translation_test"] = self.test_translation_pipeline("vi", "en", "basic")
                    
            # Calculate summary
            total_time = time.time() - start_time
            test_summary["total_time"] = total_time
            
            test_summary["overall_success"] = (
                test_summary["api_health"] and
                test_summary["translation_test"].get("success", False)
            )
            
        except Exception as e:
            logger.error(f"❌ Quick test failed: {e}")
            test_summary["error"] = str(e)
            
        test_summary["end_time"] = datetime.now().isoformat()
        
        # Log final summary
        status = "✅ PASSED" if test_summary["overall_success"] else "❌ FAILED"
        logger.info(f"\n🎯 QUICK TEST {status}")
        logger.info(f"⏱️ Total time: {test_summary['total_time']:.1f} seconds")
        logger.info(f"🏥 API Health: {'✅' if test_summary['api_health'] else '❌'}")
        logger.info(f"🌍 Translation: {'✅' if test_summary['translation_test'].get('success') else '❌'}")
        
        return test_summary
        
    def cleanup(self):
        """Clean up temporary files"""
        try:
            import shutil
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
            logger.info("🧹 Cleanup completed")
        except Exception as e:
            logger.warning(f"⚠️ Cleanup warning: {e}")

def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="PRISMY Pipeline Test")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--quick", action="store_true", help="Quick test (default)")
    parser.add_argument("--api-only", action="store_true", help="Test API health only")
    
    args = parser.parse_args()
    
    # Initialize test suite
    test_suite = PipelineTestSuite(args.api_url)
    
    try:
        if args.api_only:
            # API health test only
            logger.info("🔌 Running API health test only...")
            health_ok = test_suite.test_api_health()
            if health_ok:
                logger.info("🎉 API is healthy!")
                sys.exit(0)
            else:
                logger.error("❌ API health check failed!")
                sys.exit(1)
        else:
            # Quick test (default)
            logger.info("⚡ Running quick pipeline test...")
            results = test_suite.run_quick_test()
            
            if results.get("overall_success"):
                logger.info("🎉 QUICK TEST PASSED! Pipeline is working correctly.")
                sys.exit(0)
            else:
                logger.error("❌ QUICK TEST FAILED! Check the logs for details.")
                sys.exit(1)
                
    except KeyboardInterrupt:
        logger.info("⏹️ Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"💥 Test suite failed: {e}")
        sys.exit(1)
    finally:
        test_suite.cleanup()

if __name__ == "__main__":
    main()