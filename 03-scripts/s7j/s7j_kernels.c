/* ======== START: HEADER ========
 * s7j_kernels.c — S7j: SNN-AE + cache dengan kunci kode spike terkuantisasi (padanan Dense-AQ untuk SNN).
 * Encoder sama persis dengan snn_memo_v3 (LIF NEON, 3 time step). Kelas per neuron dihitung dari tiga mask spike
 * secara bit-sliced: lo = m0^m1^m2, hi = mayoritas(m0,m1,m2) sehingga jumlah spike c = 2*hi + lo.
 *   mode 0 COUNT: kelas = c (0..3), kunci (k0,k1) = (lo, hi)
 *   mode 1 TRI  : kelas = min(c, 2), kunci (k0,k1) = (lo & ~hi, hi)
 * Pada miss, dekoder diberi kereta spike KANONIK: neuron j di kelas k memancarkan pola rep[k][j] (pola tersering
 * kelas itu di data validasi, dihitung di Python per unit). R[k*3+t] = mask neuron yang pola kanoniknya berisi bit t.
 * Model berubah (seperti Dense-AQ), jadi skor tidak bit-identik dengan SNN_COUNT; yang diwajibkan: deterministik dan
 * tidak bergantung kapasitas cache maupun isi awal cache (diuji di fase check). Jalur miss = snn_memo_v3.
 * ======== END: HEADER ======== */
#include "../s7i/s7i_kernels.c"

int snn_rq_memo(const float *X, int n, int din, int L, int dout, int T,
                const float *We, const float *be, float th_e, float dk_e,
                const float *Wd, const float *bd, float th_d, float dk_d,
                const float *Wo, const float *bo, const uint32_t *R, int mode,
                uint32_t *keys, float *ys, int logcap, float *err, int64_t *stats)
{
    if (L != 32 || T != 3 || dout > MAXD || din > MAXD || logcap < 0 || logcap > 24 || (mode != 0 && mode != 1))
        return -1;
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
        for (int t = 0; t < 3; t++) {                       /* LIF encoder NEON: = snn_memo_v3 */
            uint32_t m = 0;
            for (int q = 0; q < 8; q++) {
                float32x4_t u = vld1q_f32(me + 4 * q), c = vld1q_f32(ce + 4 * q);
                float32x4_t v = FMA_LIF(c, u, vdk);
                uint32x4_t sp = vcgtq_f32(v, vth);
                vst1q_f32(me + 4 * q, vbslq_f32(sp, vsubq_f32(v, vth), v));
                m |= vaddvq_u32(vandq_u32(sp, vbit)) << (4 * q);
            }
            mask[t] = m;
        }
        const uint32_t lo = mask[0] ^ mask[1] ^ mask[2];
        const uint32_t hi = (mask[0] & mask[1]) | (mask[0] & mask[2]) | (mask[1] & mask[2]);
        uint32_t cm[4];
        if (mode == 0) {
            cm[0] = ~lo & ~hi; cm[1] = lo & ~hi; cm[2] = ~lo & hi; cm[3] = lo & hi;
        } else {
            cm[0] = ~lo & ~hi; cm[1] = lo & ~hi; cm[2] = hi; cm[3] = 0;
        }
        const uint32_t k0 = cm[1] | cm[3], k1 = cm[2] | cm[3];
        stats[2] += __builtin_popcount(mask[0]) + __builtin_popcount(mask[1]) + __builtin_popcount(mask[2]);
        const uint32_t sl = slot_of(k0, k1, 0u, logcap);
        uint32_t *k = keys + (size_t)sl * 4;
        float *y = ys + (size_t)sl * dout;
        if (!(k[3] && k[0] == k0 && k[1] == k1 && k[2] == 0u)) {
            stats[1]++;
            uint32_t cmask[3];
            for (int t = 0; t < 3; t++)
                cmask[t] = (cm[0] & R[t]) | (cm[1] & R[3 + t]) | (cm[2] & R[6 + t]) | (cm[3] & R[9 + t]);
            memset(md, 0, sizeof md); memset(cnt, 0, sizeof cnt); memset(acc, 0, sizeof acc);
            for (int t = 0; t < 3; t++) {                   /* dekoder + keluaran: = snn_memo_v3 */
                float32x4_t c8[8];
                for (int q = 0; q < 8; q++) c8[q] = vld1q_f32(bd + 4 * q);
                for (uint32_t m = cmask[t]; m; m &= m - 1) {
                    const float *w = Wd + (size_t)__builtin_ctz(m) * 32;
                    for (int q = 0; q < 8; q++) c8[q] = vaddq_f32(c8[q], vld1q_f32(w + 4 * q));
                    stats[3]++;
                }
                for (int q = 0; q < 8; q++) {
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
