from functools import wraps
from firebase_admin import auth
from django.http import HttpResponseForbidden

def verify_firebase_token(f):
    @wraps(f)
    def decorated_function(request, *args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return HttpResponseForbidden()
            
        try:
            decoded_token = auth.verify_id_token(token)
            request.user_id = decoded_token['uid']
        except:
            return HttpResponseForbidden()
            
        return f(request, *args, **kwargs)
    return decorated_function
