/* ======== START: HEADER ========
 * s7i_kernels.c — S7i (optimasi lanjutan SNN-AE + cache di Raspberry Pi 5). Satu thread.
 * Menyertakan s7g_kernels.c tanpa perubahan (snn_memo_v2, dense_aq_memo_v2) dan menambah versi v3 yang
 * memvektorkan JALUR MISS dengan NEON, simetris untuk kedua famili:
 *   snn_memo_v3     : = snn_memo_v2, kecuali penjumlahan baris Wd, LIF decoder (tanpa cabang, hitung spike sebagai
 *                     vektor int), dan akumulasi keluaran cnt*Wo ditulis NEON. Operasi float per elemen identik
 *                     (fma terfusi seperti kode skalar dengan gcc -ffp-contract=fast), urutan penjumlahan per elemen
 *                     tidak berubah, sehingga skor wajib bit-identik dengan SNN_COUNT (diuji di fase check).
 *   dense_aq_memo_v3: = dense_aq_memo_v2, kecuali akumulasi h2 += a*Wd, ReLU, dan yv += a*Wo ditulis NEON.
 *                     Skor wajib bit-identik dengan dense_aq_memo (s7f).
 * Kompilasi: flag SAMA dengan s7g (gcc -O3 -mcpu=native -shared -fPIC).
 * ======== END: HEADER ======== */
#include "../s7g/s7g_kernels.c"

/* acc[0..n) += a * w[0..n), fma terfusi per elemen (sama dengan kode skalar yang dikontraksi gcc) */
static inline void axpy_fma(float *acc, float a, const float *w, int n)
{
    const float32x4_t va = vdupq_n_f32(a);
    int j = 0;
    for (; j + 4 <= n; j += 4)
        vst1q_f32(acc + j, FMA_LIF(vld1q_f32(acc + j), vld1q_f32(w + j), va));
    for (; j < n; j++) acc[j] = __builtin_fmaf(a, w[j], acc[j]);
}

int snn_memo_v3(const float *X, int n, int din, int L, int dout, int T,
                const float *We, const float *be, float th_e, float dk_e,
                const float *Wd, const float *bd, float th_d, float dk_d,
                const float *Wo, const float *bo,
                uint32_t *keys, float *ys, int logcap, float *err, int64_t *stats)
{
    if (L != 32 || T != 3 || dout > MAXD || din > MAXD || logcap < 0 || logcap > 24) return -1;
    float ce[32] __attribute__((aligned(16))), me[32] __attribute__((aligned(16)));
    float md[32] __attribute__((aligned(16)));
    float acc[MAXD], yv[MAXD];
    int32_t cnt[32] __attribute__((aligned(16)));
    uint32_t mask[3];
    const float invT = 1.0f / (float)T;
    const float32x4_t vdk = vdupq_n_f32(dk_e), vth = vdupq_n_f32(th_e);
    const float32x4_t vdkd = vdupq_n_f32(dk_d), vthd = vdupq_n_f32(th_d);
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
        for (int t = 0; t < 3; t++) {                       /* LIF encoder NEON: = snn_memo_v2 */
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
            stats[1]++;                                     /* miss: decoder + keluaran NEON */
            memset(md, 0, sizeof md); memset(cnt, 0, sizeof cnt); memset(acc, 0, sizeof acc);
            for (int t = 0; t < 3; t++) {
                float32x4_t c8[8];
                for (int q = 0; q < 8; q++) c8[q] = vld1q_f32(bd + 4 * q);
                for (uint32_t m = mask[t]; m; m &= m - 1) {  /* urutan baris (ctz) sama dengan v2 */
                    const float *w = Wd + (size_t)__builtin_ctz(m) * 32;
                    for (int q = 0; q < 8; q++) c8[q] = vaddq_f32(c8[q], vld1q_f32(w + 4 * q));
                    stats[3]++;
                }
                for (int q = 0; q < 8; q++) {               /* LIF decoder tanpa cabang */
                    float32x4_t v = FMA_LIF(c8[q], vld1q_f32(md + 4 * q), vdkd);
                    uint32x4_t sp = vcgtq_f32(v, vthd);
                    vst1q_f32(md + 4 * q, vbslq_f32(sp, vsubq_f32(v, vthd), v));
                    vst1q_s32(cnt + 4 * q, vsubq_s32(vld1q_s32(cnt + 4 * q), vreinterpretq_s32_u32(sp)));
                }
            }
            for (int i = 0; i < 32; i++) {
                if (!cnt[i]) continue;
                axpy_fma(acc, (float)cnt[i], Wo + (size_t)i * dout, dout);
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

int dense_aq_memo_v3(const float *X, int n, int din, int L, int dout,
                     const float *We, const float *be, const float *Wd, const float *bd,
                     const float *Wo, const float *bo, const float *delta, int bits,
                     uint32_t *keys, float *ys, int logcap, float *err, int64_t *stats)
{
    if (L != 32 || bits < 1 || bits > 3 || dout > MAXD || din > MAXD || logcap < 0 || logcap > 24) return -1;
    float h1[32] __attribute__((aligned(16))), h2[32] __attribute__((aligned(16)));
    float yv[MAXD];
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
        for (int q = 0; q < 8; q++) {                       /* kuantisasi h1 NEON: = dense_aq_memo_v2 */
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
            stats[1]++;                                     /* miss: decoder + keluaran NEON */
            memcpy(h2, bd, 32 * sizeof(float));
            for (int i = 0; i < 32; i++) {
                if (!code[i]) continue;
                axpy_fma(h2, ((float)code[i] - 0.5f) * delta[i], Wd + (size_t)i * 32, 32);
                stats[3]++;
            }
            for (int q = 0; q < 8; q++) vst1q_f32(h2 + 4 * q, vmaxq_f32(vld1q_f32(h2 + 4 * q), vzero));
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
