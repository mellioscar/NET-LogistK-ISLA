import redis
import json
from functools import wraps
from django.core.cache import cache
from django.conf import settings

# Intentar usar Redis si está configurado, si no, usar la caché por defecto de Django
try:
    if hasattr(settings, 'REDIS_CONFIG') and settings.REDIS_CONFIG.get('host'):
        redis_client = redis.Redis(**settings.REDIS_CONFIG)
        USE_REDIS = True
    else:
        USE_REDIS = False
except:
    USE_REDIS = False

def cache_decorator(timeout=300):
    def decorator(f):
        @wraps(f)
        async def decorated_function(*args, **kwargs):
            key = f"{f.__name__}:{str(args)}:{str(kwargs)}"
            
            if USE_REDIS:
                try:
                    result = redis_client.get(key)
                    if result is not None:
                        return json.loads(result)
                except:
                    pass
            else:
                result = cache.get(key)
                if result is not None:
                    return result
            
            result = await f(*args, **kwargs)
            
            try:
                if USE_REDIS:
                    redis_client.setex(key, timeout, json.dumps(result))
                else:
                    cache.set(key, result, timeout)
            except:
                pass
                
            return result
        return decorated_function
    return decorator
