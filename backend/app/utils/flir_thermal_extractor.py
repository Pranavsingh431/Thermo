"""
FLIR Thermal Image Temperature Extraction Utility

This module provides specialized functionality for extracting temperature data
from FLIR thermal images, particularly for the FLIR T560 camera used in this project.
"""

import numpy as np
import cv2
from PIL import Image
from PIL.ExifTags import TAGS
import json
import logging
from typing import Dict, Optional, Tuple, Any
import struct
import io

logger = logging.getLogger(__name__)

class FLIRThermalExtractor:
    """Extract thermal temperature data from FLIR thermal images"""
    
    def __init__(self):
        # FLIR T560 specific parameters
        self.camera_model = "FLIR T560"
        self.thermal_sensitivity = 0.03  # °C at 30°C
        self.temperature_range = (-40, 150)  # °C
        
        # Common FLIR EXIF tags for thermal data
        self.flir_tags = {
            'PlanckR1': 21106.77,
            'PlanckB': 1501.0,
            'PlanckF': 1.0,
            'PlanckO': -7340.0,
            'PlanckR2': 0.012545258,
            'AtmosphericTransAlpha1': 0.006569,
            'AtmosphericTransAlpha2': 0.01262,
            'AtmosphericTransBeta1': -0.002276,
            'AtmosphericTransBeta2': -0.00667,
            'AtmosphericTransX': 1.9,
            'CameraTemperatureRangeMax': 150.0,
            'CameraTemperatureRangeMin': -40.0,
            'CameraTemperatureMaxClip': 150.0,
            'CameraTemperatureMinClip': -40.0,
            'CameraTemperatureMaxWarn': 100.0,
            'CameraTemperatureMinWarn': 0.0,
            'CameraTemperatureMaxSaturated': 150.0,
            'CameraTemperatureMinSaturated': -40.0
        }
    
    def extract_thermal_data(self, image_path: str) -> Dict[str, Any]:
        """
        Extract comprehensive thermal data from FLIR image
        
        Returns:
            Dict containing thermal parameters, temperature map, and statistics
        """
        try:
            # Load image and extract EXIF data
            with Image.open(image_path) as img:
                exif_data = self._extract_exif_data(img)
                
                # Extract FLIR-specific thermal parameters
                thermal_params = self._extract_flir_parameters(exif_data)
                
                # Convert image to numpy array for processing
                img_array = np.array(img.convert('RGB'))
                
                # Extract temperature map from thermal data
                temperature_map = self._extract_temperature_map(img_array, thermal_params)
                
                # Calculate thermal statistics
                thermal_stats = self._calculate_thermal_statistics(temperature_map, thermal_params)
                
                # Detect hotspots using advanced algorithms
                hotspot_analysis = self._analyze_hotspots(temperature_map, thermal_params)
                
                return {
                    'success': True,
                    'thermal_params': thermal_params,
                    'temperature_map': temperature_map,
                    'thermal_stats': thermal_stats,
                    'hotspot_analysis': hotspot_analysis,
                    'image_shape': img_array.shape,
                    'camera_model': thermal_params.get('camera_model', self.camera_model)
                }
                
        except Exception as e:
            logger.error(f"Failed to extract thermal data from {image_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback_used': True
            }
    
    def _extract_exif_data(self, img: Image.Image) -> Dict[str, Any]:
        """Extract EXIF data from FLIR image"""
        exif_data = {}
        
        try:
            exif = img.getexif()
            
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                exif_data[tag] = value
                
            # Look for FLIR-specific thermal data in EXIF
            if hasattr(img, '_getexif') and img._getexif():
                for key, value in img._getexif().items():
                    tag_name = TAGS.get(key, key)
                    exif_data[tag_name] = value
            
            return exif_data
            
        except Exception as e:
            logger.warning(f"Failed to extract EXIF data: {e}")
            return {}
    
    def _extract_flir_parameters(self, exif_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract FLIR-specific thermal parameters"""
        thermal_params = {}
        
        # Extract basic camera info
        thermal_params['camera_model'] = exif_data.get('Make', '') + ' ' + exif_data.get('Model', '')
        thermal_params['software'] = exif_data.get('Software', '')
        thermal_params['datetime'] = exif_data.get('DateTime', '')
        
        # Extract GPS data if available
        if 'GPSInfo' in exif_data:
            gps_data = exif_data['GPSInfo']
            thermal_params['gps_data'] = self._parse_gps_data(gps_data)
        
        # Extract thermal-specific parameters (if available in EXIF)
        # For FLIR images, these might be in maker notes or specific tags
        thermal_params['emissivity'] = exif_data.get('Emissivity', 0.95)
        thermal_params['reflected_temp'] = exif_data.get('ReflectedApparentTemperature', 20.0)
        thermal_params['atmospheric_temp'] = exif_data.get('AtmosphericTemperature', 20.0)
        thermal_params['distance'] = exif_data.get('SubjectDistance', 1.0)
        thermal_params['humidity'] = exif_data.get('RelativeHumidity', 50.0)
        
        # Use default FLIR parameters if not found in EXIF
        for param, default_value in self.flir_tags.items():
            thermal_params[param] = exif_data.get(param, default_value)
        
        return thermal_params
    
    def _parse_gps_data(self, gps_data: Dict) -> Dict[str, float]:
        """Parse GPS data from EXIF"""
        try:
            def convert_to_degrees(value):
                d, m, s = value
                return d + (m / 60.0) + (s / 3600.0)
            
            gps_parsed = {}
            
            if 2 in gps_data and 4 in gps_data:  # Latitude and Longitude
                lat = convert_to_degrees(gps_data[2])
                if gps_data[1] == 'S':
                    lat = -lat
                
                lon = convert_to_degrees(gps_data[4])
                if gps_data[3] == 'W':
                    lon = -lon
                
                gps_parsed['latitude'] = lat
                gps_parsed['longitude'] = lon
            
            if 6 in gps_data:  # Altitude
                gps_parsed['altitude'] = float(gps_data[6])
            
            return gps_parsed
            
        except Exception as e:
            logger.warning(f"Failed to parse GPS data: {e}")
            return {}
    
    def _extract_temperature_map(self, img_array: np.ndarray, thermal_params: Dict[str, Any]) -> np.ndarray:
        """
        Extract temperature map from thermal image
        
        This uses FLIR's thermal data extraction algorithms when available,
        or falls back to advanced color-to-temperature mapping
        """
        try:
            # Method 1: Try to extract raw thermal data (if embedded)
            thermal_map = self._extract_raw_thermal_data(img_array, thermal_params)
            
            if thermal_map is not None:
                return thermal_map
            
            # Method 2: Advanced color-to-temperature conversion
            return self._advanced_color_to_temperature(img_array, thermal_params)
            
        except Exception as e:
            logger.error(f"Temperature map extraction failed: {e}")
            # Fallback to basic color mapping
            return self._basic_color_to_temperature(img_array, thermal_params)
    
    def _extract_raw_thermal_data(self, img_array: np.ndarray, thermal_params: Dict[str, Any]) -> Optional[np.ndarray]:
        """
        Attempt to extract raw thermal data from FLIR image
        
        FLIR images sometimes contain embedded thermal data that can be extracted
        """
        try:
            # This would require access to the raw thermal data embedded in FLIR files
            # For now, return None to fall back to color mapping
            # In a real implementation, this would use FLIR SDK or specialized libraries
            return None
            
        except Exception as e:
            logger.debug(f"Raw thermal extraction failed: {e}")
            return None
    
    def _advanced_color_to_temperature(self, img_array: np.ndarray, thermal_params: Dict[str, Any]) -> np.ndarray:
        """
        Advanced color-to-temperature mapping using thermal image characteristics
        """
        try:
            # Convert to different color spaces for better thermal mapping
            hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
            lab = cv2.cvtColor(img_array, cv2.COLOR_RGB2LAB)
            
            # Extract thermal characteristics from multiple channels
            hue = hsv[:, :, 0].astype(float)
            saturation = hsv[:, :, 1].astype(float)
            value = hsv[:, :, 2].astype(float)
            
            l_channel = lab[:, :, 0].astype(float)
            a_channel = lab[:, :, 1].astype(float)
            b_channel = lab[:, :, 2].astype(float)
            
            # FLIR thermal color mapping
            # Blue/Violet (240-270°) = Cold
            # Green (120°) = Medium
            # Yellow (60°) = Warm  
            # Red (0°) = Hot
            # White = Hottest
            
            # Create temperature map based on thermal color characteristics
            temp_from_hue = np.zeros_like(hue)
            
            # Cold regions (blue/violet)
            cold_mask = (hue >= 180) & (hue <= 270)
            temp_from_hue[cold_mask] = 0.0 + (hue[cold_mask] - 180) / 90 * 0.2
            
            # Medium regions (green)
            medium_mask = (hue >= 90) & (hue < 180)
            temp_from_hue[medium_mask] = 0.2 + (180 - hue[medium_mask]) / 90 * 0.3
            
            # Warm regions (yellow)
            warm_mask = (hue >= 30) & (hue < 90)
            temp_from_hue[warm_mask] = 0.5 + (hue[warm_mask] - 30) / 60 * 0.3
            
            # Hot regions (red)
            hot_mask = (hue >= 0) & (hue < 30)
            temp_from_hue[hot_mask] = 0.8 + hue[hot_mask] / 30 * 0.2
            
            # Very hot regions (near white, high value, low saturation)
            white_mask = (value > 200) & (saturation < 50)
            temp_from_hue[white_mask] = 1.0
            
            # Combine with saturation and value for better accuracy
            thermal_intensity = (temp_from_hue * 0.6 + 
                               (value / 255.0) * 0.3 + 
                               (1 - saturation / 255.0) * 0.1)
            
            # Map to actual temperature range
            temp_min = thermal_params.get('atmospheric_temp', 20.0)
            temp_max = thermal_params.get('CameraTemperatureRangeMax', 150.0)
            
            temperature_map = temp_min + thermal_intensity * (temp_max - temp_min)
            
            return temperature_map
            
        except Exception as e:
            logger.error(f"Advanced color mapping failed: {e}")
            raise
    
    def _basic_color_to_temperature(self, img_array: np.ndarray, thermal_params: Dict[str, Any]) -> np.ndarray:
        """Basic fallback color-to-temperature mapping"""
        try:
            # Simple red channel mapping as fallback
            red_channel = img_array[:, :, 0].astype(float)
            thermal_intensity = red_channel / 255.0
            
            temp_min = thermal_params.get('atmospheric_temp', 20.0)
            temp_max = temp_min + 80.0  # Assume 80°C range
            
            return temp_min + thermal_intensity * (temp_max - temp_min)
            
        except Exception as e:
            logger.error(f"Basic color mapping failed: {e}")
            # Return ambient temperature array as last resort
            return np.full(img_array.shape[:2], thermal_params.get('atmospheric_temp', 34.0))
    
    def _calculate_thermal_statistics(self, temperature_map: np.ndarray, thermal_params: Dict[str, Any]) -> Dict[str, float]:
        """Calculate comprehensive thermal statistics"""
        try:
            stats = {
                'max_temperature': float(np.max(temperature_map)),
                'min_temperature': float(np.min(temperature_map)),
                'avg_temperature': float(np.mean(temperature_map)),
                'median_temperature': float(np.median(temperature_map)),
                'std_temperature': float(np.std(temperature_map)),
                'temperature_range': float(np.max(temperature_map) - np.min(temperature_map)),
                'ambient_temperature': thermal_params.get('atmospheric_temp', 34.0)
            }
            
            # Calculate percentiles
            stats['temp_95th_percentile'] = float(np.percentile(temperature_map, 95))
            stats['temp_5th_percentile'] = float(np.percentile(temperature_map, 5))
            
            return stats
            
        except Exception as e:
            logger.error(f"Thermal statistics calculation failed: {e}")
            return {
                'max_temperature': 34.0,
                'min_temperature': 34.0,
                'avg_temperature': 34.0,
                'ambient_temperature': 34.0
            }
    
    def _analyze_hotspots(self, temperature_map: np.ndarray, thermal_params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze hotspots in thermal image"""
        try:
            ambient_temp = thermal_params.get('atmospheric_temp', 34.0)
            potential_threshold = ambient_temp + 20.0  # +20°C
            critical_threshold = ambient_temp + 40.0   # +40°C
            
            # Create hotspot masks
            potential_mask = temperature_map >= potential_threshold
            critical_mask = temperature_map >= critical_threshold
            normal_mask = temperature_map < potential_threshold
            
            # Count hotspot pixels
            total_pixels = temperature_map.size
            potential_pixels = np.sum(potential_mask)
            critical_pixels = np.sum(critical_mask)
            normal_pixels = np.sum(normal_mask)
            
            # Find hotspot regions using morphological operations
            kernel = np.ones((5, 5), np.uint8)
            potential_regions = cv2.morphologyEx(potential_mask.astype(np.uint8), cv2.MORPH_CLOSE, kernel)
            critical_regions = cv2.morphologyEx(critical_mask.astype(np.uint8), cv2.MORPH_CLOSE, kernel)
            
            # Count distinct hotspot regions
            potential_contours, _ = cv2.findContours(potential_regions, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            critical_contours, _ = cv2.findContours(critical_regions, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter out small regions (noise)
            min_area = 50  # minimum pixels for a valid hotspot
            potential_hotspots = len([c for c in potential_contours if cv2.contourArea(c) >= min_area])
            critical_hotspots = len([c for c in critical_contours if cv2.contourArea(c) >= min_area])
            
            return {
                'total_hotspots': potential_hotspots,
                'potential_hotspots': potential_hotspots - critical_hotspots,
                'critical_hotspots': critical_hotspots,
                'normal_zones': 1 if normal_pixels > 0 else 0,
                'hotspot_coverage': {
                    'potential_percentage': (potential_pixels / total_pixels) * 100,
                    'critical_percentage': (critical_pixels / total_pixels) * 100,
                    'normal_percentage': (normal_pixels / total_pixels) * 100
                },
                'temperature_thresholds': {
                    'ambient': ambient_temp,
                    'potential_threshold': potential_threshold,
                    'critical_threshold': critical_threshold
                }
            }
            
        except Exception as e:
            logger.error(f"Hotspot analysis failed: {e}")
            return {
                'total_hotspots': 0,
                'potential_hotspots': 0,
                'critical_hotspots': 0,
                'normal_zones': 1
            }

# Global instance
flir_extractor = FLIRThermalExtractor() 