from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

ph = PasswordHasher()

def hash_password(password: str) -> str:
    return ph.hash(password)

def verify_password(hash_password: str, plain_password: str) -> bool:
    try:
        ph.verify(hash_password, plain_password)
        return True
    except (VerifyMismatchError, InvalidHashError, VerificationError):
        return False