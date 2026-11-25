/* ======== START: HEADER ========
 * s7t_kernels_x86.c — S7t (DESIGN_S7T.md): memo eksak SNN-AE untuk T time step sembarang (1 <= T <= 8), x86 AVX2.
 * Diturunkan dari s7x_ij_kernels_x86.c (snn_memo_v3) tanpa mengubah urutan operasi float:
 *   - encode/snn_miss: loop time step 3 -> T; mask[3] -> mask[T];
 *   - kunci cache: T kata 32-bit + 1 kata valid (stride KW = 9 kata per slot);
 *   - hash: untuk T = 3 identik dengan slot_of() v3; untuk T lain, xor-perkalian dengan konstanta per kata.
 * Wajib bit-identik dengan snn_ae (s7c_native_copy.c, mode 2 = count) pada setiap T (gerbang G2).
 * snn_keys_t: hanya encoder, mengekspor mask[T] per sampel untuk statistik pola (Q1).
 * Kompilasi: gcc -O3 -march=native -shared -fPIC (= S7x-ij).
 * ======== END: HEADER ======== */
#include <stdint.h>
#include <string.h>
#include <immintrin.h>

#define MAXD 64
#define MAXT 8
#define KW (MAXT + 1)
#define FMA8(c, u, k) _mm256_fmadd_ps((k), (u), (c))        /* = k*u + c terfusi (gcc -ffp-contract=fast) */

static const uint32_t HC[MAXT] = {0x9E3779B1u, 0x85EBCA77u, 0xC2B2AE3Du, 0x27D4EB2Fu,
                                  0x165667B1u, 0xD3A2646Cu, 0xFD7046C5u, 0xB55A4F09u};

static inline uint32_t slot_of_t(const uint32_t *m, int T, int logcap)
{
    uint32_t h = 0;
    for (int t = 0; t < T; t++) h ^= m[t] * HC[t];
    h ^= h >> 15;
    h *= 0x2C1B3C6Du;
    h ^= h >> 12;
    return logcap ? h >> (32 - logcap) : 0;
}

/* acc[0..n) += a * w[0..n), fma terfusi per elemen (sama dengan kode skalar yang dikontraksi gcc) */
static inline void axpy_fma(float *acc, float a, const float *w, int n)
{
    const __m256 va = _mm256_set1_ps(a);
    int j = 0;
    for (; j + 8 <= n; j += 8)
        _mm256_storeu_ps(acc + j, FMA8(_mm256_loadu_ps(acc + j), _mm256_loadu_ps(w + j), va));
    for (; j < n; j++) acc[j] = __builtin_fmaf(a, w[j], acc[j]);
}

/* ce = be + x*We (= v3), lalu LIF encoder AVX2 T time step -> mask[T]; mengembalikan jumlah spike */
static inline int64_t encode(const float *x, int din, const float *We, const float *be, __m256 vdk, __m256 vth,
                             int T, uint32_t *mask)
{
    float ce[32] __attribute__((aligned(32))), me[32] __attribute__((aligned(32)));
    memcpy(ce, be, 32 * sizeof(float));
    for (int i = 0; i < din; i++) {
        const float a = x[i], *w = We + (size_t)i * 32;
        for (int j = 0; j < 32; j++) ce[j] += a * w[j];
    }
    memset(me, 0, sizeof me);
    int64_t pop = 0;
    for (int t = 0; t < T; t++) {
        uint32_t m = 0;
        for (int q = 0; q < 4; q++) {
            __m256 u = _mm256_load_ps(me + 8 * q), c = _mm256_load_ps(ce + 8 * q);
            __m256 v = FMA8(c, u, vdk);
            __m256 sp = _mm256_cmp_ps(v, vth, _CMP_GT_OQ);
            _mm256_store_ps(me + 8 * q, _mm256_blendv_ps(v, _mm256_sub_ps(v, vth), sp));
            m |= (uint32_t)_mm256_movemask_ps(sp) << (8 * q);
        }
        mask[t] = m;
        pop += __builtin_popcount(m);
    }
    return pop;
}

/* jalur miss SNN v3: dekoder (mask[3]) + keluaran -> y; urutan float per elemen = snn_memo (s7f) */
static inline void snn_miss_t(const uint32_t *mask, int T, int dout, const float *Wd, const float *bd, __m256 vdkd,
                               __m256 vthd, const float *Wo, const float *bo, float invT, float *y, int64_t *stats)
{
    float md[32] __attribute__((aligned(32)));
    int32_t cnt[32] __attribute__((aligned(32)));
    float acc[MAXD], yv[MAXD];
    memset(md, 0, sizeof md); memset(cnt, 0, sizeof cnt); memset(acc, 0, sizeof acc);
    for (int t = 0; t < T; t++) {
        __m256 c8[4];
        for (int q = 0; q < 4; q++) c8[q] = _mm256_loadu_ps(bd + 8 * q);
        for (uint32_t m = mask[t]; m; m &= m - 1) {        /* urutan baris (ctz) sama dengan skalar */
            const float *w = Wd + (size_t)__builtin_ctz(m) * 32;
            for (int q = 0; q < 4; q++) c8[q] = _mm256_add_ps(c8[q], _mm256_loadu_ps(w + 8 * q));
            stats[3]++;
        }
        for (int q = 0; q < 4; q++) {                       /* LIF decoder tanpa cabang */
            __m256 v = FMA8(c8[q], _mm256_load_ps(md + 8 * q), vdkd);
            __m256 sp = _mm256_cmp_ps(v, vthd, _CMP_GT_OQ);
            _mm256_store_ps(md + 8 * q, _mm256_blendv_ps(v, _mm256_sub_ps(v, vthd), sp));
            __m256i cq = _mm256_load_si256((const __m256i *)(cnt + 8 * q));
            _mm256_store_si256((__m256i *)(cnt + 8 * q), _mm256_sub_epi32(cq, _mm256_castps_si256(sp)));
        }
    }
    for (int i = 0; i < 32; i++) {
        if (!cnt[i]) continue;
        axpy_fma(acc, (float)cnt[i], Wo + (size_t)i * dout, dout);
        stats[4]++;
    }
    for (int j = 0; j < dout; j++) yv[j] = acc[j] * invT + bo[j];
    memcpy(y, yv, dout * sizeof(float));
}


/* ======== START: SNN_MEMO T ======== */
int snn_memo_t(const float *X, int n, int din, int L, int dout, int T,
               const float *We, const float *be, float th_e, float dk_e,
               const float *Wd, const float *bd, float th_d, float dk_d,
               const float *Wo, const float *bo,
               uint32_t *keys, float *ys, int logcap, float *err, int64_t *stats)
{
    if (L != 32 || T < 1 || T > MAXT || dout > MAXD || din > MAXD || logcap < 0 || logcap > 24) return -1;
    uint32_t mask[MAXT];
    const float invT = 1.0f / (float)T;
    const __m256 vdk = _mm256_set1_ps(dk_e), vth = _mm256_set1_ps(th_e);
    const __m256 vdkd = _mm256_set1_ps(dk_d), vthd = _mm256_set1_ps(th_d);
    for (int s = 0; s < n; s++) {
        const float *x = X + (size_t)s * din;
        stats[2] += encode(x, din, We, be, vdk, vth, T, mask);
        const uint32_t sl = slot_of_t(mask, T, logcap);
        uint32_t *k = keys + (size_t)sl * KW;
        float *y = ys + (size_t)sl * dout;
        int same = k[MAXT] != 0;
        for (int t = 0; same && t < T; t++) same = k[t] == mask[t];
        if (!same) {
            stats[1]++;
            snn_miss_t(mask, T, dout, Wd, bd, vdkd, vthd, Wo, bo, invT, y, stats);
            for (int t = 0; t < T; t++) k[t] = mask[t];
            k[MAXT] = 1;
        } else {
            stats[0]++;
        }
        double e = 0.0;
        for (int j = 0; j < dout; j++) { const double d = (double)x[j] - (double)y[j]; e += d * d; }
        err[s] = (float)(e / dout);
    }
    return 0;
}
/* ======== END: SNN_MEMO T ======== */

/* ======== START: SNN_KEYS T ======== */
int snn_keys_t(const float *X, int n, int din, int L, int T, const float *We, const float *be, float th_e,
               float dk_e, uint32_t *out, int64_t *spikes)
{
    if (L != 32 || T < 1 || T > MAXT || din > MAXD) return -1;
    const __m256 vdk = _mm256_set1_ps(dk_e), vth = _mm256_set1_ps(th_e);
    for (int s = 0; s < n; s++)
        spikes[0] += encode(X + (size_t)s * din, din, We, be, vdk, vth, T, out + (size_t)s * T);
    return 0;
}
/* ======== END: SNN_KEYS T ======== */
