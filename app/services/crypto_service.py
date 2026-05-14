import os
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, AESCCM
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend

class CryptoService:
    RSA_KEY_SIZE = 2048
    RSA_PUBLIC_EXPONENT = 65537

    @staticmethod
    def generate_rsa_keypair():
        private_key = rsa.generate_private_key(
            public_exponent=CryptoService.RSA_PUBLIC_EXPONENT,
            key_size=CryptoService.RSA_KEY_SIZE,
            backend=default_backend()
        )
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        return private_pem, public_pem

    @staticmethod
    def encrypt_private_key(private_key_pem, master_key):
        f = Fernet(master_key)
        encrypted = f.encrypt(private_key_pem.encode('utf-8'))
        return base64.b64encode(encrypted).decode('utf-8')

    @staticmethod
    def decrypt_private_key(encrypted_private_key_b64, master_key):
        f = Fernet(master_key)
        encrypted = base64.b64decode(encrypted_private_key_b64.encode('utf-8'))
        decrypted = f.decrypt(encrypted)
        return decrypted.decode('utf-8')

    @staticmethod
    def encrypt_symmetric_key(symmetric_key, public_key_pem):
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode('utf-8'),
            backend=default_backend()
        )
        encrypted = public_key.encrypt(
            symmetric_key,
            asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return base64.b64encode(encrypted).decode('utf-8')

    @staticmethod
    def decrypt_symmetric_key(encrypted_key_b64, private_key_pem):
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode('utf-8'),
            password=None,
            backend=default_backend()
        )
        encrypted = base64.b64decode(encrypted_key_b64.encode('utf-8'))
        decrypted = private_key.decrypt(
            encrypted,
            asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return decrypted

    @staticmethod
    def generate_file_encryption_key(algorithm='fernet'):
        if algorithm == 'fernet':
            key = Fernet.generate_key()
            return key, None, 'fernet'
        elif algorithm == 'aes-gcm':
            key = AESGCM.generate_key(bit_length=256)
            nonce = os.urandom(12)
            return key, nonce, 'aes-gcm'
        elif algorithm == 'aes-ccm':
            key = AESCCM.generate_key(bit_length=256)
            nonce = os.urandom(13)
            return key, nonce, 'aes-ccm'
        else:
            key = Fernet.generate_key()
            return key, None, 'fernet'

    @staticmethod
    def encrypt_file_data(file_data, key, nonce=None, algorithm='fernet'):
        if algorithm == 'fernet':
            f = Fernet(key)
            return f.encrypt(file_data)
        elif algorithm == 'aes-gcm':
            aesgcm = AESGCM(key)
            encrypted = aesgcm.encrypt(nonce, file_data, None)
            return nonce + encrypted
        elif algorithm == 'aes-ccm':
            aesccm = AESCCM(key)
            encrypted = aesccm.encrypt(nonce, file_data, None)
            return nonce + encrypted
        else:
            f = Fernet(key)
            return f.encrypt(file_data)

    @staticmethod
    def decrypt_file_data(encrypted_data, key, algorithm='fernet'):
        if algorithm == 'fernet':
            f = Fernet(key)
            return f.decrypt(encrypted_data)
        elif algorithm == 'aes-gcm':
            nonce = encrypted_data[:12]
            ciphertext = encrypted_data[12:]
            aesgcm = AESGCM(key)
            return aesgcm.decrypt(nonce, ciphertext, None)
        elif algorithm == 'aes-ccm':
            nonce = encrypted_data[:13]
            ciphertext = encrypted_data[13:]
            aesccm = AESCCM(key)
            return aesccm.decrypt(nonce, ciphertext, None)
        else:
            f = Fernet(key)
            return f.decrypt(encrypted_data)