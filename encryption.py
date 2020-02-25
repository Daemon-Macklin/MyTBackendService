import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa

# Function to generate the result key
def generateResKey(password, salt):

    # Set up the key derivation function
    kdf = passwordEncryptionSettings(salt)

    # Generate the password key based on the password
    passwordKey = base64.urlsafe_b64encode(kdf.derive(str.encode(password)))

    # Randomly generate a key to use to encrypt user data
    masterKey = Fernet.generate_key()

    # Setup Fernet with the password key
    f = Fernet(passwordKey)

    # Encrypt the master key with the password key
    resKey = f.encrypt(masterKey)

    # Return the result key for storage
    return resKey

# Function to decrypt the master key
def decryptMasterKey(password, salt, resKey):

    # Set up the key derivation function
    kdf = passwordEncryptionSettings(salt)

    # Generate the password key based on the password
    passwordKey = base64.urlsafe_b64encode(kdf.derive(str.encode(password)))

    # Setup Fernet with the password key
    f = Fernet(passwordKey)

    # Decrypt the master key with the password key
    masterKey = f.decrypt(resKey)

    # Return the master key
    return masterKey

# Function to encrypt a string
def encryptString(password, salt, resKey, string):

    # Get the master key
    masterKey = decryptMasterKey(password, salt, resKey)

    # Setup Fernet with the master key
    f = Fernet(masterKey)

    # Return the encrypted String
    return f.encrypt(str.encode(string))

# Function to decrypt a string
def decryptString(password, salt, resKey, string):

    # Try to encode the data to a string - This is done only if the data is bytes
    try:
        string = str.encode(string)
    except TypeError:
        pass

    # Get the master key
    masterKey = decryptMasterKey(password, salt, resKey)

    # Setup Fernet with the master key
    f = Fernet(masterKey)

    # Return the decrypted string
    return str(f.decrypt(string), 'utf-8')

# Key Derivation settings
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

# Function to generate ssh key
def generateSSHKey():

    # Generate the key
    key = rsa.generate_private_key(
        backend=default_backend(),
        public_exponent=65537,
        key_size=2048
    )

    # Get the private key
    private_key = key.private_bytes(
        crypto_serialization.Encoding.PEM,
        crypto_serialization.PrivateFormat.PKCS8,
        crypto_serialization.NoEncryption())

    # Get the public key
    public_key = key.public_key().public_bytes(
        crypto_serialization.Encoding.OpenSSH,
        crypto_serialization.PublicFormat.OpenSSH
    )

    # Return the public and private keys as strings
    return str(private_key, 'utf-8'), str(public_key, 'utf-8')
