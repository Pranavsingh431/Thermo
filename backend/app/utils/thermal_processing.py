"""
Thermal image processing utilities
"""

import hashlib
import logging
import os
from datetime import datetime
from typing import Optional, Dict, Tuple, List
from PIL import Image, ExifTags
from PIL.ExifTags import TAGS, GPSTAGS
import uuid

from app.config import settings

logger = logging.getLogger(__name__)

class ThermalImageProcessor:
    """Process thermal images and extract metadata"""
    
    def __init__(self):
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']
    
    def validate_image_file(self, filename: str, file_size: int) -> Tuple[bool, str]:
        """Validate uploaded image file"""
        
        # Check file extension
        file_ext = os.path.splitext(filename.lower())[1]
        if file_ext not in self.supported_formats:
            return False, f"Unsupported file format: {file_ext}"
        
        # Check file size
        if file_size > settings.MAX_FILE_SIZE:
            max_size_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
            return False, f"File too large. Maximum size: {max_size_mb}MB"
        
        # Check filename pattern (optional)
        if not filename.startswith('FLIR'):
            logger.warning(f"Non-FLIR filename detected: {filename}")
        
        return True, "Valid image file"
    
    def calculate_file_hash(self, file_content: bytes) -> str:
        """Calculate SHA-256 hash of file content for deduplication"""
        return hashlib.sha256(file_content).hexdigest()
    
    def extract_image_metadata(self, image_path: str) -> Dict:
        """Extract comprehensive metadata from thermal image"""
        metadata = {
            'camera_model': None,
            'camera_software_version': None,
            'image_width': None,
            'image_height': None,
            'latitude': None,
            'longitude': None,
            'altitude': None,
            'gps_timestamp': None,
            'capture_timestamp': None,
            'ambient_temperature': None,
            'camera_settings': {}
        }
        
        try:
            with Image.open(image_path) as img:
                # Basic image info
                metadata['image_width'] = img.width
                metadata['image_height'] = img.height
                
                # Extract EXIF data
                exif_data = img._getexif()
                if exif_data:
                    metadata.update(self._parse_exif_data(exif_data))
                
        except Exception as e:
            logger.error(f"Failed to extract metadata from {image_path}: {e}")
        
        return metadata
    
    def _parse_exif_data(self, exif_data: dict) -> Dict:
        """Parse EXIF data and extract relevant information"""
        parsed = {}
        
        for tag, value in exif_data.items():
            tag_name = TAGS.get(tag, tag)
            
            if tag_name == 'Make':
                parsed['camera_model'] = str(value)
            elif tag_name == 'Model':
                if parsed.get('camera_model'):
                    parsed['camera_model'] += f" {value}"
                else:
                    parsed['camera_model'] = str(value)
            elif tag_name == 'Software':
                parsed['camera_software_version'] = str(value)
            elif tag_name == 'DateTime':
                parsed['capture_timestamp'] = self._parse_datetime(str(value))
            elif tag_name == 'GPSInfo':
                gps_data = self._parse_gps_data(value)
                parsed.update(gps_data)
            
            # Store additional camera settings
            elif tag_name in ['ExposureTime', 'FNumber', 'ISO', 'FocalLength']:
                if 'camera_settings' not in parsed:
                    parsed['camera_settings'] = {}
                parsed['camera_settings'][tag_name] = str(value)
        
        return parsed
    
    def _parse_gps_data(self, gps_info: dict) -> Dict:
        """Parse GPS information from EXIF data"""
        gps_data = {}
        
        try:
            # Extract GPS coordinates
            lat = self._get_decimal_coords(
                gps_info.get(2),  # GPSLatitude
                gps_info.get(1)   # GPSLatitudeRef
            )
            lon = self._get_decimal_coords(
                gps_info.get(4),  # GPSLongitude
                gps_info.get(3)   # GPSLongitudeRef
            )
            
            if lat is not None and lon is not None:
                gps_data['latitude'] = lat
                gps_data['longitude'] = lon
            
            # Extract altitude
            if 6 in gps_info:  # GPSAltitude
                altitude_ref = gps_info.get(5, 0)  # GPSAltitudeRef
                altitude = float(gps_info[6])
                if altitude_ref == 1:  # Below sea level
                    altitude = -altitude
                gps_data['altitude'] = altitude
            
            # Extract GPS timestamp
            if 7 in gps_info and 29 in gps_info:  # GPSTimeStamp and GPSDateStamp
                gps_data['gps_timestamp'] = self._parse_gps_timestamp(
                    gps_info[7], gps_info[29]
                )
            
        except Exception as e:
            logger.error(f"Failed to parse GPS data: {e}")
        
        return gps_data
    
    def _get_decimal_coords(self, coords, coords_ref):
        """Convert GPS coordinates to decimal format"""
        if not coords or not coords_ref:
            return None
        
        try:
            decimal_degrees = coords[0] + coords[1]/60 + coords[2]/3600
            if coords_ref in ['S', 'W']:
                decimal_degrees = -decimal_degrees
            return decimal_degrees
        except (IndexError, TypeError, ZeroDivisionError):
            return None
    
    def _parse_gps_timestamp(self, time_stamp, date_stamp):
        """Parse GPS timestamp from EXIF data"""
        try:
            time_str = f"{int(time_stamp[0]):02d}:{int(time_stamp[1]):02d}:{int(time_stamp[2]):02d}"
            datetime_str = f"{date_stamp} {time_str}"
            return datetime.strptime(datetime_str, "%Y:%m:%d %H:%M:%S")
        except Exception:
            return None
    
    def _parse_datetime(self, datetime_str: str):
        """Parse datetime string from EXIF"""
        try:
            return datetime.strptime(datetime_str, "%Y:%m:%d %H:%M:%S")
        except ValueError:
            try:
                return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return None
    
    def find_matching_substation(self, latitude: float, longitude: float, substations: List) -> Optional[int]:
        """Find the closest substation to the image coordinates"""
        if not latitude or not longitude or not substations:
            return None
        
        closest_substation = None
        min_distance = float('inf')
        
        for substation in substations:
            if substation.is_point_within_boundary(latitude, longitude):
                return substation.id
            
            # If not within boundary, find closest
            distance = substation.get_distance_to_point(latitude, longitude)
            if distance < min_distance:
                min_distance = distance
                closest_substation = substation
        
        # Return closest if within reasonable distance (5km)
        if closest_substation and min_distance <= 5000:
            return closest_substation.id
        
        return None
    
    def create_batch_id(self) -> str:
        """Create a unique batch ID for processing"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"batch_{timestamp}_{unique_id}"
    
    def save_uploaded_file(self, file_content: bytes, filename: str, batch_id: str) -> str:
        """Save uploaded file to disk temporarily"""
        upload_dir = settings.UPLOAD_DIR
        os.makedirs(upload_dir, exist_ok=True)
        
        # Create subdirectory for batch
        batch_dir = os.path.join(upload_dir, batch_id)
        os.makedirs(batch_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(batch_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        return file_path
    
    def cleanup_batch_files(self, batch_id: str) -> bool:
        """Clean up temporary files after processing"""
        try:
            batch_dir = os.path.join(settings.UPLOAD_DIR, batch_id)
            if os.path.exists(batch_dir):
                import shutil
                shutil.rmtree(batch_dir)
                logger.info(f"Cleaned up batch files for {batch_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to cleanup batch {batch_id}: {e}")
        return False
    
    def analyze_thermal_colors(self, image_path: str) -> Dict:
        """Analyze thermal color distribution for basic hotspot detection"""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Convert to numpy array for analysis
                import numpy as np
                img_array = np.array(img)
                
                # Count thermal color patterns
                red_pixels = np.sum(img_array[:,:,0] > 200)
                yellow_pixels = np.sum(
                    (img_array[:,:,0] > 200) & 
                    (img_array[:,:,1] > 200) & 
                    (img_array[:,:,2] < 100)
                )
                blue_pixels = np.sum(img_array[:,:,2] > 200)
                
                total_pixels = img_array.shape[0] * img_array.shape[1]
                
                return {
                    'hot_pixel_count': int(red_pixels),
                    'warm_pixel_count': int(yellow_pixels),
                    'cold_pixel_count': int(blue_pixels),
                    'hot_percentage': float(red_pixels / total_pixels * 100),
                    'warm_percentage': float(yellow_pixels / total_pixels * 100),
                    'cold_percentage': float(blue_pixels / total_pixels * 100),
                    'total_pixels': int(total_pixels)
                }
        except Exception as e:
            logger.error(f"Failed to analyze thermal colors: {e}")
            return {}
    
    def estimate_temperature_from_colors(self, color_analysis: Dict, ambient_temp: float = 34.0) -> Dict:
        """Estimate temperature ranges based on thermal color analysis"""
        estimates = {
            'estimated_max_temp': ambient_temp,
            'estimated_min_temp': ambient_temp,
            'estimated_avg_temp': ambient_temp,
            'hotspot_detected': False
        }
        
        try:
            hot_percentage = color_analysis.get('hot_percentage', 0)
            warm_percentage = color_analysis.get('warm_percentage', 0)
            
            # Simple estimation based on color distribution
            if hot_percentage > 5:  # More than 5% hot pixels
                estimates['estimated_max_temp'] = ambient_temp + 30 + (hot_percentage * 2)
                estimates['hotspot_detected'] = True
            elif warm_percentage > 10:  # More than 10% warm pixels
                estimates['estimated_max_temp'] = ambient_temp + 15 + warm_percentage
            
            # Estimate average temperature
            temp_offset = (hot_percentage * 25 + warm_percentage * 10) / 100
            estimates['estimated_avg_temp'] = ambient_temp + temp_offset
            
            # Cold areas indicate lower baseline
            cold_percentage = color_analysis.get('cold_percentage', 0)
            if cold_percentage > 20:
                estimates['estimated_min_temp'] = ambient_temp - 10
            
        except Exception as e:
            logger.error(f"Failed to estimate temperatures: {e}")
        
        return estimates

# Global thermal processor instance
thermal_processor = ThermalImageProcessor() 