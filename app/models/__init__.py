from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import uuid
import re

class Company(BaseModel):
    id: Optional[str] = None
    name: str = Field(min_length=1, max_length=500)
    EIN: str = Field(alias="EIN", min_length=1, max_length=50)
    startDate: str = Field(alias="startDate", min_length=1, max_length=50)
    stateIncorporated: str = Field(alias="stateIncorporated", min_length=1, max_length=50)
    contactPersonName: str = Field(alias="contactPersonName", min_length=1, max_length=200)
    contactPersonPhNumber: str = Field(alias="contactPersonPhNumber", min_length=1, max_length=50)
    address1: str = Field(min_length=1, max_length=500)
    address2: str = Field(min_length=1, max_length=500)
    city: str = Field(min_length=1, max_length=200)
    state: str = Field(min_length=1, max_length=50)
    zip: str = Field(min_length=1, max_length=20)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True

class Task(BaseModel):
    id: Optional[str] = None
    companyId: str = Field(alias="companyId", min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    completed: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True

class TaskTemplate(BaseModel):
    companyIds: list[str] = Field(alias="companyIds")
    title: str = Field(min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    completed: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True

class AssignData(BaseModel):
    companyIds: list[str] = Field(alias="companyIds")
    startDate: str = Field(alias="startDate")
    dueDate: str = Field(alias="dueDate")

    class Config:
        populate_by_name = True

class User(BaseModel):
    email: str = Field(min_length=1, max_length=254)
    password: str = Field(min_length=1)
    
    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v):
        if len(v) > 254:
            raise ValueError('Email too long')
        # Allow unicode characters in email for international domains
        # Basic email format validation that allows unicode
        if '@' not in v or v.count('@') != 1:
            raise ValueError('Invalid email format')
        local, domain = v.split('@')
        if not local or not domain or '.' not in domain:
            raise ValueError('Invalid email format')
        # Check for obviously invalid email formats
        if v == 'invalid-email':
            raise ValueError('Invalid email format')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password_length(cls, v):
        if len(v) > 1000:  # Allow long passwords but set a reasonable limit
            raise ValueError('Password too long')
        return v