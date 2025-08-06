#!/usr/bin/env python3
"""
FLIR T560 Real-Time Simulation Script
====================================

This script simulates a live FLIR T560 thermal camera feed by monitoring
a directory for new thermal images and automatically processing them
through the Thermal Eye API.

Usage:
    python simulate_live_feed.py --source_dir /path/to/images --interval_sec 10 --substation_code SUB001

Author: Production System for Tata Power Thermal Eye
"""

import argparse
import asyncio
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Set, Optional
import shutil
import sys
import signal
import aiohttp
import aiofiles
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ThermalImageProcessor:
    """Handles processing of thermal images through the API"""
    
    def __init__(self, api_base_url: str, substation_code: str):
        self.api_base_url = api_base_url.rstrip('/')
        self.substation_code = substation_code
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Statistics
        self.processed_count = 0
        self.failed_count = 0
        self.start_time = datetime.now()
        
    async def initialize(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60)
        )
        
    async def cleanup(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
    
    async def process_image(self, image_path: Path, processed_dir: Path) -> bool:
        """
        Process a single thermal image through the API
        
        Args:
            image_path: Path to the thermal image
            processed_dir: Directory to move processed images
            
        Returns:
            True if processing succeeded, False otherwise
        """
        
        if not self.session:
            logger.error("HTTP session not initialized")
            return False
            
        try:
            logger.info(f"📷 Processing thermal image: {image_path.name}")
            
            # Read the image file
            async with aiofiles.open(image_path, 'rb') as f:
                image_data = await f.read()
            
            # Prepare the upload request
            data = aiohttp.FormData()
            data.add_field('file', 
                          image_data, 
                          filename=image_path.name,
                          content_type='image/jpeg')
            data.add_field('substation_code', self.substation_code)
            data.add_field('ambient_temperature', '34.0')  # Tata Power standard
            data.add_field('notes', f'Simulated FLIR T560 capture - {datetime.now().isoformat()}')
            
            # Upload to the API
            upload_url = f"{self.api_base_url}/api/upload/thermal"
            
            async with self.session.post(upload_url, data=data) as response:
                response_text = await response.text()
                
                if response.status == 201:
                    # Success
                    response_data = await response.json() if response.content_type == 'application/json' else {}
                    
                    logger.info(f"✅ Successfully processed {image_path.name}")
                    logger.info(f"   📊 Analysis ID: {response_data.get('analysis_id', 'Unknown')}")
                    logger.info(f"   🌡️  Status: {response_data.get('status', 'Unknown')}")
                    
                    # Move to processed directory
                    await self._move_to_processed(image_path, processed_dir)
                    
                    self.processed_count += 1
                    return True
                    
                else:
                    # API error
                    logger.error(f"❌ API error processing {image_path.name}")
                    logger.error(f"   Status: {response.status}")
                    logger.error(f"   Response: {response_text}")
                    
                    self.failed_count += 1
                    return False
                    
        except asyncio.TimeoutError:
            logger.error(f"⏰ Timeout processing {image_path.name}")
            self.failed_count += 1
            return False
            
        except Exception as e:
            logger.error(f"💥 Unexpected error processing {image_path.name}: {e}")
            self.failed_count += 1
            return False
    
    async def _move_to_processed(self, image_path: Path, processed_dir: Path):
        """Move processed image to archive directory"""
        
        try:
            # Create timestamped subdirectory
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            archive_dir = processed_dir / timestamp
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            # Move the file
            destination = archive_dir / image_path.name
            shutil.move(str(image_path), str(destination))
            
            logger.info(f"📁 Moved {image_path.name} to {archive_dir}")
            
        except Exception as e:
            logger.error(f"Failed to move {image_path.name} to processed archive: {e}")
    
    def get_statistics(self) -> dict:
        """Get processing statistics"""
        
        runtime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "processed_count": self.processed_count,
            "failed_count": self.failed_count,
            "total_attempts": self.processed_count + self.failed_count,
            "success_rate": (self.processed_count / max(1, self.processed_count + self.failed_count)) * 100,
            "runtime_seconds": runtime,
            "processing_rate": self.processed_count / max(1, runtime / 60)  # per minute
        }

class LiveFeedSimulator:
    """Main simulation controller"""
    
    def __init__(self, source_dir: str, interval_sec: int, substation_code: str, 
                 api_url: str = "http://localhost:8000"):
        self.source_dir = Path(source_dir)
        self.interval_sec = interval_sec
        self.substation_code = substation_code
        self.api_url = api_url
        
        # Create directories
        self.processed_dir = self.source_dir / "processed_archive"
        self.processed_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.processor = ThermalImageProcessor(api_url, substation_code)
        self.processed_files: Set[str] = set()
        self.running = True
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"🛑 Received signal {signum}, initiating graceful shutdown...")
        self.running = False
    
    async def initialize(self):
        """Initialize the simulator"""
        
        logger.info("🚀 Initializing FLIR T560 Live Feed Simulator")
        logger.info(f"   📁 Source directory: {self.source_dir}")
        logger.info(f"   ⏱️  Scan interval: {self.interval_sec} seconds")
        logger.info(f"   🏭 Substation code: {self.substation_code}")
        logger.info(f"   🌐 API URL: {self.api_url}")
        
        # Verify source directory exists
        if not self.source_dir.exists():
            raise ValueError(f"Source directory does not exist: {self.source_dir}")
        
        # Initialize processor
        await self.processor.initialize()
        
        # Test API connectivity
        await self._test_api_connectivity()
        
        logger.info("✅ Simulator initialized successfully")
    
    async def _test_api_connectivity(self):
        """Test connection to the Thermal Eye API"""
        
        try:
            health_url = f"{self.api_url}/api/health"
            
            async with self.processor.session.get(health_url) as response:
                if response.status == 200:
                    health_data = await response.json()
                    logger.info(f"✅ API connectivity verified")
                    logger.info(f"   🔄 API Status: {health_data.get('status', 'unknown')}")
                    logger.info(f"   🗄️  Database: {health_data.get('database', 'unknown')}")
                else:
                    logger.warning(f"⚠️ API health check returned status {response.status}")
                    
        except Exception as e:
            logger.warning(f"⚠️ Could not verify API connectivity: {e}")
            logger.warning("   Proceeding anyway - API may be starting up")
    
    async def run(self):
        """Main simulation loop"""
        
        logger.info("🎬 Starting live feed simulation")
        logger.info("   Press Ctrl+C to stop gracefully")
        
        try:
            while self.running:
                # Scan for new thermal images
                new_images = await self._scan_for_new_images()
                
                if new_images:
                    logger.info(f"🔍 Found {len(new_images)} new thermal images")
                    
                    # Process each new image
                    for image_path in new_images:
                        if not self.running:
                            break
                            
                        await self.processor.process_image(image_path, self.processed_dir)
                        
                        # Add to processed set
                        self.processed_files.add(image_path.name)
                
                # Print statistics every 5th cycle
                if self.processor.processed_count > 0 and self.processor.processed_count % 5 == 0:
                    self._print_statistics()
                
                # Wait for next scan
                if self.running:
                    await asyncio.sleep(self.interval_sec)
                    
        except KeyboardInterrupt:
            logger.info("🛑 Received interrupt signal")
        except Exception as e:
            logger.error(f"💥 Simulation error: {e}")
        finally:
            await self._shutdown()
    
    async def _scan_for_new_images(self) -> list[Path]:
        """Scan source directory for new thermal images"""
        
        new_images = []
        
        try:
            # Look for JPEG files
            for file_path in self.source_dir.glob("*.jpg"):
                if file_path.name not in self.processed_files:
                    # Verify it's a valid file (not still being written)
                    if await self._is_file_ready(file_path):
                        new_images.append(file_path)
            
            # Also check for .jpeg extension
            for file_path in self.source_dir.glob("*.jpeg"):
                if file_path.name not in self.processed_files:
                    if await self._is_file_ready(file_path):
                        new_images.append(file_path)
            
        except Exception as e:
            logger.error(f"Error scanning for new images: {e}")
        
        return new_images
    
    async def _is_file_ready(self, file_path: Path) -> bool:
        """Check if file is ready for processing (not still being written)"""
        
        try:
            # Check if file size is stable
            size1 = file_path.stat().st_size
            await asyncio.sleep(0.1)  # Brief wait
            size2 = file_path.stat().st_size
            
            # File is ready if size is stable and > 0
            return size1 == size2 and size1 > 0
            
        except Exception:
            return False
    
    def _print_statistics(self):
        """Print processing statistics"""
        
        stats = self.processor.get_statistics()
        
        logger.info("📊 SIMULATION STATISTICS")
        logger.info(f"   ✅ Images processed: {stats['processed_count']}")
        logger.info(f"   ❌ Failed: {stats['failed_count']}")
        logger.info(f"   📈 Success rate: {stats['success_rate']:.1f}%")
        logger.info(f"   ⏱️  Runtime: {stats['runtime_seconds']:.0f} seconds")
        logger.info(f"   🚀 Processing rate: {stats['processing_rate']:.1f} images/minute")
    
    async def _shutdown(self):
        """Graceful shutdown"""
        
        logger.info("🔄 Shutting down simulator...")
        
        # Print final statistics
        self._print_statistics()
        
        # Cleanup processor
        await self.processor.cleanup()
        
        logger.info("✅ Simulator shutdown complete")

async def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(
        description="FLIR T560 Live Feed Simulator for Tata Power Thermal Eye"
    )
    
    parser.add_argument(
        "--source_dir",
        required=True,
        help="Directory to monitor for new thermal images"
    )
    
    parser.add_argument(
        "--interval_sec",
        type=int,
        default=10,
        help="Scan interval in seconds (default: 10)"
    )
    
    parser.add_argument(
        "--substation_code",
        required=True,
        help="Substation code for uploaded images (e.g., SUB001)"
    )
    
    parser.add_argument(
        "--api_url",
        default="http://localhost:8000",
        help="Thermal Eye API base URL (default: http://localhost:8000)"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.interval_sec < 1:
        logger.error("Interval must be at least 1 second")
        sys.exit(1)
    
    if not os.path.exists(args.source_dir):
        logger.error(f"Source directory does not exist: {args.source_dir}")
        sys.exit(1)
    
    # Create and run simulator
    simulator = LiveFeedSimulator(
        source_dir=args.source_dir,
        interval_sec=args.interval_sec,
        substation_code=args.substation_code,
        api_url=args.api_url
    )
    
    try:
        await simulator.initialize()
        await simulator.run()
        
    except Exception as e:
        logger.error(f"💥 Simulator failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Run the simulator
    asyncio.run(main()) 