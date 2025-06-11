"""
Feature Flag System
Control rollout of new features
"""
import os
from typing import Dict, Any
from enum import Enum

class FeatureStage(Enum):
    OFF = "off"
    INTERNAL = "internal"
    BETA = "beta"
    GA = "ga"  # General Availability

class FeatureFlags:
    """Manage feature rollout"""
    
    # Feature definitions
    FEATURES = {
        "advanced_pdf_processing": {
            "stage": FeatureStage.OFF,
            "description": "Advanced PDF with tables, images, OCR",
            "config": {
                "table_extraction": True,
                "ocr_enabled": True,
                "formula_extraction": False  # Phase 2
            }
        },
        "smart_chunking": {
            "stage": FeatureStage.GA,
            "description": "Intelligent text chunking",
            "config": {}
        }
    }
    
    @classmethod
    def is_enabled(cls, feature: str, user_tier: str = "standard") -> bool:
        """Check if feature is enabled"""
        if feature not in cls.FEATURES:
            return False
            
        feature_config = cls.FEATURES[feature]
        stage = feature_config["stage"]
        
        # Feature rollout logic
        if stage == FeatureStage.OFF:
            return False
        elif stage == FeatureStage.INTERNAL:
            return os.getenv("PRISMY_INTERNAL_USER") == "true"
        elif stage == FeatureStage.BETA:
            return user_tier in ["premium", "beta"]
        elif stage == FeatureStage.GA:
            return True
            
        return False
        
    @classmethod
    def get_config(cls, feature: str) -> Dict[str, Any]:
        """Get feature configuration"""
        if feature in cls.FEATURES:
            return cls.FEATURES[feature]["config"]
        return {}
        
    @classmethod
    def set_stage(cls, feature: str, stage: FeatureStage):
        """Update feature stage (for testing/rollout)"""
        if feature in cls.FEATURES:
            cls.FEATURES[feature]["stage"] = stage
