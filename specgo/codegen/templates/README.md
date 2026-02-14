<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright (c) 2026 Ce Xu (Dylan) -->

# Templates

Jinja2 templates for code generation.

Current status:
- `c/protocol.h.j2`: Protocol structs, constants, and encode/decode prototypes.
- `c/protocol.c.j2`: Protocol encode/decode implementations (little-endian + big-endian signals).

Planned:
- platform adapter templates
- API wrapper templates
