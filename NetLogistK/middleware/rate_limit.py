from redis import Redis
from datetime import datetime
from django.http import HttpResponse

redis_client = Redis(host='localhost', port=6379, db=0)

class TooManyRequestsResponse(HttpResponse):
    status_code = 429

class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        ip = request.META.get('REMOTE_ADDR')
        key = f'rate_limit:{ip}'
        
        # Limitar a 100 requests por minuto
        if redis_client.get(key) and int(redis_client.get(key)) > 100:
            return TooManyRequestsResponse('Demasiadas solicitudes. Por favor, intente más tarde.')
            
        redis_client.incr(key)
        redis_client.expire(key, 60)  # 1 minuto
        
        return self.get_response(request)
