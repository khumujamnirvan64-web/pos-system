import secrets

def generate_refresh_token():
    return secrets.token_urlsafe(32)