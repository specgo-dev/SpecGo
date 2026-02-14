/* Intentionally mismatched encode/decode demo artifact for roundtrip failure tests. */
#ifndef SPECGO_TEMPLATE_ROUNDTRIP_MISMATCH_SANITIZED_PROTOCOL_H
#define SPECGO_TEMPLATE_ROUNDTRIP_MISMATCH_SANITIZED_PROTOCOL_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    SPECGO_OK = 0,
    SPECGO_ERR_NULL = -1,
    SPECGO_ERR_SIZE = -2,
    SPECGO_ERR_RANGE = -3
} specgo_status_t;

enum {
    SPECGO_TEMPLATE_ROUNDTRIP_MISMATCH_SANITIZED_SG_TEMPLATE_ROUNDTRIP_MISMATCH_MSG_ID = 258
};

enum {
    SPECGO_TEMPLATE_ROUNDTRIP_MISMATCH_SANITIZED_SG_TEMPLATE_ROUNDTRIP_MISMATCH_MSG_DLC = 1
};

typedef struct {
    uint64_t counter;
    uint64_t mode;
} template_roundtrip_mismatch_sanitized_sg_template_roundtrip_mismatch_msg_t;

int template_roundtrip_mismatch_sanitized_encode_sg_template_roundtrip_mismatch_msg(
    uint8_t *out_payload,
    size_t out_size,
    const template_roundtrip_mismatch_sanitized_sg_template_roundtrip_mismatch_msg_t *in
);

int template_roundtrip_mismatch_sanitized_decode_sg_template_roundtrip_mismatch_msg(
    const uint8_t *payload,
    size_t payload_size,
    template_roundtrip_mismatch_sanitized_sg_template_roundtrip_mismatch_msg_t *out
);

#ifdef __cplusplus
}
#endif

#endif /* SPECGO_TEMPLATE_ROUNDTRIP_MISMATCH_SANITIZED_PROTOCOL_H */

