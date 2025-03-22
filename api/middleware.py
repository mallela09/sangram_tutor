import json
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            error_str = str(e).lower()
            logger.error(f"Unhandled exception: {str(e)}")
            
            # Detect common field errors
            if "field required" in error_str or "grade_level" in error_str or "full_name" in error_str:
                # Return a user-friendly error
                json_compatible_response = {
                    "error": "User data error detected and handled",
                    "detail": str(e),
                    "message": "There was an issue with the user data. Please try again."
                }
                return Response(
                    content=json.dumps(json_compatible_response),
                    status_code=500,
                    media_type="application/json"
                )
            # Re-raise the exception if we can't handle it
            raise e