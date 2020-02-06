import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


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
    return f.encrypt(string)

def decryptString(password, salt, resKey, string):

    masterKey = decryptMasterKey(password, salt, resKey)
    f = Fernet(masterKey)
    return f.decrypt(string)


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
