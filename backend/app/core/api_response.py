"""
Standardized API Response Format

All endpoints must return responses in this standardized format.
"""

from typing import Any, Optional, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar('T')


class ErrorDetail(BaseModel):
    """Error detail structure"""
    code: str = Field(..., description="Error code for programmatic handling")
    details: dict = Field(default_factory=dict, description="Additional error details")


class SuccessResponse(BaseModel, Generic[T]):
    """Standardized success response format"""
    success: bool = Field(True, description="Indicates if the request was successful")
    message: str = Field(..., description="Human-readable success message")
    data: Optional[T] = Field(default_factory=dict, description="Response data")


class ErrorResponse(BaseModel):
    """Standardized error response format"""
    success: bool = Field(False, description="Indicates if the request was successful")
    message: str = Field(..., description="Human-readable error message")
    error: ErrorDetail = Field(..., description="Error details")


class APIResponse:
    """Helper class for creating standardized responses"""
    
    @staticmethod
    def success(
        message: str,
        data: Any = None,
        status_code: int = 200
    ) -> tuple:
        """
        Create a success response.
        
        Args:
            message: Success message
            data: Response data
            status_code: HTTP status code
            
        Returns:
            tuple of (response_dict, status_code)
        """
        response = SuccessResponse(
            success=True,
            message=message,
            data=data if data is not None else {}
        )
        return response.model_dump(), status_code
    
    @staticmethod
    def error(
        message: str,
        error_code: str,
        error_details: Optional[dict] = None,
        status_code: int = 400
    ) -> tuple:
        """
        Create an error response.
        
        Args:
            message: Error message
            error_code: Error code for programmatic handling
            error_details: Additional error details
            status_code: HTTP status code
            
        Returns:
            tuple of (response_dict, status_code)
        """
        response = ErrorResponse(
            success=False,
            message=message,
            error=ErrorDetail(
                code=error_code,
                details=error_details if error_details is not None else {}
            )
        )
        return response.model_dump(), status_code
    
    @staticmethod
    def created(message: str, data: Any = None) -> tuple:
        """Create a 201 Created response"""
        return APIResponse.success(message, data, 201)
    
    @staticmethod
    def no_content(message: str = "Request successful") -> tuple:
        """Create a 204 No Content response"""
        return APIResponse.success(message, None, 204)
    
    @staticmethod
    def bad_request(message: str, error_code: str = "BAD_REQUEST", error_details: Optional[dict] = None) -> tuple:
        """Create a 400 Bad Request response"""
        return APIResponse.error(message, error_code, error_details, 400)
    
    @staticmethod
    def unauthorized(message: str = "Unauthorized access", error_code: str = "UNAUTHORIZED") -> tuple:
        """Create a 401 Unauthorized response"""
        return APIResponse.error(message, error_code, None, 401)
    
    @staticmethod
    def forbidden(message: str = "Access forbidden", error_code: str = "FORBIDDEN") -> tuple:
        """Create a 403 Forbidden response"""
        return APIResponse.error(message, error_code, None, 403)
    
    @staticmethod
    def not_found(message: str = "Resource not found", error_code: str = "NOT_FOUND") -> tuple:
        """Create a 404 Not Found response"""
        return APIResponse.error(message, error_code, None, 404)
    
    @staticmethod
    def conflict(message: str, error_code: str = "CONFLICT", error_details: Optional[dict] = None) -> tuple:
        """Create a 409 Conflict response"""
        return APIResponse.error(message, error_code, error_details, 409)
    
    @staticmethod
    def validation_error(message: str, error_details: Optional[dict] = None) -> tuple:
        """Create a 422 Validation Error response"""
        return APIResponse.error(message, "VALIDATION_ERROR", error_details, 422)
    
    @staticmethod
    def internal_error(message: str = "Internal server error", error_code: str = "INTERNAL_ERROR") -> tuple:
        """Create a 500 Internal Server Error response"""
        return APIResponse.error(message, error_code, None, 500)
