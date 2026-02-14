/* Intentionally mismatched encode/decode demo artifact for roundtrip failure tests. */
#include "template_roundtrip_mismatch_sanitized_protocol.h"

#include <string.h>

int template_roundtrip_mismatch_sanitized_encode_sg_template_roundtrip_mismatch_msg(
    uint8_t *out_payload,
    size_t out_size,
    const template_roundtrip_mismatch_sanitized_sg_template_roundtrip_mismatch_msg_t *in
) {
    if (out_payload == NULL || in == NULL) {
        return SPECGO_ERR_NULL;
    }
    if (out_size < SPECGO_TEMPLATE_ROUNDTRIP_MISMATCH_SANITIZED_SG_TEMPLATE_ROUNDTRIP_MISMATCH_MSG_DLC) {
        return SPECGO_ERR_SIZE;
    }
    if (in->counter > 15U || in->mode > 15U) {
        return SPECGO_ERR_RANGE;
    }

    memset(out_payload, 0, SPECGO_TEMPLATE_ROUNDTRIP_MISMATCH_SANITIZED_SG_TEMPLATE_ROUNDTRIP_MISMATCH_MSG_DLC);
    out_payload[0] = (uint8_t)((in->counter & 0x0FU) | ((in->mode & 0x0FU) << 4U));
    return SPECGO_OK;
}

int template_roundtrip_mismatch_sanitized_decode_sg_template_roundtrip_mismatch_msg(
    const uint8_t *payload,
    size_t payload_size,
    template_roundtrip_mismatch_sanitized_sg_template_roundtrip_mismatch_msg_t *out
) {
    uint8_t counter_raw;
    if (payload == NULL || out == NULL) {
        return SPECGO_ERR_NULL;
    }
    if (payload_size < SPECGO_TEMPLATE_ROUNDTRIP_MISMATCH_SANITIZED_SG_TEMPLATE_ROUNDTRIP_MISMATCH_MSG_DLC) {
        return SPECGO_ERR_SIZE;
    }

    memset(out, 0, sizeof(*out));
    counter_raw = (uint8_t)(payload[0] & 0x0FU);
    /* Intentional bug: +1 introduces encode/decode inconsistency. */
    out->counter = (uint64_t)((counter_raw + 1U) & 0x0FU);
    out->mode = (uint64_t)((payload[0] >> 4U) & 0x0FU);
    return SPECGO_OK;
}

