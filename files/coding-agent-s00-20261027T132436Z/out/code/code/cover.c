/* Monte Carlo cover-time estimator for simple random walks.
 * Input (stdin): n m, then m lines "u v" (0-indexed), then R and seed.
 * Output: one line per start vertex: start mean_cover sd_cover.
 * Usage: ./cover < graph.txt */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

static unsigned long long s[2];
static inline unsigned long long next(void) {
    unsigned long long s1 = s[0];
    const unsigned long long s0 = s[1];
    s[0] = s0;
    s1 ^= s1 << 23;
    s[1] = s1 ^ s0 ^ (s1 >> 17) ^ (s0 >> 26);
    return s[1] + s0;
}

int main(void) {
    int n, m;
    if (scanf("%d %d", &n, &m) != 2) return 1;
    int *eu = malloc(sizeof(int) * m), *ev = malloc(sizeof(int) * m);
    int *deg = calloc(n, sizeof(int));
    for (int i = 0; i < m; i++) {
        if (scanf("%d %d", &eu[i], &ev[i]) != 2) return 1;
        deg[eu[i]]++; deg[ev[i]]++;
    }
    int R;
    unsigned long long seed;
    if (scanf("%d %llu", &R, &seed) != 2) return 1;
    int **adj = malloc(sizeof(int *) * n);
    int *fill = calloc(n, sizeof(int));
    for (int i = 0; i < n; i++) adj[i] = malloc(sizeof(int) * (deg[i] > 0 ? deg[i] : 1));
    for (int i = 0; i < m; i++) {
        adj[eu[i]][fill[eu[i]]++] = ev[i];
        adj[ev[i]][fill[ev[i]]++] = eu[i];
    }
    s[0] = seed * 0x9E3779B97F4A7C15ULL + 1; s[1] = seed ^ 0xDEADBEEFCAFEULL;
    for (int i = 0; i < 20; i++) next();
    char *vis = malloc(n);
    for (int st = 0; st < n; st++) {
        double sum = 0, sum2 = 0;
        for (int r = 0; r < R; r++) {
            memset(vis, 0, n);
            int v = st, seen = 1; long long steps = 0;
            vis[v] = 1;
            while (seen < n) {
                int d = deg[v];
                v = adj[v][next() % d];
                steps++;
                if (!vis[v]) { vis[v] = 1; seen++; }
            }
            sum += steps; sum2 += (double)steps * steps;
        }
        double mean = sum / R;
        double var = (sum2 / R - mean * mean) * R / (R - 1.0);
        printf("%d %.6f %.6f\n", st, mean, sqrt(var));
    }
    return 0;
}
