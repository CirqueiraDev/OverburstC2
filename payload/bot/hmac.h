#ifndef HMAC_H
#define HMAC_H

#include <stdint.h>
#include <string.h>

// SHA-256 Implementation
typedef struct {
    uint32_t state[8];
    uint64_t count;
    uint8_t buffer[64];
} sha256_ctx;

void sha256_init(sha256_ctx *ctx);
void sha256_update(sha256_ctx *ctx, const uint8_t *data, size_t len);
void sha256_final(sha256_ctx *ctx, uint8_t *hash);

// HMAC-SHA256 Implementation
void hmac_sha256(const uint8_t *key, size_t key_len,
                 const uint8_t *data, size_t data_len,
                 uint8_t *out);

// Base64 decode helper
int base64_decode(const char *in, uint8_t *out, size_t out_len);

#endif