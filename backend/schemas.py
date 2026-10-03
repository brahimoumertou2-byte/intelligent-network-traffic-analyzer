"""API request and response schemas."""
from datetime import datetime
from ipaddress import ip_address
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

def validate_ip(value: str) -> str:
    try: return str(ip_address(value))
    except ValueError as exc: raise ValueError("must be a valid IPv4 or IPv6 address") from exc

class TrafficCreate(BaseModel):
    source_ip: str
    destination_ip: str
    protocol: str = Field(min_length=1, max_length=16)
    source_port: int | None = Field(default=None, ge=0, le=65535)
    destination_port: int | None = Field(default=None, ge=0, le=65535)
    packet_size: int = Field(gt=0, le=65535000)
    timestamp: datetime | None = None
    @field_validator("source_ip", "destination_ip")
    @classmethod
    def valid_ip(cls, value): return validate_ip(value)
    @field_validator("protocol")
    @classmethod
    def protocol_upper(cls, value): return value.strip().upper()

class TrafficRead(TrafficCreate, ORMModel):
    id: int
    timestamp: datetime

class AlertCreate(BaseModel):
    type: str = Field(min_length=1, max_length=80)
    source_ip: str | None = None
    description: str = Field(min_length=1, max_length=2000)
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    status: Literal["open", "acknowledged", "resolved"] = "open"
    timestamp: datetime | None = None
    @field_validator("source_ip")
    @classmethod
    def valid_ip(cls, value): return validate_ip(value) if value else value

class AlertUpdate(BaseModel):
    status: Literal["open", "acknowledged", "resolved"] | None = None
    severity: Literal["low", "medium", "high", "critical"] | None = None
    description: str | None = Field(default=None, min_length=1, max_length=2000)

class AlertRead(AlertCreate, ORMModel):
    id: int
    timestamp: datetime

class DeviceCreate(BaseModel):
    ip_address: str
    hostname: str | None = Field(default=None, max_length=255)
    status: Literal["active", "inactive"] = "active"
    last_seen: datetime | None = None
    @field_validator("ip_address")
    @classmethod
    def valid_ip(cls, value): return validate_ip(value)

class DeviceUpdate(BaseModel):
    hostname: str | None = Field(default=None, max_length=255)
    status: Literal["active", "inactive"] | None = None
    last_seen: datetime | None = None

class DeviceRead(DeviceCreate, ORMModel):
    id: int
