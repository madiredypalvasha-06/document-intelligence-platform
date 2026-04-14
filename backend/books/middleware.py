"""
Rate limiting middleware for API endpoints.
"""
import time
from collections import defaultdict
from django.http import JsonResponse


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    def is_allowed(self, key: str) -> tuple[bool, int]:
        """Check if request is allowed. Returns (allowed, remaining_requests)."""
        now = time.time()
        window_start = now - self.window_seconds
        
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if req_time > window_start
        ]
        
        if len(self.requests[key]) >= self.max_requests:
            return False, 0
        
        self.requests[key].append(now)
        remaining = self.max_requests - len(self.requests[key])
        return True, remaining
    
    def cleanup(self):
        """Remove old entries to prevent memory leaks."""
        now = time.time()
        window_start = now - self.window_seconds
        for key in list(self.requests.keys()):
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if req_time > window_start
            ]
            if not self.requests[key]:
                del self.requests[key]


rate_limiter = RateLimiter(max_requests=100, window_seconds=60)


class RateLimitMiddleware:
    """Middleware to apply rate limiting to API endpoints."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.path.startswith('/api/'):
            client_ip = self.get_client_ip(request)
            key = f"{client_ip}:{request.path}"
            
            allowed, remaining = rate_limiter.is_allowed(key)
            
            if not allowed:
                return JsonResponse({
                    'error': 'Rate limit exceeded. Please wait before making more requests.',
                    'retry_after': rate_limiter.window_seconds
                }, status=429)
            
            response = self.get_response(request)
            response['X-RateLimit-Limit'] = str(rate_limiter.max_requests)
            response['X-RateLimit-Remaining'] = str(remaining)
            return response
        
        return self.get_response(request)
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')
