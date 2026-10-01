import hashlib
import hmac
import secrets


def hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.scrypt(
        password.encode(), salt=salt.encode(), n=16384, r=8, p=1
    ).hex()
    return f"{salt}:{digest}"


def verify_password(password, stored):
    salt, digest = stored.split(":")
    actual = hashlib.scrypt(
        password.encode(), salt=salt.encode(), n=16384, r=8, p=1
    ).hex()
    return hmac.compare_digest(actual, digest)


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()
