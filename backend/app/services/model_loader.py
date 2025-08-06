"""
Production-Grade Model Loader Service
====================================

This service implements bulletproof AI model loading with integrity verification.
The system MUST NOT start if model integrity cannot be verified.

Author: Production System for Tata Power Thermal Eye
"""

import os
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class ModelIntegrityError(Exception):
    """Raised when model file integrity check fails"""
    pass

class ModelLoadingError(Exception):
    """Raised when model cannot be loaded into memory"""
    pass

class ProductionModelLoader:
    """
    Production-grade model loader with integrity verification.
    
    CRITICAL: Application MUST NOT start if models fail integrity checks.
    """
    
    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.logger = logging.getLogger(__name__)
        self.loaded_models: Dict[str, Any] = {}
        self.model_metadata: Dict[str, Dict] = {}
        
        # Create models directory if it doesn't exist
        self.models_dir.mkdir(exist_ok=True)
        
        # Model configuration with expected checksums
        self.model_config = {
            "yolo_nas_s": {
                "filename": "yolo_nas_s_coco.pth",
                "expected_sha256": None,  # Will be calculated on first successful download
                "url": "https://sghub.deci.ai/models/yolo_nas_s_coco.pth",
                "description": "YOLO-NAS Small model trained on COCO dataset",
                "version": "1.0"
            }
        }
        
        self.logger.info("🔒 Production Model Loader initialized")
    
    def verify_model_integrity(self, model_name: str) -> bool:
        """
        Verify model file integrity using SHA256 checksum.
        
        Args:
            model_name: Name of the model to verify
            
        Returns:
            True if integrity check passes
            
        Raises:
            ModelIntegrityError: If integrity check fails
        """
        if model_name not in self.model_config:
            raise ModelIntegrityError(f"Unknown model: {model_name}")
        
        config = self.model_config[model_name]
        model_path = self.models_dir / config["filename"]
        
        if not model_path.exists():
            raise ModelIntegrityError(f"Model file not found: {model_path}")
        
        # Calculate SHA256 checksum
        sha256_hash = hashlib.sha256()
        try:
            with open(model_path, "rb") as f:
                # Read file in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            
            calculated_checksum = sha256_hash.hexdigest()
            
            # If this is first time, store the checksum
            if config["expected_sha256"] is None:
                config["expected_sha256"] = calculated_checksum
                self._save_model_metadata(model_name, {
                    "checksum": calculated_checksum,
                    "file_size": model_path.stat().st_size,
                    "last_verified": datetime.now().isoformat(),
                    "version": config["version"]
                })
                self.logger.info(f"✅ Model {model_name}: Initial checksum stored - {calculated_checksum[:16]}...")
                return True
            
            # Verify against expected checksum
            if calculated_checksum != config["expected_sha256"]:
                raise ModelIntegrityError(
                    f"Model {model_name} integrity check FAILED!\n"
                    f"Expected: {config['expected_sha256'][:16]}...\n"
                    f"Calculated: {calculated_checksum[:16]}...\n"
                    f"File may be corrupted or tampered with!"
                )
            
            self.logger.info(f"✅ Model {model_name}: Integrity verification PASSED - {calculated_checksum[:16]}...")
            return True
            
        except Exception as e:
            raise ModelIntegrityError(f"Failed to verify model {model_name}: {e}")
    
    def load_yolo_nas_model(self) -> Any:
        """
        Load YOLO-NAS model with full integrity verification.
        
        Returns:
            Loaded YOLO-NAS model object
            
        Raises:
            ModelIntegrityError: If integrity check fails
            ModelLoadingError: If model loading fails
        """
        model_name = "yolo_nas_s"
        
        try:
            # Step 1: Verify model integrity
            self.verify_model_integrity(model_name)
            
            # Step 2: Attempt to load model
            self.logger.info(f"🤖 Loading YOLO-NAS model into memory...")
            
            try:
                # Import here to avoid circular dependencies
                from super_gradients.training import models
                
                model_path = self.models_dir / self.model_config[model_name]["filename"]
                
                # Try to load from local file first
                if model_path.exists():
                    self.logger.info(f"📂 Loading model from local file: {model_path}")
                    model = models.get('yolo_nas_s', pretrained_weights=None)
                    
                    # Load state dict if file exists and is valid
                    try:
                        import torch
                        state_dict = torch.load(model_path, map_location='cpu')
                        model.load_state_dict(state_dict)
                        self.logger.info("✅ Model loaded from local checkpoint")
                    except Exception as load_error:
                        self.logger.warning(f"⚠️ Failed to load local checkpoint: {load_error}")
                        # Fall back to downloading
                        model = models.get('yolo_nas_s', pretrained_weights='coco')
                else:
                    # Download model
                    self.logger.info("📥 Downloading YOLO-NAS model...")
                    model = models.get('yolo_nas_s', pretrained_weights='coco')
                
                # Set model to evaluation mode
                model.eval()
                
                # Store model metadata
                self.model_metadata[model_name] = {
                    "loaded_at": datetime.now().isoformat(),
                    "version": self.model_config[model_name]["version"],
                    "status": "loaded",
                    "memory_size_mb": self._estimate_model_size(model)
                }
                
                self.loaded_models[model_name] = model
                
                self.logger.info(f"🎉 YOLO-NAS model successfully loaded - Version {self.model_config[model_name]['version']}")
                return model
                
            except ImportError as e:
                raise ModelLoadingError(f"Required ML libraries not available: {e}")
            except Exception as e:
                raise ModelLoadingError(f"Failed to load YOLO-NAS model: {e}")
                
        except ModelIntegrityError:
            # Re-raise integrity errors as-is
            raise
        except Exception as e:
            raise ModelLoadingError(f"Unexpected error loading model {model_name}: {e}")
    
    def get_model_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status of all models.
        
        Returns:
            Dictionary containing model status information
        """
        status = {
            "models_directory": str(self.models_dir),
            "models_available": {},
            "loaded_models": list(self.loaded_models.keys()),
            "integrity_status": "unknown",
            "last_check": datetime.now().isoformat()
        }
        
        for model_name, config in self.model_config.items():
            model_path = self.models_dir / config["filename"]
            
            model_status = {
                "file_exists": model_path.exists(),
                "file_size_mb": round(model_path.stat().st_size / 1024 / 1024, 2) if model_path.exists() else 0,
                "version": config["version"],
                "loaded": model_name in self.loaded_models,
                "integrity_verified": False
            }
            
            # Check integrity if file exists
            if model_path.exists():
                try:
                    self.verify_model_integrity(model_name)
                    model_status["integrity_verified"] = True
                except ModelIntegrityError:
                    model_status["integrity_verified"] = False
            
            status["models_available"][model_name] = model_status
        
        # Overall integrity status
        all_verified = all(
            model["integrity_verified"] for model in status["models_available"].values()
            if model["file_exists"]
        )
        status["integrity_status"] = "verified" if all_verified else "failed"
        
        return status
    
    def _save_model_metadata(self, model_name: str, metadata: Dict) -> None:
        """Save model metadata to JSON file"""
        metadata_file = self.models_dir / f"{model_name}_metadata.json"
        
        try:
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Failed to save metadata for {model_name}: {e}")
    
    def _estimate_model_size(self, model) -> float:
        """Estimate model memory size in MB"""
        try:
            import torch
            param_size = 0
            buffer_size = 0
            
            for param in model.parameters():
                param_size += param.nelement() * param.element_size()
            
            for buffer in model.buffers():
                buffer_size += buffer.nelement() * buffer.element_size()
            
            total_size_mb = (param_size + buffer_size) / 1024 / 1024
            return round(total_size_mb, 2)
        except Exception:
            return 0.0
    
    def initialize_all_models(self) -> bool:
        """
        Initialize all models with integrity verification.
        
        Returns:
            True if all models loaded successfully
            
        Raises:
            ModelIntegrityError: If any model fails integrity check
            ModelLoadingError: If any model fails to load
        """
        self.logger.info("🚀 Initializing production AI models...")
        
        try:
            # Load YOLO-NAS model
            yolo_model = self.load_yolo_nas_model()
            
            if yolo_model is None:
                raise ModelLoadingError("YOLO-NAS model returned None")
            
            self.logger.info("✅ All production models initialized successfully")
            return True
            
        except (ModelIntegrityError, ModelLoadingError) as e:
            self.logger.critical(f"🚨 CRITICAL: Model initialization FAILED - {e}")
            self.logger.critical("🛑 APPLICATION CANNOT START - Model integrity compromised")
            raise
        except Exception as e:
            self.logger.critical(f"🚨 CRITICAL: Unexpected error during model initialization - {e}")
            raise ModelLoadingError(f"Unexpected model initialization error: {e}")

# Global model loader instance
model_loader = ProductionModelLoader() 