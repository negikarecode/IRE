import logging
import subprocess
import os
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from abc import ABC, abstractmethod

logger = logging.getLogger("virus_scan")


class VirusScanEngine(ABC):
    """Abstract base class for virus scan engines"""
    
    @abstractmethod
    async def scan_file(self, file_path: str) -> Dict[str, Any]:
        """
        Scan a file for viruses.
        
        Returns:
            dict with keys: status (clean/infected/error), engine, scan_timestamp, details
        """
        pass


class ClamAVScanEngine(VirusScanEngine):
    """ClamAV virus scan engine"""
    
    def __init__(self, clamscan_path: str = "/usr/bin/clamscan"):
        self.clamscan_path = clamscan_path
        self.engine_name = "clamav"
    
    async def scan_file(self, file_path: str) -> Dict[str, Any]:
        """Scan file using ClamAV"""
        try:
            # Run clamscan command
            result = subprocess.run(
                [self.clamscan_path, file_path],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            # Parse output
            output = result.stdout + result.stderr
            
            if result.returncode == 0:
                # No virus found
                return {
                    "status": "clean",
                    "engine": self.engine_name,
                    "scan_timestamp": datetime.now(timezone.utc).isoformat(),
                    "details": output
                }
            elif result.returncode == 1:
                # Virus found
                return {
                    "status": "infected",
                    "engine": self.engine_name,
                    "scan_timestamp": datetime.now(timezone.utc).isoformat(),
                    "details": output
                }
            else:
                # Error occurred
                return {
                    "status": "error",
                    "engine": self.engine_name,
                    "scan_timestamp": datetime.now(timezone.utc).isoformat(),
                    "details": output
                }
                
        except subprocess.TimeoutExpired:
            logger.error(f"[VIRUS_SCAN_TIMEOUT] File: {file_path}")
            return {
                "status": "error",
                "engine": self.engine_name,
                "scan_timestamp": datetime.now(timezone.utc).isoformat(),
                "details": "Scan timed out"
            }
        except FileNotFoundError:
            logger.error(f"[VIRUS_SCAN_NOT_FOUND] ClamAV not found at {self.clamscan_path}")
            return {
                "status": "error",
                "engine": self.engine_name,
                "scan_timestamp": datetime.now(timezone.utc).isoformat(),
                "details": "ClamAV not installed"
            }
        except Exception as e:
            logger.error(f"[VIRUS_SCAN_ERROR] File: {file_path}, Error: {str(e)}")
            return {
                "status": "error",
                "engine": self.engine_name,
                "scan_timestamp": datetime.now(timezone.utc).isoformat(),
                "details": str(e)
            }


class MockScanEngine(VirusScanEngine):
    """Mock virus scan engine for testing/development"""
    
    def __init__(self):
        self.engine_name = "mock"
    
    async def scan_file(self, file_path: str) -> Dict[str, Any]:
        """Mock scan - always returns clean"""
        logger.info(f"[MOCK_VIRUS_SCAN] File: {file_path}")
        return {
            "status": "clean",
            "engine": self.engine_name,
            "scan_timestamp": datetime.now(timezone.utc).isoformat(),
            "details": "Mock scan - no actual virus scanning performed"
        }


class VirusScanService:
    """Service for managing virus scanning of uploaded files"""
    
    def __init__(self, engine: Optional[VirusScanEngine] = None):
        self.engine = engine or self._get_default_engine()
    
    def _get_default_engine(self) -> VirusScanEngine:
        """Get the default virus scan engine based on configuration"""
        from app.config import settings
        
        scan_engine = os.getenv("VIRUS_SCAN_ENGINE", "mock").lower()
        
        if scan_engine == "clamav":
            clamscan_path = os.getenv("CLAMSCAN_PATH", "/usr/bin/clamscan")
            return ClamAVScanEngine(clamscan_path)
        else:
            # Default to mock for development
            return MockScanEngine()
    
    async def scan_file(self, file_path: str) -> Dict[str, Any]:
        """
        Scan a file for viruses.
        
        Args:
            file_path: Path to the file to scan
            
        Returns:
            dict with scan results
        """
        logger.info(f"[VIRUS_SCAN_START] File: {file_path}, Engine: {self.engine.engine_name}")
        
        result = await self.engine.scan_file(file_path)
        
        logger.info(f"[VIRUS_SCAN_COMPLETE] File: {file_path}, Status: {result['status']}")
        
        return result
    
    async def scan_file_content(self, file_content: bytes, original_filename: str) -> Dict[str, Any]:
        """
        Scan file content by writing to temp file first.
        
        Args:
            file_content: File content as bytes
            original_filename: Original filename for extension
            
        Returns:
            dict with scan results
        """
        import tempfile
        
        # Create temp file
        with tempfile.NamedTemporaryFile(
            suffix=os.path.splitext(original_filename)[1],
            delete=False
        ) as temp_file:
            temp_path = temp_file.name
            temp_file.write(file_content)
        
        try:
            # Scan the temp file
            result = await self.scan_file(temp_path)
            return result
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"[TEMP_FILE_CLEANUP_ERROR] {e}")


# Global virus scan service instance
_virus_scan_service: Optional[VirusScanService] = None


def get_virus_scan_service() -> VirusScanService:
    """Get or create the global virus scan service instance"""
    global _virus_scan_service
    if _virus_scan_service is None:
        _virus_scan_service = VirusScanService()
    return _virus_scan_service
