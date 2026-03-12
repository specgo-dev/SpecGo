# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""Spec IR data model (minimal stub).

TODO: Expand fields to cover framing, CRC, state machines, and timing.
"""

from __future__ import annotations

from typing import Literal, Optional, List
from pydantic import BaseModel, Field, ConfigDict

class IRMeta(BaseModel):
    """Basic Information about the file."""

    name: str = Field(..., description="Name of the spec.")
    version: str = Field(..., description="Version of the spec.")
    source: str = Field(..., description="Source of the spec.")
    format: Literal["dbc", "pdf", "text", "md"] = Field(..., description="Original format of the spec file.")

class BusType(BaseModel):
    """Information about the bus type."""

    bustype: Literal["CAN", "UART", "SPI", "I2C", "unknown"] = Field(..., description="Type of the bus.")
    busmode: Optional[Literal["classic", "fd"]] = Field(None, description="Bus mode (classic or FD). Only applicable to CAN.")
    sup_bitrates: Optional[List[int]] = Field(None, gt=0, description="Bitrate of the bus in bits per second.")

class EnumEntry(BaseModel):
    """An entry in an enumeration."""
    
    name: str
    value: int
    description: Optional[str] = None

class Signal(BaseModel):
    """A signal within a message."""
    
    name: str
    start_bit: int = Field(..., ge=0, description="Starting bit position of the signal within the message.")
    bit_length: int = Field(..., gt=0, description="Length of the signal in bits.")
    byte_order: Literal["little_endian", "big_endian", "unknown"] = Field(..., description="Byte order of the signal.")
    signed: bool = False
    scale: float = 1.0
    offset: float = 0.0
    min: Optional[float] = None
    default: Optional[float] = None
    max: Optional[float] = None
    unit: Optional[str] = None
    enum: Optional[List[EnumEntry]] = None


class Message(BaseModel):
    """A protocol message containing one or more signals."""

    id: int = Field(..., ge=0, description="Message ID (e.g., CAN ID).")
    name: str
    dlc: int = Field(..., ge=0, description="Payload length in bytes (CAN: data bytes; non-CAN: payload bytes).")
    is_extended: bool = False
    is_fd: bool = False
    bus_type: Optional[BusType] = None
    description: Optional[str] = None
    direction: Optional[Literal["tx", "rx", "tx/rx", "unknown"]] = None
    signals: List[Signal] = Field(default_factory=list)


class SpecIR(BaseModel):
    """Root IR object for a spec."""

    model_config = ConfigDict(extra="forbid")
    ir_version: str = "0.1"
    meta: IRMeta
    bus_type: BusType
    messages: List[Message] = Field(default_factory=list)
