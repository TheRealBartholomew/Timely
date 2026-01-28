from datetime import datetime
import hashlib
import os
from pydantic import BaseModel, validator, EmailStr
from typing import Optional

class User(BaseModel):
    user_id: str
    email: EmailStr
    hash_password: str
    chronotype: str
    created_at: datetime = datetime.now()

    @validator('chronotype')
    def validate_chronotype(cls, v):
        # Update to match HTML form options
        valid_chronotypes = ['Early', 'Middle', 'Late']
        if v not in valid_chronotypes:
            raise ValueError(f'Chronotype must be one of {valid_chronotypes}')
        return v

    @staticmethod
    def hashedpassword(password:str, salt: bytes = None) -> str:
        if salt is None:
            salt = os.urandom(16)
        salted = salt + password.encode('utf-8')
        hash_result = hashlib.sha256(salted).hexdigest()
        return salt.hex() + ':' + hash_result

    @staticmethod
    def verify_password(stored_password: str, stored_credential: str) -> bool:
        try:
            parts = stored_credential.split(':')
            salt = bytes.fromhex(parts[0])
            stored_hash = parts[1]
            computed_hash = User.hashedpassword(stored_password, salt).split(':')[1]
            return computed_hash == stored_hash
        except ValueError as e:
            # Re-raise validation errors - these indicate data corruption
            print(f"Password verification error: {str(e)}")  # Log for debugging
            raise
        except Exception as e:
            # Catch unexpected errors but log them
            print(f"Unexpected error during password verification: {str(e)}")
            # For development: raise the error to see what went wrong
            raise
            # For production: you might return False here instead