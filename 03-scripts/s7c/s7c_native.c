/* ======== START: HEADER ========
 * s7c_native.c — Kernel native C untuk S7c v2 (Raspberry Pi 5, satu thread).
 * Dense-AE dan SNN-AE dengan BN + skala 1/sqrt(fan_in) sudah dilipat ke bobot oleh driver.
 * Bobot row-major [in][out] (sama dengan kernel Keras).
 *   dense_ae : zs=0 padat; zs=1 lewati aktivasi ReLU nol (zero-skip, setara T2).
 *   snn_ae   : arus input encoder dihitung sekali (input konstan antar time step).
 *              mode 0 TENSOR : semua baris dikalikan spike 0/1 tiap t (seperti TF)
 *              mode 1 SPIKE  : satu baris bobot per spike per t (event-driven)
 *              mode 2 COUNT  : enc->dec per spike per t; output satu baris per neuron
 *                              decoder aktif, dikali jumlah spike (readout count-based)
 *   pmu_*    : perf_event_open (user space): cycles, instructions, L1D_CACHE (0x04),
 *              L1D_CACHE_REFILL (0x03), MEM_ACCESS (0x13).
 * Kompilasi: gcc -O3 -mcpu=native -shared -fPIC -o s7c_native.so s7c_native.c
 * ======== END: HEADER ======== */
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <sys/syscall.h>
#include <linux/perf_event.h>

#define MAXD 64

/* ======== START: DENSE-AE ======== */
/* stats[0] += nol di h1, stats[1] += nol di h2 */
void dense_ae(const float *X, int n, int din, int L, int dout,
              const float *We, const float *be, const float *Wd, const float *bd,
              const float *Wo, const float *bo, int zs, float *err, int64_t *stats)
{
    float h1[MAXD], h2[MAXD], y[MAXD];
    for (int s = 0; s < n; s++) {
        const float *x = X + (size_t)s * din;
        memcpy(h1, be, L * sizeof(float));
        for (int i = 0; i < din; i++) {
            const float a = x[i], *w = We + (size_t)i * L;
            for (int j = 0; j < L; j++) h1[j] += a * w[j];
        }
        for (int j = 0; j < L; j++) if (h1[j] < 0.f) h1[j] = 0.f;
        memcpy(h2, bd, L * sizeof(float));
        for (int i = 0; i < L; i++) {
            const float a = h1[i], *w = Wd + (size_t)i * L;
            if (a == 0.f) { stats[0]++; if (zs) continue; }
            for (int j = 0; j < L; j++) h2[j] += a * w[j];
        }
        for (int j = 0; j < L; j++) if (h2[j] < 0.f) h2[j] = 0.f;
        memcpy(y, bo, dout * sizeof(float));
        for (int i = 0; i < L; i++) {
            const float a = h2[i], *w = Wo + (size_t)i * dout;
            if (a == 0.f) { stats[1]++; if (zs) continue; }
            for (int j = 0; j < dout; j++) y[j] += a * w[j];
        }
        double e = 0.0;
        for (int j = 0; j < dout; j++) { const double d = (double)x[j] - (double)y[j]; e += d * d; }
        err[s] = (float)(e / dout);
    }
}
/* ======== END: DENSE-AE ======== */

/* ======== START: SNN-AE ======== */
/* stats: [0] spike encoder, [1] spike decoder, [2] neuron decoder aktif (>=1 spike),
          [3] baris Wo dibaca, [4] baris Wd dibaca */
void snn_ae(const float *X, int n, int din, int L, int dout, int T,
            const float *We, const float *be, float th_e, float dk_e,
            const float *Wd, const float *bd, float th_d, float dk_d,
            const float *Wo, const float *bo, int mode, float *err, int64_t *stats)
{
    float ce[MAXD], me[MAXD], md[MAXD], cd[MAXD], acc[MAXD];
    unsigned char se[MAXD], sd[MAXD];
    int cnt[MAXD];
    const float invT = 1.0f / (float)T;
    for (int s = 0; s < n; s++) {
        const float *x = X + (size_t)s * din;
        memcpy(ce, be, L * sizeof(float));                  /* arus input: sekali */
        for (int i = 0; i < din; i++) {
            const float a = x[i], *w = We + (size_t)i * L;
            for (int j = 0; j < L; j++) ce[j] += a * w[j];
        }
        memset(me, 0, sizeof me); memset(md, 0, sizeof md);
        memset(cnt, 0, sizeof cnt); memset(acc, 0, sizeof acc);
        for (int t = 0; t < T; t++) {
            for (int j = 0; j < L; j++) {                   /* LIF encoder */
                me[j] = dk_e * me[j] + ce[j];
                se[j] = me[j] > th_e;
                if (se[j]) { me[j] -= th_e; stats[0]++; }
            }
            memcpy(cd, bd, L * sizeof(float));              /* encoder -> decoder */
            for (int i = 0; i < L; i++) {
                const float *w = Wd + (size_t)i * L;
                if (mode == 0) {
                    const float a = (float)se[i];
                    for (int j = 0; j < L; j++) cd[j] += a * w[j];
                    stats[4]++;
                } else if (se[i]) {
                    for (int j = 0; j < L; j++) cd[j] += w[j];
                    stats[4]++;
                }
            }
            for (int j = 0; j < L; j++) {                   /* LIF decoder */
                md[j] = dk_d * md[j] + cd[j];
                sd[j] = md[j] > th_d;
                if (sd[j]) { md[j] -= th_d; stats[1]++; cnt[j]++; }
            }
            if (mode == 2) continue;                        /* count: output setelah T */
            for (int i = 0; i < L; i++) {                   /* decoder -> output */
                const float *w = Wo + (size_t)i * dout;
                if (mode == 0) {
                    const float a = (float)sd[i];
                    for (int j = 0; j < dout; j++) acc[j] += a * w[j];
                    stats[3]++;
                } else if (sd[i]) {
                    for (int j = 0; j < dout; j++) acc[j] += w[j];
                    stats[3]++;
                }
            }
        }
        for (int i = 0; i < L; i++) {
            if (!cnt[i]) continue;
            stats[2]++;
            if (mode == 2) {
                const float c = (float)cnt[i], *w = Wo + (size_t)i * dout;
                for (int j = 0; j < dout; j++) acc[j] += c * w[j];
                stats[3]++;
            }
        }
        double e = 0.0;
        for (int j = 0; j < dout; j++) {
            const double d = (double)x[j] - (double)(acc[j] * invT + bo[j]);
            e += d * d;
        }
        err[s] = (float)(e / dout);
    }
}
/* ======== END: SNN-AE ======== */

/* ======== START: PMU (perf_event_open) ======== */
#define NEV 5
static int fds[NEV] = {-1, -1, -1, -1, -1};
static const uint32_t EV_TYPE[NEV] = {PERF_TYPE_HARDWARE, PERF_TYPE_HARDWARE, PERF_TYPE_RAW, PERF_TYPE_RAW, PERF_TYPE_RAW};
static const uint64_t EV_CFG[NEV] = {PERF_COUNT_HW_CPU_CYCLES, PERF_COUNT_HW_INSTRUCTIONS, 0x04, 0x03, 0x13};

/* Membuka counter (sekali). Mengembalikan bitmask counter yang berhasil dibuka. */
int pmu_open(void)
{
    int ok = 0;
    for (int k = 0; k < NEV; k++) {
        if (fds[k] >= 0) { ok |= 1 << k; continue; }
        struct perf_event_attr a;
        memset(&a, 0, sizeof a);
        a.size = sizeof a; a.type = EV_TYPE[k]; a.config = EV_CFG[k];
        a.disabled = 1; a.exclude_kernel = 1; a.exclude_hv = 1;
        fds[k] = (int)syscall(__NR_perf_event_open, &a, 0, -1, -1, 0);
        if (fds[k] >= 0) ok |= 1 << k;
    }
    return ok;
}

void pmu_begin(void)
{
    for (int k = 0; k < NEV; k++) if (fds[k] >= 0) {
        ioctl(fds[k], PERF_EVENT_IOC_RESET, 0);
        ioctl(fds[k], PERF_EVENT_IOC_ENABLE, 0);
    }
}

/* out[k] = nilai counter k, atau -1 bila tidak tersedia */
void pmu_end(int64_t *out)
{
    for (int k = 0; k < NEV; k++) if (fds[k] >= 0) ioctl(fds[k], PERF_EVENT_IOC_DISABLE, 0);
    for (int k = 0; k < NEV; k++) {
        uint64_t v = 0;
        out[k] = (fds[k] >= 0 && read(fds[k], &v, sizeof v) == (ssize_t)sizeof v) ? (int64_t)v : -1;
    }
}
/* ======== END: PMU (perf_event_open) ======== */
