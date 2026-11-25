/* ======== START: HEADER ========
 * s7x_ij_kernels_x86.c — S7x-ij: port x86 (AVX2) dari s7i_kernels.c (snn_memo_v3, dense_aq_memo_v3) dan
 * s7j_kernels.c (snn_rq_memo) untuk konfirmasi n = 30 unit per dataset di CPU server. Satu thread.
 * Pemetaan NEON -> AVX2 sama dengan S7x (s7x_kernels_x86.c): 32 neuron = 4 vektor x 8 lajur; vfmaq = _mm256_fmadd_ps;
 * vcgtq = _mm256_cmp_ps(_CMP_GT_OQ); vbslq = blendv; bitmask = movemask; cnt -= mask = sub_epi32.
 *   snn_memo_v3     : jalur hit = snn_memo_v2 (S7x); jalur miss AVX2 (baris Wd, LIF decoder tanpa cabang, cnt*Wo).
 *                     Wajib bit-identik dengan SNN_COUNT.
 *   dense_aq_memo_v3: jalur hit = dense_aq_memo_v2 (S7x); jalur miss AVX2 (h2 += a*Wd, ReLU, yv += a*Wo).
 *                     Wajib bit-identik dengan dense_aq_memo (s7f). ReLU = max(0, h) dengan urutan operand yang
 *                     mempertahankan -0 dan NaN seperti `if (h < 0) h = 0` skalar.
 *   snn_rq_memo     : kunci kode spike terkuantisasi (mode 0 COUNT, 1 TRI) + pola kanonik R (dari validasi, per unit);
 *                     encoder = snn_memo_v3, jalur miss = snn_memo_v3 dengan mask kanonik. Wajib bit-identik dengan
 *                     snn_rq_ref (s7x_ij_ref.c, skalar tanpa cache) dan tidak bergantung kapasitas / isi awal cache.
 * Kompilasi: gcc -O3 -march=native -shared -fPIC (= S7f/S7x server).
 * ======== END: HEADER ======== */
#include <stdint.h>
#include <string.h>
#include <immintrin.h>

#define MAXD 64
#define FMA8(c, u, k) _mm256_fmadd_ps((k), (u), (c))        /* = k*u + c terfusi (gcc -ffp-contract=fast) */

static inline uint32_t slot_of(uint32_t k0, uint32_t k1, uint32_t k2, int logcap)
{
    uint32_t h = k0 * 0x9E3779B1u ^ k1 * 0x85EBCA77u ^ k2 * 0xC2B2AE3Du;
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

/* ce = be + x*We (sama dengan v2), lalu LIF encoder AVX2 3 time step -> mask[3]; mengembalikan jumlah spike */
static inline int64_t encode(const float *x, int din, const float *We, const float *be, __m256 vdk, __m256 vth,
                             uint32_t *mask)
{
    float ce[32] __attribute__((aligned(32))), me[32] __attribute__((aligned(32)));
    memcpy(ce, be, 32 * sizeof(float));
    for (int i = 0; i < din; i++) {
        const float a = x[i], *w = We + (size_t)i * 32;
        for (int j = 0; j < 32; j++) ce[j] += a * w[j];
    }
    memset(me, 0, sizeof me);
    int64_t pop = 0;
    for (int t = 0; t < 3; t++) {
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
static inline void snn_miss_v3(const uint32_t *mask, int dout, const float *Wd, const float *bd, __m256 vdkd,
                               __m256 vthd, const float *Wo, const float *bo, float invT, float *y, int64_t *stats)
{
    float md[32] __attribute__((aligned(32)));
    int32_t cnt[32] __attribute__((aligned(32)));
    float acc[MAXD], yv[MAXD];
    memset(md, 0, sizeof md); memset(cnt, 0, sizeof cnt); memset(acc, 0, sizeof acc);
    for (int t = 0; t < 3; t++) {
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

/* ======== START: SNN_MEMO V3 ======== */
int snn_memo_v3(const float *X, int n, int din, int L, int dout, int T,
                const float *We, const float *be, float th_e, float dk_e,
                const float *Wd, const float *bd, float th_d, float dk_d,
                const float *Wo, const float *bo,
                uint32_t *keys, float *ys, int logcap, float *err, int64_t *stats)
{
    if (L != 32 || T != 3 || dout > MAXD || din > MAXD || logcap < 0 || logcap > 24) return -1;
    uint32_t mask[3];
    const float invT = 1.0f / (float)T;
    const __m256 vdk = _mm256_set1_ps(dk_e), vth = _mm256_set1_ps(th_e);
    const __m256 vdkd = _mm256_set1_ps(dk_d), vthd = _mm256_set1_ps(th_d);
    for (int s = 0; s < n; s++) {
        const float *x = X + (size_t)s * din;
        stats[2] += encode(x, din, We, be, vdk, vth, mask);
        const uint32_t sl = slot_of(mask[0], mask[1], mask[2], logcap);
        uint32_t *k = keys + (size_t)sl * 4;
        float *y = ys + (size_t)sl * dout;
        if (!(k[3] && k[0] == mask[0] && k[1] == mask[1] && k[2] == mask[2])) {
            stats[1]++;
            snn_miss_v3(mask, dout, Wd, bd, vdkd, vthd, Wo, bo, invT, y, stats);
            k[0] = mask[0]; k[1] = mask[1]; k[2] = mask[2]; k[3] = 1;
        } else {
            stats[0]++;
        }
        double e = 0.0;
        for (int j = 0; j < dout; j++) { const double d = (double)x[j] - (double)y[j]; e += d * d; }
        err[s] = (float)(e / dout);
    }
    return 0;
}
/* ======== END: SNN_MEMO V3 ======== */

/* ======== START: DENSE_AQ V3 ======== */
int dense_aq_memo_v3(const float *X, int n, int din, int L, int dout,
                     const float *We, const float *be, const float *Wd, const float *bd,
                     const float *Wo, const float *bo, const float *delta, int bits,
                     uint32_t *keys, float *ys, int logcap, float *err, int64_t *stats)
{
    if (L != 32 || bits < 1 || bits > 3 || dout > MAXD || din > MAXD || logcap < 0 || logcap > 24) return -1;
    float h1[32] __attribute__((aligned(32))), h2[32] __attribute__((aligned(32)));
    float yv[MAXD];
    int32_t code[32] __attribute__((aligned(32)));
    const int top = (1 << bits) - 1;
    const __m256i vtop = _mm256_set1_epi32(top), vone = _mm256_set1_epi32(1);
    const __m256 vzero = _mm256_setzero_ps();
    for (int s = 0; s < n; s++) {
        const float *x = X + (size_t)s * din;
        memcpy(h1, be, 32 * sizeof(float));
        for (int i = 0; i < din; i++) {
            const float a = x[i], *w = We + (size_t)i * 32;
            for (int j = 0; j < 32; j++) h1[j] += a * w[j];
        }
        int64_t act = 0;
        for (int q = 0; q < 4; q++) {                       /* kuantisasi h1 AVX2: = dense_aq_memo_v2 (S7x) */
            __m256 h = _mm256_load_ps(h1 + 8 * q);
            __m256 pos = _mm256_cmp_ps(h, vzero, _CMP_GT_OQ);
            __m256i c = _mm256_min_epi32(_mm256_add_epi32(_mm256_cvttps_epi32(_mm256_div_ps(h, _mm256_loadu_ps(delta + 8 * q))),
                                                          vone), vtop);
            _mm256_store_si256((__m256i *)(code + 8 * q), _mm256_and_si256(_mm256_castps_si256(pos), c));
            act += __builtin_popcount((unsigned)_mm256_movemask_ps(pos));
        }
        stats[2] += act;
        uint32_t kk[3] = {0, 0, 0};
        for (int j = 0; j < 32; j++) {
            const uint32_t c = (uint32_t)code[j];
            const int bit = j * bits;
            kk[bit >> 5] |= c << (bit & 31);
            if ((bit & 31) + bits > 32) kk[(bit >> 5) + 1] |= c >> (32 - (bit & 31));
        }
        const uint32_t sl = slot_of(kk[0], kk[1], kk[2], logcap);
        uint32_t *k = keys + (size_t)sl * 4;
        float *y = ys + (size_t)sl * dout;
        if (!(k[3] && k[0] == kk[0] && k[1] == kk[1] && k[2] == kk[2])) {
            stats[1]++;                                     /* miss: decoder + keluaran AVX2 */
            memcpy(h2, bd, 32 * sizeof(float));
            for (int i = 0; i < 32; i++) {
                if (!code[i]) continue;
                axpy_fma(h2, ((float)code[i] - 0.5f) * delta[i], Wd + (size_t)i * 32, 32);
                stats[3]++;
            }
            for (int q = 0; q < 4; q++) _mm256_store_ps(h2 + 8 * q, _mm256_max_ps(vzero, _mm256_load_ps(h2 + 8 * q)));
            memcpy(yv, bo, dout * sizeof(float));
            for (int i = 0; i < 32; i++) {
                if (h2[i] == 0.f) continue;
                axpy_fma(yv, h2[i], Wo + (size_t)i * dout, dout);
                stats[4]++;
            }
            memcpy(y, yv, dout * sizeof(float));
            k[0] = kk[0]; k[1] = kk[1]; k[2] = kk[2]; k[3] = 1;
        } else {
            stats[0]++;
        }
        double e = 0.0;
        for (int j = 0; j < dout; j++) { const double d = (double)x[j] - (double)y[j]; e += d * d; }
        err[s] = (float)(e / dout);
    }
    return 0;
}
/* ======== END: DENSE_AQ V3 ======== */

/* ======== START: SNN_RQ (S7j) ========
 * Kelas per neuron dari tiga mask: lo = m0^m1^m2, hi = mayoritas -> jumlah spike = 2*hi + lo.
 *   mode 0 COUNT: kelas = jumlah (0..3); mode 1 TRI: kelas = min(jumlah, 2). Kunci (k0, k1, 0).
 * Pada miss, dekoder diberi mask kanonik cmask[t] = OR_k (cm[k] & R[3k + t]). */
int snn_rq_memo(const float *X, int n, int din, int L, int dout, int T,
                const float *We, const float *be, float th_e, float dk_e,
                const float *Wd, const float *bd, float th_d, float dk_d,
                const float *Wo, const float *bo, const uint32_t *R, int mode,
                uint32_t *keys, float *ys, int logcap, float *err, int64_t *stats)
{
    if (L != 32 || T != 3 || dout > MAXD || din > MAXD || logcap < 0 || logcap > 24 || (mode != 0 && mode != 1))
        return -1;
    uint32_t mask[3];
    const float invT = 1.0f / (float)T;
    const __m256 vdk = _mm256_set1_ps(dk_e), vth = _mm256_set1_ps(th_e);
    const __m256 vdkd = _mm256_set1_ps(dk_d), vthd = _mm256_set1_ps(th_d);
    for (int s = 0; s < n; s++) {
        const float *x = X + (size_t)s * din;
        stats[2] += encode(x, din, We, be, vdk, vth, mask);
        const uint32_t lo = mask[0] ^ mask[1] ^ mask[2];
        const uint32_t hi = (mask[0] & mask[1]) | (mask[0] & mask[2]) | (mask[1] & mask[2]);
        uint32_t cm[4];
        if (mode == 0) {
            cm[0] = ~lo & ~hi; cm[1] = lo & ~hi; cm[2] = ~lo & hi; cm[3] = lo & hi;
        } else {
            cm[0] = ~lo & ~hi; cm[1] = lo & ~hi; cm[2] = hi; cm[3] = 0;
        }
        const uint32_t k0 = cm[1] | cm[3], k1 = cm[2] | cm[3];
        const uint32_t sl = slot_of(k0, k1, 0u, logcap);
        uint32_t *k = keys + (size_t)sl * 4;
        float *y = ys + (size_t)sl * dout;
        if (!(k[3] && k[0] == k0 && k[1] == k1 && k[2] == 0u)) {
            stats[1]++;
            uint32_t cmask[3];
            for (int t = 0; t < 3; t++)
                cmask[t] = (cm[0] & R[t]) | (cm[1] & R[3 + t]) | (cm[2] & R[6 + t]) | (cm[3] & R[9 + t]);
            snn_miss_v3(cmask, dout, Wd, bd, vdkd, vthd, Wo, bo, invT, y, stats);
            k[0] = k0; k[1] = k1; k[2] = 0u; k[3] = 1;
        } else {
            stats[0]++;
        }
        double e = 0.0;
        for (int j = 0; j < dout; j++) { const double d = (double)x[j] - (double)y[j]; e += d * d; }
        err[s] = (float)(e / dout);
    }
    return 0;
}
/* ======== END: SNN_RQ ======== */
