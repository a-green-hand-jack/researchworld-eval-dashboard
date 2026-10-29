#include <stdint.h>
#include <stddef.h>
/* Independent graph streams, xorshift64*; rejection avoids modulo bias. */
static uint64_t next(uint64_t *s) {
    *s ^= *s >> 12; *s ^= *s << 25; *s ^= *s >> 27;
    return *s * UINT64_C(2685821657736338717);
}
static unsigned draw(uint64_t *s, unsigned b) {
    uint64_t r, threshold = (-((uint64_t)b)) % b;
    do { r = next(s); } while (r < threshold);
    return (unsigned)(r % b);
}
void simulate(int n, const int *degree, const int *adj, int trials,
              uint64_t seed, uint64_t *out) {
    uint64_t state = seed ? seed : 1;
    uint32_t full = (UINT32_C(1) << n) - 1;
    for (int i = 0; i < trials; i++) {
        unsigned v = draw(&state, n);
        uint32_t seen = UINT32_C(1) << v;
        uint64_t steps = 0;
        while (seen != full) {
            v = adj[v * n + draw(&state, degree[v])];
            seen |= UINT32_C(1) << v;
            steps++;
        }
        out[i] = steps;
    }
}
