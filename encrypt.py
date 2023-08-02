from passlib.context import CryptContext

#Declares the settings for encryption#
pwd_context = CryptContext(
        schemes=["pbkdf2_sha256"],
        default="pbkdf2_sha256",
        pbkdf2_sha256__default_rounds=30000
)

#Encrypts password
def encrypt_password(password):
  return pwd_context.encrypt(password)

#Compares encrypted password attempt to encrypted password, and returns whether it matches in BOOL
def verify_password(password, hashed):
  return pwd_context.verify(password, hashed)