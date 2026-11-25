/* ======== START: HEADER ========
 * s7g_kernels.c — S7g (trade-off SNN-AE vs Dense-AE di Raspberry Pi 5). Satu thread.
 * snn_memo_v2: sama persis dengan snn_memo (s7f_memo.c, sha 760cf934…) kecuali LIF encoder ditulis tanpa cabang
 * (select, bukan if) agar bisa divektorkan. Operasi float per neuron identik (dk*u + c, banding, kurang th), sehingga
 * kunci, isi cache, dan skor harus bit-identik dengan SNN_COUNT; ini diuji di fase check sebelum pengukuran apa pun.
 * Jalur miss (decoder + output) disalin tanpa perubahan dari snn_memo.
 * Kompilasi: flag SAMA dengan s7f (gcc -O3 -mcpu=native -shared -fPIC).
 * ======== END: HEADER ======== */
#include <stdint.h>
#include <string.h>
#include <arm_neon.h>

#define MAXD 64
#ifndef LIF_UNFUSED
#define FMA_LIF(c, u, k) vfmaq_f32((c), (u), (k))          /* = dk*u + c terfusi (gcc -ffp-contract=fast) */
#else
#define FMA_LIF(c, u, k) vaddq_f32(vmulq_f32((k), (u)), (c))
#endif

static inline uint32_t slot_of(uint32_t k0, uint32_t k1, uint32_t k2, int logcap)
{
    uint32_t h = k0 * 0x9E3779B1u ^ k1 * 0x85EBCA77u ^ k2 * 0xC2B2AE3Du;
    h ^= h >> 15;
    h *= 0x2C1B3C6Du;
    h ^= h >> 12;
    return logcap ? h >> (32 - logcap) : 0;
}

int snn_memo_v2(const float *X, int n, int din, int L, int dout, int T,
                const float *We, const float *be, float th_e, float dk_e,
                const float *Wd, const float *bd, float th_d, float dk_d,
                const float *Wo, const float *bo,
                uint32_t *keys, float *ys, int logcap, float *err, int64_t *stats)
{
    if (L != 32 || T != 3 || dout > MAXD || din > MAXD || logcap < 0 || logcap > 24) return -1;
    float ce[32] __attribute__((aligned(16))), me[32] __attribute__((aligned(16)));
    float md[MAXD], cd[MAXD], acc[MAXD], yv[MAXD];
    int cnt[MAXD];
    uint32_t mask[3];
    const float invT = 1.0f / (float)T;
    const float32x4_t vdk = vdupq_n_f32(dk_e), vth = vdupq_n_f32(th_e);
    const uint32_t bw[4] = {1u, 2u, 4u, 8u};
    const uint32x4_t vbit = vld1q_u32(bw);
    for (int s = 0; s < n; s++) {
        const float *x = X + (size_t)s * din;
        memcpy(ce, be, 32 * sizeof(float));
        for (int i = 0; i < din; i++) {
            const float a = x[i], *w = We + (size_t)i * 32;
            for (int j = 0; j < 32; j++) ce[j] += a * w[j];
        }
        memset(me, 0, sizeof me);
        int64_t pop = 0;
        for (int t = 0; t < 3; t++) {                       /* LIF encoder NEON: fma(dk,u,c), banding, kurang th */
            uint32_t m = 0;
            for (int q = 0; q < 8; q++) {
                float32x4_t u = vld1q_f32(me + 4 * q), c = vld1q_f32(ce + 4 * q);
                float32x4_t v = FMA_LIF(c, u, vdk);
                uint32x4_t sp = vcgtq_f32(v, vth);
                vst1q_f32(me + 4 * q, vbslq_f32(sp, vsubq_f32(v, vth), v));
                m |= vaddvq_u32(vandq_u32(sp, vbit)) << (4 * q);
            }
            mask[t] = m;
            pop += __builtin_popcount(m);
        }
        stats[2] += pop;
        const uint32_t sl = slot_of(mask[0], mask[1], mask[2], logcap);
        uint32_t *k = keys + (size_t)sl * 4;
        float *y = ys + (size_t)sl * dout;
        if (!(k[3] && k[0] == mask[0] && k[1] == mask[1] && k[2] == mask[2])) {
            stats[1]++;                                     /* miss: = snn_memo (s7f) */
            memset(md, 0, sizeof md); memset(cnt, 0, sizeof cnt); memset(acc, 0, sizeof acc);
            for (int t = 0; t < T; t++) {
                memcpy(cd, bd, L * sizeof(float));
                for (uint32_t m = mask[t]; m; m &= m - 1) {
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
        double e = 0.0;
        for (int j = 0; j < dout; j++) { const double d = (double)x[j] - (double)y[j]; e += d * d; }
        err[s] = (float)(e / dout);
    }
    return 0;
}

/* ======== START: DENSE_AQ V2 (kontrol keadilan, optimasi jalur hit yang setara) ========
 * Sama persis dengan dense_aq_memo (s7f_memo.c) kecuali kuantisasi h1 ditulis NEON: pembagian h1/delta memakai
 * vdivq_f32 (IEEE, identik dengan pembagian skalar), pemotongan ke int = vcvtq_s32_f32 (truncate, = cast C untuk
 * nilai positif), batas atas, dan nol untuk h1 <= 0. Kode, kunci, isi cache, dan skor wajib bit-identik. */
int dense_aq_memo_v2(const float *X, int n, int din, int L, int dout,
                     const float *We, const float *be, const float *Wd, const float *bd,
                     const float *Wo, const float *bo, const float *delta, int bits,
                     uint32_t *keys, float *ys, int logcap, float *err, int64_t *stats)
{
    if (L != 32 || bits < 1 || bits > 3 || dout > MAXD || din > MAXD || logcap < 0 || logcap > 24) return -1;
    float h1[32] __attribute__((aligned(16)));
    float h2[MAXD], yv[MAXD];
    int32_t code[32] __attribute__((aligned(16)));
    const int top = (1 << bits) - 1;
    const int32x4_t vtop = vdupq_n_s32(top), vone = vdupq_n_s32(1);
    const float32x4_t vzero = vdupq_n_f32(0.f);
    for (int s = 0; s < n; s++) {
        const float *x = X + (size_t)s * din;
        memcpy(h1, be, 32 * sizeof(float));
        for (int i = 0; i < din; i++) {
            const float a = x[i], *w = We + (size_t)i * 32;
            for (int j = 0; j < 32; j++) h1[j] += a * w[j];
        }
        int64_t act = 0;
        for (int q = 0; q < 8; q++) {
            float32x4_t h = vld1q_f32(h1 + 4 * q);
            uint32x4_t pos = vcgtq_f32(h, vzero);
            int32x4_t c = vminq_s32(vaddq_s32(vcvtq_s32_f32(vdivq_f32(h, vld1q_f32(delta + 4 * q))), vone), vtop);
            vst1q_s32(code + 4 * q, vbslq_s32(pos, c, vdupq_n_s32(0)));
            act -= vaddvq_s32(vreinterpretq_s32_u32(pos));
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
            stats[1]++;                                     /* miss: = dense_aq_memo (s7f) */
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
/* ======== END: DENSE_AQ V2 ======== */
