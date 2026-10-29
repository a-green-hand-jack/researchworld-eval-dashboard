#include <stdint.h>

/* xorshift64*: nonzero state; rejection sampling avoids modulo bias. */
static uint64_t next_u64(uint64_t *state) {
    uint64_t x = *state;
    x ^= x >> 12; x ^= x << 25; x ^= x >> 27;
    *state = x;
    return x * UINT64_C(2685821657736338717);
}
static uint32_t bounded(uint64_t *state, uint32_t bound) {
    uint64_t threshold = (uint64_t)(-((uint64_t)bound)) % bound;
    uint64_t x;
    do { x = next_u64(state); } while (x < threshold);
    return (uint32_t)(x % bound);
}
void simulate(int n, const int *offset, const int *neighbors,
              int repetitions, uint64_t seed, uint64_t *out) {
    uint64_t state = seed ? seed : 1;
    uint32_t full = (UINT32_C(1) << n) - 1;
    for (int r = 0; r < repetitions; ++r) {
        int v = (int)bounded(&state, (uint32_t)n);
        uint32_t seen = UINT32_C(1) << v;
        uint64_t steps = 0;
        while (seen != full) {
            v = neighbors[offset[v] + bounded(&state, offset[v+1]-offset[v])];
            seen |= UINT32_C(1) << v;
            ++steps;
        }
        out[r] = steps;
    }
}
