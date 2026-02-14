# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Ce Xu (Dylan)
"""Layer 1: Semantic validation for SpecIR.

Checks cross-field constraints that Pydantic field-level validation cannot enforce:
- Signal bit range fits within message DLC
- No overlapping signal bits within a message
- Default value within [min, max] range
- Enum entry values fit within signal bit_length (signed or unsigned)
- Scale must not be zero
- min must be less than max when both are set
"""

from __future__ import annotations

from specgo.ir.model import Message, Signal, SpecIR


def _signal_bits(sig: Signal) -> set[int]:
    """Compute the set of bit positions occupied by a signal.

    Little-endian (Intel): start_bit is the LSB, bits are contiguous upward.
    Big-endian (Motorola): start_bit is the MSB, bits are laid out across
    bytes in CAN bit numbering (MSB bit within each byte counted 7..0,
    bytes numbered 0,1,2,...).
    """
    if sig.byte_order == "little_endian":
        return set(range(sig.start_bit, sig.start_bit + sig.bit_length))

    if sig.byte_order == "big_endian":
        bits: set[int] = set()
        bit_pos = sig.start_bit
        for _ in range(sig.bit_length):
            bits.add(bit_pos)
            # Move to next bit in Motorola layout:
            # If at bit 0 of current byte, jump to bit 7 of next byte
            if bit_pos % 8 == 0:
                bit_pos += 15  # end of current byte row -> bit 7 of next byte
            else:
                bit_pos -= 1
        return bits

    # Unknown byte order — fall back to contiguous range (best effort)
    return set(range(sig.start_bit, sig.start_bit + sig.bit_length))


def _check_signal_fits_dlc(sig: Signal, msg: Message) -> list[str]:
    """Check that all signal bits are non-negative and fit within dlc * 8."""
    errors = []
    dlc_bits = msg.dlc * 8
    occupied = _signal_bits(sig)
    min_bit = min(occupied)
    max_bit = max(occupied)
    if min_bit < 0:
        errors.append(
            f"[semantic] Message '{msg.name}' (ID {msg.id}), signal '{sig.name}': "
            f"bit position {min_bit} is negative"
        )
    if max_bit >= dlc_bits:
        errors.append(
            f"[semantic] Message '{msg.name}' (ID {msg.id}), signal '{sig.name}': "
            f"bit {max_bit} exceeds DLC ({msg.dlc} bytes = {dlc_bits} bits)"
        )
    return errors


def _check_signal_bit_overlaps(msg: Message) -> list[str]:
    """Check for overlapping signal bit ranges within a message."""
    errors = []
    occupied: list[tuple[str, set[int]]] = []
    for sig in msg.signals:
        bits = _signal_bits(sig)
        for prev_name, prev_bits in occupied:
            overlap = bits & prev_bits
            if overlap:
                errors.append(
                    f"[semantic] Message '{msg.name}' (ID {msg.id}): "
                    f"signal '{sig.name}' overlaps with signal '{prev_name}' "
                    f"at bit(s) {sorted(overlap)}"
                )
        occupied.append((sig.name, bits))
    return errors


def _check_default_in_range(sig: Signal, msg_name: str, msg_id: int) -> list[str]:
    """Check that default value is within [min, max] if set."""
    errors = []
    if sig.default is None:
        return errors
    if sig.min is not None and sig.default < sig.min:
        errors.append(
            f"[semantic] Message '{msg_name}' (ID {msg_id}), signal '{sig.name}': "
            f"default ({sig.default}) is less than min ({sig.min})"
        )
    if sig.max is not None and sig.default > sig.max:
        errors.append(
            f"[semantic] Message '{msg_name}' (ID {msg_id}), signal '{sig.name}': "
            f"default ({sig.default}) is greater than max ({sig.max})"
        )
    return errors


def _check_scale_not_zero(sig: Signal, msg_name: str, msg_id: int) -> list[str]:
    """Check that scale is not zero."""
    if sig.scale == 0:
        return [
            f"[semantic] Message '{msg_name}' (ID {msg_id}), signal '{sig.name}': "
            f"scale is 0"
        ]
    return []


def _check_min_less_than_max(sig: Signal, msg_name: str, msg_id: int) -> list[str]:
    """Check that min < max when both are set."""
    if sig.min is not None and sig.max is not None and sig.min >= sig.max:
        return [
            f"[semantic] Message '{msg_name}' (ID {msg_id}), signal '{sig.name}': "
            f"min ({sig.min}) is not less than max ({sig.max})"
        ]
    return []


def _check_enum_values(sig: Signal, msg_name: str, msg_id: int) -> list[str]:
    """Check that enum entry values fit within bit_length range.

    Signed signals: valid range is [-(2^(n-1)), 2^(n-1) - 1]
    Unsigned signals: valid range is [0, 2^n - 1]
    """
    errors = []
    if sig.enum is None:
        return errors
    if sig.signed:
        min_val = -(1 << (sig.bit_length - 1))
        max_val = (1 << (sig.bit_length - 1)) - 1
    else:
        min_val = 0
        max_val = (1 << sig.bit_length) - 1
    for entry in sig.enum:
        if entry.value < min_val:
            errors.append(
                f"[semantic] Message '{msg_name}' (ID {msg_id}), signal '{sig.name}', "
                f"enum '{entry.name}': value ({entry.value}) below min for "
                f"{sig.bit_length}-bit {'signed' if sig.signed else 'unsigned'} signal ({min_val})"
            )
        if entry.value > max_val:
            errors.append(
                f"[semantic] Message '{msg_name}' (ID {msg_id}), signal '{sig.name}', "
                f"enum '{entry.name}': value ({entry.value}) exceeds max for "
                f"{sig.bit_length}-bit {'signed' if sig.signed else 'unsigned'} signal ({max_val})"
            )
    return errors


def validate_semantic(spec: SpecIR) -> list[str]:
    """Run all Layer 1 semantic checks on a SpecIR instance.

    Returns a list of error strings. Empty list means all checks passed.
    """
    errors: list[str] = []

    for msg in spec.messages:
        errors.extend(_check_signal_bit_overlaps(msg))
        for sig in msg.signals:
            errors.extend(_check_signal_fits_dlc(sig, msg))
            errors.extend(_check_scale_not_zero(sig, msg.name, msg.id))
            errors.extend(_check_min_less_than_max(sig, msg.name, msg.id))
            errors.extend(_check_default_in_range(sig, msg.name, msg.id))
            errors.extend(_check_enum_values(sig, msg.name, msg.id))

    return errors
