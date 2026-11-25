/* ======== START: HEADER ========
 * s7x_ij_ref.c — rujukan skalar tanpa cache untuk SNN_RQ (S7j), hanya untuk fase check S7x-ij.
 * Encoder dan dekoder disalin dari snn_memo (s7f_memo.c, sha 760cf934…): LIF skalar bercabang, baris Wd menurut
 * bit menaik, cnt*Wo, y = acc*invT + bo. Satu-satunya perbedaan: dekoder diberi mask kanonik
 * cmask[t] = OR_k (cm[k] & R[3k + t]) dengan kelas COUNT/TRI (definisi = s7j_kernels.c). Tidak ada cache, sehingga
 * skor ini menjadi definisi model RQ yang tidak bergantung kapasitas maupun isi awal cache.
 * Kompilasi: gcc -O3 -march=native -shared -fPIC (= kernel yang diuji).
 * ======== END: HEADER ======== */
#include <stdint.h>
#include <string.h>

#define MAXD 64

int snn_rq_ref(const float *X, int n, int din, int L, int dout, int T,
               const float *We, const float *be, float th_e, float dk_e,
               const float *Wd, const float *bd, float th_d, float dk_d,
               const float *Wo, const float *bo, const uint32_t *R, int mode, float *err, uint32_t *keys_out)
{
    if (L != 32 || T != 3 || dout > MAXD || din > MAXD || (mode != 0 && mode != 1)) return -1;
    float ce[MAXD], me[MAXD], md[MAXD], cd[MAXD], acc[MAXD], yv[MAXD];
    int cnt[MAXD];
    uint32_t mask[3];
    const float invT = 1.0f / (float)T;
    for (int s = 0; s < n; s++) {
        const float *x = X + (size_t)s * din;
        memcpy(ce, be, L * sizeof(float));
        for (int i = 0; i < din; i++) {
            const float a = x[i], *w = We + (size_t)i * L;
            for (int j = 0; j < L; j++) ce[j] += a * w[j];
        }
        memset(me, 0, sizeof me);
        for (int t = 0; t < T; t++) {
            uint32_t m = 0;
            for (int j = 0; j < L; j++) {
                me[j] = dk_e * me[j] + ce[j];
                if (me[j] > th_e) { me[j] -= th_e; m |= 1u << j; }
            }
            mask[t] = m;
        }
        uint32_t cm[4] = {0, 0, 0, 0};                     /* kelas per neuron, dihitung per bit (skalar) */
        for (int j = 0; j < L; j++) {
            int c = (int)((mask[0] >> j) & 1u) + (int)((mask[1] >> j) & 1u) + (int)((mask[2] >> j) & 1u);
            if (mode == 1 && c > 2) c = 2;
            cm[c] |= 1u << j;
        }
        keys_out[2 * s] = cm[1] | cm[3];
        keys_out[2 * s + 1] = cm[2] | cm[3];
        uint32_t cmask[3];
        for (int t = 0; t < 3; t++)
            cmask[t] = (cm[0] & R[t]) | (cm[1] & R[3 + t]) | (cm[2] & R[6 + t]) | (cm[3] & R[9 + t]);
        memset(md, 0, sizeof md); memset(cnt, 0, sizeof cnt); memset(acc, 0, sizeof acc);
        for (int t = 0; t < T; t++) {
            memcpy(cd, bd, L * sizeof(float));
            for (uint32_t m = cmask[t]; m; m &= m - 1) {
                const float *w = Wd + (size_t)__builtin_ctz(m) * L;
                for (int j = 0; j < L; j++) cd[j] += w[j];
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
        }
        for (int j = 0; j < dout; j++) yv[j] = acc[j] * invT + bo[j];
        double e = 0.0;
        for (int j = 0; j < dout; j++) { const double d = (double)x[j] - (double)yv[j]; e += d * d; }
        err[s] = (float)(e / dout);
    }
    return 0;
}
