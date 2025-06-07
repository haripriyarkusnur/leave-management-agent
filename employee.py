from pydantic import BaseModel, EmailStr
from typing import Optional

class Employee(BaseModel):
    emp_id: str
    emp_name: str
    role: str
    dept: str
    date_of_joining: str  # keep as string in the API
    total_leaves: int = 12
    applied_leaves: int
    status: str
    email: EmailStr  # Add email field with validation
    is_on_probation: bool = False  # Add probation status
