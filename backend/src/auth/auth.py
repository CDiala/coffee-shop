import json
from flask import request, _request_ctx_stack
from functools import wraps
from jose import jwt
from urllib.request import urlopen


AUTH0_DOMAIN = 'marche-du-cafe.us.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'https://cshop_api/'

## AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


## Auth Header
def get_token_auth_header():
    """Obtains the Access Token from the Authorization Header
    """
    auth_header = request.headers.get('Authorization', None)
    if not auth_header:
        raise AuthError({
            'code': 'missing_auth_header',
            'description': 'No header found.'
        }, 401)

    auth_part = auth_header.split(' ')
    if auth_part[0].lower() != 'bearer':
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Wrong header provided.'
        }, 401)

    elif len(auth_part) == 1:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Token not found.'
        }, 401)

    elif len(auth_part) > 2:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must be bearer token.'
        }, 401)

    token = auth_part[1]
    return token

# Check for permission
def check_permissions(permission, payload):
    if 'permissions' not in payload:
        raise AuthError({
            'code': 'invalid_permission',
            'description': 'permission not included'
        }, 400)

    if permission not in payload['permissions']:
        raise AuthError({
            'code': 'forbidden',
            'description': 'Permission not granted.'
        }, 403)

    return True

def check_permissions(permission, payload):
    raise Exception('Not Implemented')


# Verify and decode token and return the payload
def verify_decode_jwt(token):
    # Get data from header
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())

    # Get unverified header
    unverified_header = jwt.get_unverified_header(token)

    rsa_key = {}

    # Check for 'kid' key in unverified header
    if 'kid' not in unverified_header:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization malformed.'
        }, 401)

    # Build rsa_key dict
    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    
    # Verify JWT string's signature and validate reserved claims.
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://' + AUTH0_DOMAIN + '/'
            )
            return payload

        except jwt.ExpiredSignatureError:
            raise AuthError({
                'code': 'token_expired',
                'description': 'Token expired.'
            }, 401)

        except jwt.JWTClaimsError:
            raise AuthError({
                'code': 'invalid_claims',
                'description': 'Incorrect claims. Please check the audience and issuer.'
            }, 401)

        except Exception:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token.'
            }, 400)

    raise AuthError({
        'code': 'invalid_header',
        'description': 'Unable to find the appropriate key.'
    }, 400)


# require_auth decorator
def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            payload = verify_decode_jwt(token)
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)
        return wrapper
    return requires_auth_decorator