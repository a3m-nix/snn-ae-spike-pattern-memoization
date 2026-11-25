/* ======== START: HEADER ========
 * s7k_keys.c — S7k K2: keluarkan tiga mask spike encoder per sampel (kunci memo eksak).
 * Encoder disalin persis dari snn_rq_memo (s7j_kernels.c) = snn_memo_v3 (LIF NEON, 3 time step), dengan
 * operasi, urutan, dan flag kompilasi yang sama. Kunci COUNT/TRI diturunkan di Python dari mask ini dengan rumus
 * bit-sliced yang sama dengan s7j_kernels.c. Gerbang G2 (s7k_rpi.py) memeriksa total spike dan hit rate simulasi
 * terhadap statistik kernel.
 * ======== END: HEADER ======== */
#include "../s7j/s7j_kernels.c"

int snn_keys(const float *X, int n, int din, int L, int T, const float *We, const float *be, float th_e, float dk_e,
             uint32_t *masks)
{
    if (L != 32 || T != 3 || din > MAXD) return -1;
    float ce[32] __attribute__((aligned(16))), me[32] __attribute__((aligned(16)));
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
        for (int t = 0; t < 3; t++) {                       /* LIF encoder NEON: = snn_rq_memo / snn_memo_v3 */
            uint32_t m = 0;
            for (int q = 0; q < 8; q++) {
                float32x4_t u = vld1q_f32(me + 4 * q), c = vld1q_f32(ce + 4 * q);
                float32x4_t v = FMA_LIF(c, u, vdk);
                uint32x4_t sp = vcgtq_f32(v, vth);
                vst1q_f32(me + 4 * q, vbslq_f32(sp, vsubq_f32(v, vth), v));
                m |= vaddvq_u32(vandq_u32(sp, vbit)) << (4 * q);
            }
            masks[(size_t)s * 3 + t] = m;
        }
    }
    return 0;
}
