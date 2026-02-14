/*
 * Intentionally broken C source for parser/compile-failure demonstration.
 * This file is synthetic and contains no production logic.
 */

#include <stddef.h>
#include <stdint.h>

int sg_template_broken_encode(uint8_t *payload, size_t payload_len) {
    if (payload == NULL || payload_len == 0) {
        return -1
    }
    return 0;
}

