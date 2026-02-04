"""
Security middleware for FastAPI integration
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

from .integration import secure_config_service

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle security checks for all API requests
    """
    
    def __init__(self, app, excluded_paths: list = None):
        """
        Initialize security middleware
        
        Args:
            app: FastAPI application
            excluded_paths: List of paths to exclude from security checks
        """
        super().__init__(app)
        self.excluded_paths = excluded_paths or ["/health", "/docs", "/openapi.json"]
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request through security checks
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain
            
        Returns:
            Response from next handler or security error response
        """
        # Skip security checks for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)
        
        # Extract client information
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        endpoint = request.url.path
        
        # Validate access
        try:
            if not secure_config_service.validate_request_access(client_ip, user_agent, endpoint):
                logger.warning(f"Access denied for {client_ip} to {endpoint}")
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": "Access denied",
                        "message": "Your request has been blocked due to security policies"
                    }
                )
        except Exception as e:
            logger.error(f"Security validation error: {e}")
            # In case of security system failure, allow request but log the error
            # In production, you might want to be more restrictive
        
        # Process request
        response = await call_next(request)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address from request
        
        Args:
            request: FastAPI request object
            
        Returns:
            Client IP address
        """
        # Check for forwarded headers (when behind proxy/load balancer)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"


def create_security_exception_handler():
    """
    Create exception handler for security-related errors
    
    Returns:
        Exception handler function
    """
    async def security_exception_handler(request: Request, exc: HTTPException):
        """Handle security exceptions"""
        if exc.status_code == 403:
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Security violation",
                    "message": "Access denied due to security policy",
                    "timestamp": str(request.state.timestamp) if hasattr(request.state, 'timestamp') else None
                }
            )
        
        # For other HTTP exceptions, return default handling
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail}
        )
    
    return security_exception_handler