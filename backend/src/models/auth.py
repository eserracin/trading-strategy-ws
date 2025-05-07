# src/models/auth.py
from pydantic import BaseModel, Field

class AuthenticationEntity(BaseModel):
    username: str = Field(None, description="Username for the user")
    email: str = Field(None, description="Email for the user")
    password: str = Field(None, description="Password for the user")
    test: bool = Field(False, description="Test mode flag")
