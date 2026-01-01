from pydantic import BaseModel, Field
from typing import Optional

class LifeDimensions(BaseModel):
    """Data model for the 8 dimensions of the Wheel of Life."""
    career_finance: int = Field(..., ge=1, le=10)
    health_fitness: int = Field(..., ge=1, le=10)
    relationships_family: int = Field(..., ge=1, le=10)
    spirituality_inner_peace: int = Field(..., ge=1, le=10)
    personal_growth_learning: int = Field(..., ge=1, le=10)
    fun_recreation: int = Field(..., ge=1, le=10)
    physical_environment: int = Field(..., ge=1, le=10)
    contribution_legacy: int = Field(..., ge=1, le=10)

class UserChakraInput(BaseModel):
    """The main schema for comparing Current vs Ideal status."""
    user_id: str
    email: str = Field(..., pattern=r"^\S+@\S+\.\S+$")  # Added email with basic regex validation
    age: int
    job_status: str
    current_status: LifeDimensions
    ideal_identity: LifeDimensions
    language: str = "sinhala" # Defaulting to Sinhala as requested