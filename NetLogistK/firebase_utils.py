from firebase_admin import auth
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def verificar_y_renovar_token(token):
    try:
        # Verificar el token actual
        decoded_token = auth.verify_id_token(token)
        exp_timestamp = decoded_token.get('exp', 0)
        
        # Si el token expirará en menos de 1 hora, renovarlo
        if datetime.fromtimestamp(exp_timestamp) - datetime.now() < timedelta(hours=1):
            nuevo_token = auth.create_custom_token(decoded_token['uid'])
            logger.debug("Token renovado preventivamente")
            return nuevo_token
            
        return token
        
    except auth.ExpiredIdTokenError:
        try:
            # Renovar token expirado
            decoded_token = auth.verify_id_token(token, check_revoked=False)
            nuevo_token = auth.create_custom_token(decoded_token['uid'])
            logger.debug("Token expirado renovado exitosamente")
            return nuevo_token
        except Exception as e:
            logger.error(f"Error al renovar token: {e}")
            raise 