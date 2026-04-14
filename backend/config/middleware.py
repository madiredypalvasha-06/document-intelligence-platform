"""
Custom middleware for CORS OPTIONS handling.
"""
from django.http import HttpResponse


class CorsOptionsMiddleware:
    """
    Middleware to handle CORS preflight OPTIONS requests.
    This ensures the server responds correctly to OPTIONS requests for CORS.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == 'OPTIONS':
            response = HttpResponse()
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Accept, Authorization, X-Requested-With, Origin, Cache-Control'
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Max-Age'] = '86400'
            return response
        return self.get_response(request)
