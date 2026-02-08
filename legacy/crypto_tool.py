from cryptography.fernet import Fernet

def fernet_create_key() -> bytes:
    key = Fernet.generate_key()
    return key 

def fernet_encrypt(key: bytes, input: str, encoding: str='utf-8') -> str:
    cipher_suite = Fernet(key)
    encrypted = cipher_suite.encrypt(input.encode())
    output = encrypted.decode(encoding)
    return output

def fernet_decrypt(key: bytes, input: str, encoding: str='utf-8') -> str:
    cipher_suite = Fernet(key)
    decrypted = cipher_suite.decrypt(input.encode())
    output = decrypted.decode(encoding)
    return output