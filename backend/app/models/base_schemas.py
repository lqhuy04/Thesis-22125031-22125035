"""
Base response schemas for standardized API responses
"""
from pydantic import BaseModel, Field
from typing import Any, Optional, TypeVar, Generic
from uuid import uuid4


T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """
    Standardized API response format
    
    Fields:
        data: Response payload (can be any type)
        errorCode: 0 for success, non-zero for errors
        errorDesc: Error description (empty string if no error)
        requestId: Unique request identifier for tracking
        result: Boolean indicating success (True) or failure (False)
    """
    data: T = Field(default=None, description="Response data payload")
    errorCode: int = Field(default=0, description="Error code (0 = success)")
    errorDesc: str = Field(default="", description="Error description")
    requestId: str = Field(default_factory=lambda: str(uuid4()), description="Unique request ID")
    result: bool = Field(default=True, description="Success flag")
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": {},
                "errorCode": 0,
                "errorDesc": "",
                "requestId": "123e4567-e89b-12d3-a456-426614174000",
                "result": True
            }
        }


def success_response(data: Any = None, request_id: Optional[str] = None) -> dict:
    """
    Create a successful API response
    
    Args:
        data: Response data
        request_id: Optional request ID (generated if not provided)
        
    Returns:
        Dictionary with standardized success response
    """
    return {
        "data": data if data is not None else {},
        "errorCode": 0,
        "errorDesc": "",
        "requestId": request_id or str(uuid4()),
        "result": True
    }


def error_response(
    error_code: int,
    error_desc: str,
    data: Any = None,
    request_id: Optional[str] = None
) -> dict:
    """
    Create an error API response
    
    Args:
        error_code: Error code (non-zero)
        error_desc: Error description
        data: Optional error data
        request_id: Optional request ID (generated if not provided)
        
    Returns:
        Dictionary with standardized error response
    """
    return {
        "data": data if data is not None else {},
        "errorCode": error_code,
        "errorDesc": error_desc,
        "requestId": request_id or str(uuid4()),
        "result": False
    }
