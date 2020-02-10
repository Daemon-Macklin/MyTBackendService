import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def generateResKey(password, salt):

    kdf = passwordEncryptionSettings(salt)
    passwordKey = base64.urlsafe_b64encode(kdf.derive(str.encode(password)))
    masterKey = Fernet.generate_key()
    f = Fernet(passwordKey)
    resKey = f.encrypt(masterKey)
    return resKey


def decryptMasterKey(password, salt, resKey):

    kdf = passwordEncryptionSettings(salt)
    passwordKey = base64.urlsafe_b64encode(kdf.derive(str.encode(password)))
    f = Fernet(passwordKey)
    masterKey = f.decrypt(resKey)
    return masterKey

def encryptString(password, salt, resKey, string):

    masterKey = decryptMasterKey(password, salt, resKey)
    f = Fernet(masterKey)
    return f.encrypt(str.encode(string))

def decryptString(password, salt, resKey, string):

    masterKey = decryptMasterKey(password, salt, resKey)
    f = Fernet(masterKey)
    return str(f.decrypt(string), 'utf-8')


def passwordEncryptionSettings(salt):

    backend = default_backend()

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=backend
    )

    return kdf


def generateSSHKey():
    key = rsa.generate_private_key(
        backend=default_backend(),
        public_exponent=65537,
        key_size=2048
    )

    private_key = key.private_bytes(
        crypto_serialization.Encoding.PEM,
        crypto_serialization.PrivateFormat.PKCS8,
        crypto_serialization.NoEncryption())

    public_key = key.public_key().public_bytes(
        crypto_serialization.Encoding.OpenSSH,
        crypto_serialization.PublicFormat.OpenSSH
    )

    return str(private_key, 'utf-8'), str(public_key, 'utf-8')
