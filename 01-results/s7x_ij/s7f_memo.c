/* ======== START: HEADER ========
 * s7f_memo.c — Memoization eksak kode spike untuk SNN-AE (satu thread). Pelengkap s7c_native.c
 * (berkas itu TIDAK diubah; kernel DENSE/DENSE_ZS/SNN_COUNT diambil dari salinannya).
 *
 * Gagasan: input SNN-AE konstan selama T time step, sehingga decoder + output sepenuhnya
 * ditentukan oleh pola spike encoder (T bitmask x 32 neuron). Pola itu menjadi kunci cache;
 * isinya rekonstruksi y. Pada hit, hanya encoder (sama dengan lapisan 1 Dense) + LIF encoder +
 * lookup yang dihitung. Pada miss, decoder + output dihitung persis seperti SNN_COUNT di s7c
 * (urutan operasi float sama), lalu disimpan. Skor dan keputusan identik bit dengan SNN_COUNT.
 *
 * Cache: direct-mapped, kapasitas 2^logcap slot, disediakan pemanggil:
 *   keys [cap * 4] uint32 : k0, k1, k2 (bitmask t=0..2), valid
 *   ys   [cap * dout] float
 * stats: [0] hit, [1] miss, [2] spike encoder, [3] baris Wd dibaca, [4] baris Wo dibaca
 * Syarat: L == 32, T == 3 (model final), dout <= MAXD.
 * Kompilasi: flag SAMA dengan s7c_native.c (gcc -O3 -mcpu=native / -march=native).
 * ======== END: HEADER ======== */
#include <stdint.h>
#include <string.h>

#define MAXD 64

static inline uint32_t slot_of(uint32_t k0, uint32_t k1, uint32_t k2, int logcap)
{
    uint32_t h = k0 * 0x9E3779B1u ^ k1 * 0x85EBCA77u ^ k2 * 0xC2B2AE3Du;
    h ^= h >> 15;
    h *= 0x2C1B3C6Du;
    h ^= h >> 12;
    return logcap ? h >> (32 - logcap) : 0;
}

/* Mengembalikan 0 OK, -1 argumen tidak valid. */
int snn_memo(const float *X, int n, int din, int L, int dout, int T,
             const float *We, const float *be, float th_e, float dk_e,
             const float *Wd, const float *bd, float th_d, float dk_d,
             const float *Wo, const float *bo,
             uint32_t *keys, float *ys, int logcap, float *err, int64_t *stats)
{
    if (L != 32 || T != 3 || dout > MAXD || din > MAXD || logcap < 0 || logcap > 24) return -1;
    float ce[MAXD], me[MAXD], md[MAXD], cd[MAXD], acc[MAXD], yv[MAXD];
    int cnt[MAXD];
    uint32_t mask[3];
    const float invT = 1.0f / (float)T;
    for (int s = 0; s < n; s++) {
        const float *x = X + (size_t)s * din;
        memcpy(ce, be, L * sizeof(float));                  /* arus input: sekali (= s7c) */
        for (int i = 0; i < din; i++) {
            const float a = x[i], *w = We + (size_t)i * L;
            for (int j = 0; j < L; j++) ce[j] += a * w[j];
        }
        memset(me, 0, sizeof me);
        for (int t = 0; t < T; t++) {                       /* LIF encoder (= s7c) -> bitmask */
            uint32_t m = 0;
            for (int j = 0; j < L; j++) {
                me[j] = dk_e * me[j] + ce[j];
                if (me[j] > th_e) { me[j] -= th_e; m |= 1u << j; }
            }
            mask[t] = m;
            stats[2] += __builtin_popcount(m);
        }
        const uint32_t sl = slot_of(mask[0], mask[1], mask[2], logcap);
        uint32_t *k = keys + (size_t)sl * 4;
        float *y = ys + (size_t)sl * dout;
        if (!(k[3] && k[0] == mask[0] && k[1] == mask[1] && k[2] == mask[2])) {
            stats[1]++;                                     /* miss: decoder + output (= SNN_COUNT) */
            memset(md, 0, sizeof md); memset(cnt, 0, sizeof cnt); memset(acc, 0, sizeof acc);
            for (int t = 0; t < T; t++) {
                memcpy(cd, bd, L * sizeof(float));
                for (uint32_t m = mask[t]; m; m &= m - 1) { /* bit menaik = urutan i di s7c */
                    const float *w = Wd + (size_t)__builtin_ctz(m) * L;
                    for (int j = 0; j < L; j++) cd[j] += w[j];
                    stats[3]++;
                }
                for (int j = 0; j < L; j++) {
                    md[j] = dk_d * md[j] + cd[j];
                    if (md[j] > th_d) { md[j] -= th_d; cnt[j]++; }
                }
            }
            for (int i = 0; i < L; i++) {
                if (!cnt[i]) continue;
                const float c = (float)cnt[i], *w = Wo + (size_t)i * dout;
                for (int j = 0; j < dout; j++) acc[j] += c * w[j];
                stats[4]++;
            }
            for (int j = 0; j < dout; j++) yv[j] = acc[j] * invT + bo[j];
            memcpy(y, yv, dout * sizeof(float));
            k[0] = mask[0]; k[1] = mask[1]; k[2] = mask[2]; k[3] = 1;
        } else {
            stats[0]++;
        }
        double e = 0.0;                                     /* = s7c: (x - y)^2 dalam double */
        for (int j = 0; j < dout; j++) { const double d = (double)x[j] - (double)y[j]; e += d * d; }
        err[s] = (float)(e / dout);
    }
    return 0;
}

/* ======== START: KONTROL KEADILAN — DENSE-AE DENGAN h1 TERDISKRETKAN (DENSE_AQ) ========
 * Dense-AE diberi "bottleneck diskret" agar dapat di-cache seperti SNN (MENGUBAH model):
 *   kode_j = 0 bila h1_j <= 0, selain itu min(2^b - 1, floor(h1_j / delta_j) + 1)
 *   h1q_j  = 0 untuk kode 0, selain itu (kode_j - 0.5) * delta_j
 * Kunci = kode 32 neuron x b bit (b <= 3, maks 96 bit). Decoder + output dari h1q (zero-skip
 * seperti DENSE_ZS s7c), disimpan di cache direct-mapped yang sama strukturnya dengan snn_memo.
 * stats: [0] hit, [1] miss, [2] neuron h1 bukan nol, [3] baris Wd dibaca, [4] baris Wo dibaca
 */
int dense_aq_memo(const float *X, int n, int din, int L, int dout,
                  const float *We, const float *be, const float *Wd, const float *bd,
                  const float *Wo, const float *bo, const float *delta, int bits,
                  uint32_t *keys, float *ys, int logcap, float *err, int64_t *stats)
{
    if (L != 32 || bits < 1 || bits > 3 || dout > MAXD || din > MAXD || logcap < 0 || logcap > 24) return -1;
    float h1[MAXD], h2[MAXD], yv[MAXD];
    int code[MAXD];
    const int top = (1 << bits) - 1;
    for (int s = 0; s < n; s++) {
        const float *x = X + (size_t)s * din;
        memcpy(h1, be, L * sizeof(float));                  /* lapisan 1 (= s7c dense) */
        for (int i = 0; i < din; i++) {
            const float a = x[i], *w = We + (size_t)i * L;
            for (int j = 0; j < L; j++) h1[j] += a * w[j];
        }
        uint32_t kk[3] = {0, 0, 0};
        for (int j = 0; j < L; j++) {
            int c = 0;
            if (h1[j] > 0.f) {
                c = (int)(h1[j] / delta[j]) + 1;
                if (c > top) c = top;
                stats[2]++;
            }
            code[j] = c;
            const int bit = j * bits;
            kk[bit >> 5] |= (uint32_t)c << (bit & 31);
            if ((bit & 31) + bits > 32) kk[(bit >> 5) + 1] |= (uint32_t)c >> (32 - (bit & 31));
        }
        const uint32_t sl = slot_of(kk[0], kk[1], kk[2], logcap);
        uint32_t *k = keys + (size_t)sl * 4;
        float *y = ys + (size_t)sl * dout;
        if (!(k[3] && k[0] == kk[0] && k[1] == kk[1] && k[2] == kk[2])) {
            stats[1]++;
            memcpy(h2, bd, L * sizeof(float));
            for (int i = 0; i < L; i++) {
                if (!code[i]) continue;
                const float a = ((float)code[i] - 0.5f) * delta[i], *w = Wd + (size_t)i * L;
                for (int j = 0; j < L; j++) h2[j] += a * w[j];
                stats[3]++;
            }
            for (int j = 0; j < L; j++) if (h2[j] < 0.f) h2[j] = 0.f;
            memcpy(yv, bo, dout * sizeof(float));
            for (int i = 0; i < L; i++) {
                const float a = h2[i], *w = Wo + (size_t)i * dout;
                if (a == 0.f) continue;
                for (int j = 0; j < dout; j++) yv[j] += a * w[j];
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
/* ======== END: KONTROL KEADILAN ======== */
