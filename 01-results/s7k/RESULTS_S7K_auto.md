# S7k — Automated Analysis Results

## K1 — Per-Attack-Subtype Detection (Server, 30 Units)

### Gate G1

| dataset | variant | ref | max_abs_dAUC | max_abs_dF1 | pass |
|---|---|---|---|---|---|
| edge_iiotset | SNN_EXACT | S7x-ij accuracy_long | 0.00e+00 | 0.00e+00 | True |
| edge_iiotset | SNN_RQC_16 | S7x-ij accuracy_long | 0.00e+00 | 0.00e+00 | True |
| edge_iiotset | SNN_RQT_16 | S7x-ij accuracy_long | 0.00e+00 | 0.00e+00 | True |
| edge_iiotset | DENSE_ZS | acc30_long (descriptive) | 7.02e-09 | 2.22e-16 | True |
| edge_iiotset | DENSE_AQV33_16 | acc30_long (descriptive) | 0.00e+00 | 2.22e-16 | True |
| edge_iiotset | DENSE_AQV32_16 | acc30_long (descriptive) | 0.00e+00 | 2.22e-16 | True |
| ciciot2023 | SNN_EXACT | S7x-ij accuracy_long | 0.00e+00 | 0.00e+00 | True |
| ciciot2023 | SNN_RQC_16 | S7x-ij accuracy_long | 0.00e+00 | 0.00e+00 | True |
| ciciot2023 | SNN_RQT_16 | S7x-ij accuracy_long | 0.00e+00 | 0.00e+00 | True |
| ciciot2023 | DENSE_ZS | acc30_long (descriptive) | 2.95e-07 | 1.11e-16 | True |
| ciciot2023 | DENSE_AQV33_16 | acc30_long (descriptive) | 0.00e+00 | 1.11e-16 | True |
| ciciot2023 | DENSE_AQV32_16 | acc30_long (descriptive) | 0.00e+00 | 1.11e-16 | True |

### edge_iiotset: Per-Subtype Recall (Median of 30 Units; Δ vs. Base Model)

| variant | subtype | base_median | rate_median | Δ [CI95] | n_units_drop_gt_0.05 | decision_change_median | flag |
|---|---|---|---|---|---|---|---|
| SNN_RQC_16 | ddos-http-flood-attacks | 0.996 | 0.996 | +0.000 [+0.000; +0.000] | 0 | 0.000 | – |
| SNN_RQC_16 | ddos-icmp-flood-attacks | 1.000 | 1.000 | +0.000 [+0.000; +0.000] | 0 | 0.000 | – |
| SNN_RQC_16 | ddos-tcp-syn-flood-attacks | 1.000 | 1.000 | +0.000 [+0.000; +0.000] | 0 | 0.000 | – |
| SNN_RQC_16 | ddos-udp-flood-attacks | 1.000 | 1.000 | +0.000 [+0.000; +0.000] | 0 | 0.000 | – |
| SNN_RQC_16 | normal | 0.008 | 0.009 | +0.000 [-0.000; +0.000] | 0 | 0.001 | FPR |
| SNN_RQT_16 | ddos-http-flood-attacks | 0.996 | 0.994 | -0.002 [-0.004; -0.001] | 1 | 0.003 | – |
| SNN_RQT_16 | ddos-icmp-flood-attacks | 1.000 | 1.000 | +0.000 [+0.000; +0.000] | 0 | 0.000 | – |
| SNN_RQT_16 | ddos-tcp-syn-flood-attacks | 1.000 | 1.000 | +0.000 [+0.000; +0.000] | 0 | 0.000 | – |
| SNN_RQT_16 | ddos-udp-flood-attacks | 1.000 | 1.000 | +0.000 [+0.000; +0.000] | 0 | 0.000 | – |
| SNN_RQT_16 | normal | 0.008 | 0.008 | +0.000 [-0.000; +0.000] | 0 | 0.006 | FPR |
| DENSE_AQV33_16 | ddos-http-flood-attacks | 1.000 | 0.999 | -0.001 [-0.003; -0.000] | 1 | 0.001 | – |
| DENSE_AQV33_16 | ddos-icmp-flood-attacks | 1.000 | 1.000 | +0.000 [+0.000; +0.000] | 0 | 0.000 | – |
| DENSE_AQV33_16 | ddos-tcp-syn-flood-attacks | 1.000 | 1.000 | +0.000 [+0.000; +0.000] | 0 | 0.000 | – |
| DENSE_AQV33_16 | ddos-udp-flood-attacks | 1.000 | 1.000 | +0.000 [+0.000; +0.000] | 0 | 0.000 | – |
| DENSE_AQV33_16 | normal | 0.007 | 0.008 | +0.000 [-0.000; +0.001] | 0 | 0.012 | FPR |
| DENSE_AQV32_16 | ddos-http-flood-attacks | 1.000 | 0.916 | -0.084 [-0.170; -0.037] | 18 | 0.084 | – |
| DENSE_AQV32_16 | ddos-icmp-flood-attacks | 1.000 | 1.000 | +0.000 [+0.000; +0.000] | 0 | 0.000 | – |
| DENSE_AQV32_16 | ddos-tcp-syn-flood-attacks | 1.000 | 1.000 | +0.000 [+0.000; +0.000] | 0 | 0.000 | – |
| DENSE_AQV32_16 | ddos-udp-flood-attacks | 1.000 | 1.000 | +0.000 [+0.000; +0.000] | 0 | 0.000 | – |
| DENSE_AQV32_16 | normal | 0.007 | 0.011 | +0.002 [+0.001; +0.003] | 2 | 0.013 | FPR |

### ciciot2023: Per-Subtype Recall (Median of 30 Units; Δ vs. Base Model)

| variant | subtype | base_median | rate_median | Δ [CI95] | n_units_drop_gt_0.05 | decision_change_median | flag |
|---|---|---|---|---|---|---|---|
| SNN_RQC_16 | DDoS-ACK_Fragmentation | 0.980 | 0.979 | -0.001 [-0.001; -0.000] | 0 | 0.002 | – |
| SNN_RQC_16 | DDoS-HTTP_Flood- | 0.177 | 0.168 | -0.007 [-0.012; -0.001] | 2 | 0.014 | floor |
| SNN_RQC_16 | DDoS-ICMP_Flood | 0.775 | 0.353 | +0.000 [-0.037; +0.000] | 10 | 0.004 | – |
| SNN_RQC_16 | DDoS-ICMP_Fragmentation | 0.956 | 0.956 | +0.000 [-0.000; +0.000] | 0 | 0.001 | – |
| SNN_RQC_16 | DDoS-PSHACK_Flood | 0.653 | 0.623 | -0.019 [-0.029; -0.003] | 8 | 0.034 | – |
| SNN_RQC_16 | DDoS-RSTFINFlood | 0.994 | 0.994 | +0.000 [-0.000; +0.000] | 0 | 0.000 | – |
| SNN_RQC_16 | DDoS-SYN_Flood | 0.942 | 0.857 | -0.012 [-0.023; -0.003] | 7 | 0.036 | – |
| SNN_RQC_16 | DDoS-SlowLoris | 0.077 | 0.072 | -0.001 [-0.002; +0.000] | 0 | 0.008 | floor |
| SNN_RQC_16 | DDoS-SynonymousIP_Flood | 0.965 | 0.912 | -0.000 [-0.021; +0.000] | 7 | 0.030 | – |
| SNN_RQC_16 | DDoS-TCP_Flood | 0.994 | 0.964 | -0.002 [-0.015; +0.003] | 5 | 0.022 | – |
| SNN_RQC_16 | DDoS-UDP_Flood | 0.001 | 0.001 | -0.000 [-0.003; +0.000] | 2 | 0.003 | floor |
| SNN_RQC_16 | DDoS-UDP_Fragmentation | 0.975 | 0.974 | +0.000 [-0.001; +0.000] | 0 | 0.001 | – |
| SNN_RQC_16 | Mirai-greeth_flood | 0.959 | 0.958 | +0.000 [-0.000; +0.000] | 0 | 0.000 | – |
| SNN_RQC_16 | Mirai-greip_flood | 0.959 | 0.958 | -0.000 [-0.001; +0.000] | 0 | 0.001 | – |
| SNN_RQC_16 | Mirai-udpplain | 0.021 | 0.002 | +0.000 [-0.047; +0.000] | 10 | 0.005 | floor |
| SNN_RQC_16 | normal | 0.010 | 0.008 | +0.000 [-0.000; +0.001] | 1 | 0.005 | FPR |
| SNN_RQT_16 | DDoS-ACK_Fragmentation | 0.980 | 0.977 | -0.002 [-0.003; -0.001] | 0 | 0.003 | – |
| SNN_RQT_16 | DDoS-HTTP_Flood- | 0.177 | 0.173 | -0.010 [-0.019; -0.000] | 5 | 0.031 | floor |
| SNN_RQT_16 | DDoS-ICMP_Flood | 0.775 | 0.000 | -0.178 [-0.597; -0.000] | 16 | 0.386 | – |
| SNN_RQT_16 | DDoS-ICMP_Fragmentation | 0.956 | 0.956 | -0.001 [-0.002; -0.001] | 0 | 0.002 | – |
| SNN_RQT_16 | DDoS-PSHACK_Flood | 0.653 | 0.570 | -0.092 [-0.103; -0.058] | 22 | 0.100 | – |
| SNN_RQT_16 | DDoS-RSTFINFlood | 0.994 | 0.993 | -0.000 [-0.000; +0.000] | 6 | 0.000 | – |
| SNN_RQT_16 | DDoS-SYN_Flood | 0.942 | 0.690 | -0.144 [-0.237; -0.061] | 20 | 0.206 | – |
| SNN_RQT_16 | DDoS-SlowLoris | 0.077 | 0.071 | -0.006 [-0.013; -0.002] | 2 | 0.019 | floor |
| SNN_RQT_16 | DDoS-SynonymousIP_Flood | 0.965 | 0.732 | -0.132 [-0.263; -0.067] | 20 | 0.210 | – |
| SNN_RQT_16 | DDoS-TCP_Flood | 0.994 | 0.807 | -0.153 [-0.200; -0.103] | 25 | 0.153 | consistent drop |
| SNN_RQT_16 | DDoS-UDP_Flood | 0.001 | 0.000 | -0.001 [-0.005; +0.000] | 2 | 0.001 | floor |
| SNN_RQT_16 | DDoS-UDP_Fragmentation | 0.975 | 0.974 | -0.001 [-0.002; +0.000] | 0 | 0.002 | – |
| SNN_RQT_16 | Mirai-greeth_flood | 0.959 | 0.958 | -0.000 [-0.001; -0.000] | 0 | 0.001 | – |
| SNN_RQT_16 | Mirai-greip_flood | 0.959 | 0.957 | -0.001 [-0.002; -0.001] | 0 | 0.003 | – |
| SNN_RQT_16 | Mirai-udpplain | 0.021 | 0.002 | -0.005 [-0.085; -0.000] | 11 | 0.018 | floor |
| SNN_RQT_16 | normal | 0.010 | 0.009 | -0.000 [-0.003; -0.000] | 1 | 0.007 | FPR |
| DENSE_AQV33_16 | DDoS-ACK_Fragmentation | 0.981 | 0.979 | -0.001 [-0.003; +0.000] | 0 | 0.004 | – |
| DENSE_AQV33_16 | DDoS-HTTP_Flood- | 0.194 | 0.175 | -0.022 [-0.032; -0.008] | 4 | 0.047 | floor |
| DENSE_AQV33_16 | DDoS-ICMP_Flood | 0.997 | 0.997 | +0.000 [-0.000; +0.000] | 2 | 0.000 | – |
| DENSE_AQV33_16 | DDoS-ICMP_Fragmentation | 0.958 | 0.957 | -0.001 [-0.001; -0.000] | 0 | 0.003 | – |
| DENSE_AQV33_16 | DDoS-PSHACK_Flood | 0.994 | 0.777 | -0.091 [-0.184; -0.017] | 18 | 0.118 | – |
| DENSE_AQV33_16 | DDoS-RSTFINFlood | 0.994 | 0.994 | +0.000 [-0.000; +0.000] | 0 | 0.000 | – |
| DENSE_AQV33_16 | DDoS-SYN_Flood | 0.986 | 0.959 | -0.028 [-0.035; -0.016] | 1 | 0.028 | – |
| DENSE_AQV33_16 | DDoS-SlowLoris | 0.074 | 0.071 | -0.004 [-0.012; +0.005] | 0 | 0.028 | floor |
| DENSE_AQV33_16 | DDoS-SynonymousIP_Flood | 0.996 | 0.996 | +0.000 [-0.000; +0.000] | 1 | 0.000 | – |
| DENSE_AQV33_16 | DDoS-TCP_Flood | 0.998 | 0.998 | -0.000 [-0.001; +0.000] | 2 | 0.000 | – |
| DENSE_AQV33_16 | DDoS-UDP_Flood | 0.001 | 0.005 | +0.000 [+0.000; +0.006] | 1 | 0.007 | floor |
| DENSE_AQV33_16 | DDoS-UDP_Fragmentation | 0.976 | 0.975 | -0.000 [-0.001; +0.000] | 0 | 0.002 | – |
| DENSE_AQV33_16 | Mirai-greeth_flood | 0.959 | 0.959 | +0.000 [-0.001; +0.000] | 0 | 0.001 | – |
| DENSE_AQV33_16 | Mirai-greip_flood | 0.961 | 0.960 | -0.001 [-0.002; -0.000] | 0 | 0.004 | – |
| DENSE_AQV33_16 | Mirai-udpplain | 0.002 | 0.011 | +0.008 [+0.001; +0.048] | 0 | 0.012 | floor |
| DENSE_AQV33_16 | normal | 0.009 | 0.013 | +0.002 [+0.000; +0.008] | 1 | 0.011 | FPR |
| DENSE_AQV32_16 | DDoS-ACK_Fragmentation | 0.981 | 0.973 | -0.007 [-0.008; -0.006] | 0 | 0.008 | – |
| DENSE_AQV32_16 | DDoS-HTTP_Flood- | 0.194 | 0.120 | -0.058 [-0.083; -0.038] | 17 | 0.086 | floor |
| DENSE_AQV32_16 | DDoS-ICMP_Flood | 0.997 | 0.726 | -0.222 [-0.912; -0.000] | 17 | 0.271 | – |
| DENSE_AQV32_16 | DDoS-ICMP_Fragmentation | 0.958 | 0.955 | -0.004 [-0.004; -0.002] | 0 | 0.004 | – |
| DENSE_AQV32_16 | DDoS-PSHACK_Flood | 0.994 | 0.618 | -0.321 [-0.366; -0.217] | 27 | 0.321 | consistent drop |
| DENSE_AQV32_16 | DDoS-RSTFINFlood | 0.994 | 0.994 | -0.000 [-0.000; +0.000] | 0 | 0.000 | – |
| DENSE_AQV32_16 | DDoS-SYN_Flood | 0.986 | 0.773 | -0.218 [-0.282; -0.098] | 26 | 0.218 | consistent drop |
| DENSE_AQV32_16 | DDoS-SlowLoris | 0.074 | 0.033 | -0.023 [-0.037; -0.009] | 6 | 0.044 | floor |
| DENSE_AQV32_16 | DDoS-SynonymousIP_Flood | 0.996 | 0.806 | -0.189 [-0.282; -0.066] | 22 | 0.189 | – |
| DENSE_AQV32_16 | DDoS-TCP_Flood | 0.998 | 0.879 | -0.116 [-0.268; -0.055] | 21 | 0.116 | – |
| DENSE_AQV32_16 | DDoS-UDP_Flood | 0.001 | 0.001 | +0.000 [-0.000; +0.004] | 1 | 0.006 | floor |
| DENSE_AQV32_16 | DDoS-UDP_Fragmentation | 0.976 | 0.974 | -0.003 [-0.003; -0.002] | 0 | 0.004 | – |
| DENSE_AQV32_16 | Mirai-greeth_flood | 0.959 | 0.958 | -0.001 [-0.001; -0.000] | 0 | 0.002 | – |
| DENSE_AQV32_16 | Mirai-greip_flood | 0.961 | 0.957 | -0.003 [-0.004; -0.002] | 0 | 0.005 | – |
| DENSE_AQV32_16 | Mirai-udpplain | 0.002 | 0.002 | +0.000 [-0.001; +0.006] | 0 | 0.004 | floor |
| DENSE_AQV32_16 | normal | 0.009 | 0.012 | +0.003 [+0.000; +0.007] | 1 | 0.017 | FPR |

## K2 Key Patterns (Pi, Median of 3 Units)

### edge_iiotset

| key | spikes_per_sample_mean | spikes_per_sample_median | test_seen_in_val | top10_coverage | top100_coverage | top1000_coverage |
|---|---|---|---|---|---|---|
| count | 38.369 | 41.000 | 0.497 | 0.332 | 0.509 | 0.745 |
| exact | 38.369 | 41.000 | 0.460 | 0.317 | 0.470 | 0.671 |
| tri | 38.369 | 41.000 | 0.549 | 0.344 | 0.558 | 0.855 |

### ciciot2023

| key | spikes_per_sample_mean | spikes_per_sample_median | test_seen_in_val | top10_coverage | top100_coverage | top1000_coverage |
|---|---|---|---|---|---|---|
| count | 31.691 | 28.000 | 0.320 | 0.195 | 0.439 | 0.738 |
| exact | 31.691 | 28.000 | 0.274 | 0.188 | 0.399 | 0.643 |
| tri | 31.691 | 28.000 | 0.350 | 0.203 | 0.454 | 0.785 |

## K3 PMU Counters (Pi, Median of 3 Units)

### edge_iiotset

| variant | cycles_per_sample | instructions_per_sample | l1d_access_per_sample | l1d_refill_per_sample | mem_access_per_sample | ipc | l1d_refill_per_kinstr |
|---|---|---|---|---|---|---|---|
| DENSE | 1970.768 | 7085.527 | 2623.765 | 1.339 | 2623.764 | 3.599 | 0.189 |
| DENSE_AQV32_16 | 656.658 | 1735.257 | 716.805 | 2.263 | 716.805 | 2.637 | 1.315 |
| DENSE_AQV33_16 | 762.977 | 1948.144 | 818.596 | 2.934 | 818.596 | 2.553 | 1.518 |
| DENSE_ZS | 1636.415 | 5909.889 | 2115.196 | 1.307 | 2115.196 | 3.557 | 0.221 |
| SNN_COUNT | 3740.814 | 10823.857 | 4074.742 | 1.329 | 4074.742 | 2.919 | 0.123 |
| SNN_MEMOV3_16 | 750.432 | 1718.798 | 779.429 | 3.064 | 779.429 | 2.290 | 1.790 |
| SNN_RQC_16 | 663.456 | 1537.854 | 699.230 | 2.937 | 699.230 | 2.298 | 1.910 |
| SNN_RQT_16 | 609.262 | 1430.859 | 654.500 | 2.732 | 654.499 | 2.356 | 1.909 |

### ciciot2023

| variant | cycles_per_sample | instructions_per_sample | l1d_access_per_sample | l1d_refill_per_sample | mem_access_per_sample | ipc | l1d_refill_per_kinstr |
|---|---|---|---|---|---|---|---|
| DENSE | 2003.743 | 7127.569 | 2651.538 | 1.260 | 2651.538 | 3.557 | 0.177 |
| DENSE_AQV32_16 | 667.160 | 1748.147 | 725.181 | 2.247 | 725.181 | 2.617 | 1.276 |
| DENSE_AQV33_16 | 779.810 | 1974.371 | 830.075 | 2.788 | 830.075 | 2.531 | 1.451 |
| DENSE_ZS | 1551.493 | 5427.920 | 1946.592 | 1.261 | 1946.592 | 3.499 | 0.236 |
| SNN_COUNT | 3291.694 | 10035.618 | 3593.678 | 1.317 | 3593.678 | 3.009 | 0.133 |
| SNN_MEMOV3_16 | 630.768 | 1443.214 | 665.667 | 2.678 | 665.667 | 2.288 | 1.832 |
| SNN_RQC_16 | 583.774 | 1368.295 | 628.318 | 2.458 | 628.318 | 2.337 | 1.790 |
| SNN_RQT_16 | 563.412 | 1339.794 | 616.692 | 2.364 | 616.692 | 2.366 | 1.758 |

## K4 Cache Capacity (Pi, Median of 3 Units)

### edge_iiotset

| variant | ns_median | ratio_vs_dense_zs | hit_rate |
|---|---|---|---|
| DENSE_AQV32_12 | 281.298 | 0.405 | 0.958 |
| DENSE_AQV32_14 | 279.026 | 0.401 | 0.971 |
| DENSE_AQV32_16 | 279.640 | 0.402 | 0.973 |
| DENSE_AQV33_12 | 338.658 | 0.496 | 0.817 |
| DENSE_AQV33_14 | 323.456 | 0.471 | 0.884 |
| DENSE_AQV33_16 | 324.178 | 0.472 | 0.903 |
| DENSE_ZS | 685.163 | 1.000 | nan |
| SNN_MEMOV3_12 | 339.320 | 0.497 | 0.693 |
| SNN_MEMOV3_14 | 317.773 | 0.465 | 0.783 |
| SNN_MEMOV3_16 | 315.004 | 0.461 | 0.825 |
| SNN_RQC_12 | 300.623 | 0.440 | 0.792 |
| SNN_RQC_14 | 283.577 | 0.414 | 0.864 |
| SNN_RQC_16 | 282.773 | 0.414 | 0.890 |
| SNN_RQT_12 | 269.211 | 0.394 | 0.866 |
| SNN_RQT_14 | 256.827 | 0.376 | 0.912 |
| SNN_RQT_16 | 256.560 | 0.375 | 0.925 |

### ciciot2023

| variant | ns_median | ratio_vs_dense_zs | hit_rate |
|---|---|---|---|
| DENSE_AQV32_12 | 280.626 | 0.434 | 0.940 |
| DENSE_AQV32_14 | 278.275 | 0.431 | 0.954 |
| DENSE_AQV32_16 | 279.171 | 0.432 | 0.959 |
| DENSE_AQV33_12 | 323.565 | 0.500 | 0.807 |
| DENSE_AQV33_14 | 319.610 | 0.494 | 0.848 |
| DENSE_AQV33_16 | 324.500 | 0.501 | 0.865 |
| DENSE_ZS | 646.939 | 1.000 | nan |
| SNN_MEMOV3_12 | 262.992 | 0.409 | 0.834 |
| SNN_MEMOV3_14 | 258.334 | 0.404 | 0.872 |
| SNN_MEMOV3_16 | 262.559 | 0.412 | 0.883 |
| SNN_RQC_12 | 243.541 | 0.382 | 0.890 |
| SNN_RQC_14 | 241.243 | 0.379 | 0.915 |
| SNN_RQC_16 | 243.109 | 0.382 | 0.923 |
| SNN_RQT_12 | 236.291 | 0.369 | 0.911 |
| SNN_RQT_14 | 234.336 | 0.367 | 0.931 |
| SNN_RQT_16 | 236.613 | 0.370 | 0.936 |

## K2 Per Traffic Class, s0_f0 (edge_iiotset)

| class | n | variant | ns_median | hit_rate | spikes_enc_per_sample | exact_unique_test | exact_test_seen_in_val |
|---|---|---|---|---|---|---|---|
| ddos-http-flood-attacks | 4250 | DENSE_ZS | 730.288 | nan | 0.000 | 1199 | 0.000 |
| ddos-http-flood-attacks | 4250 | DENSE_AQV33_16 | 493.072 | 0.604 | 20.604 | 1199 | 0.000 |
| ddos-http-flood-attacks | 4250 | SNN_MEMOV3_16 | 377.922 | 0.716 | 45.403 | 1199 | 0.000 |
| ddos-http-flood-attacks | 4250 | SNN_RQT_16 | 306.549 | 0.841 | 45.403 | 1199 | 0.000 |
| ddos-icmp-flood-attacks | 4250 | DENSE_ZS | 561.420 | nan | 0.000 | 48 | 0.000 |
| ddos-icmp-flood-attacks | 4250 | DENSE_AQV33_16 | 260.592 | 0.998 | 12.254 | 48 | 0.000 |
| ddos-icmp-flood-attacks | 4250 | SNN_MEMOV3_16 | 220.458 | 0.989 | 26.873 | 48 | 0.000 |
| ddos-icmp-flood-attacks | 4250 | SNN_RQT_16 | 218.388 | 0.995 | 26.873 | 48 | 0.000 |
| ddos-tcp-syn-flood-attacks | 4250 | DENSE_ZS | 700.087 | nan | 0.000 | 367 | 0.000 |
| ddos-tcp-syn-flood-attacks | 4250 | DENSE_AQV33_16 | 281.686 | 0.963 | 22.043 | 367 | 0.000 |
| ddos-tcp-syn-flood-attacks | 4250 | SNN_MEMOV3_16 | 280.519 | 0.842 | 34.402 | 367 | 0.000 |
| ddos-tcp-syn-flood-attacks | 4250 | SNN_RQT_16 | 257.913 | 0.890 | 34.402 | 367 | 0.000 |
| ddos-udp-flood-attacks | 4250 | DENSE_ZS | 678.824 | nan | 0.000 | 117 | 0.000 |
| ddos-udp-flood-attacks | 4250 | DENSE_AQV33_16 | 275.481 | 0.974 | 20.276 | 117 | 0.000 |
| ddos-udp-flood-attacks | 4250 | SNN_MEMOV3_16 | 227.612 | 0.972 | 23.879 | 117 | 0.000 |
| ddos-udp-flood-attacks | 4250 | SNN_RQT_16 | 221.381 | 0.990 | 23.879 | 117 | 0.000 |
| normal | 16747 | DENSE_ZS | 708.172 | nan | 0.000 | 7979 | 0.762 |
| normal | 16747 | DENSE_AQV33_16 | 367.997 | 0.859 | 21.845 | 7979 | 0.762 |
| normal | 16747 | SNN_MEMOV3_16 | 379.181 | 0.749 | 44.184 | 7979 | 0.762 |
| normal | 16747 | SNN_RQT_16 | 286.071 | 0.902 | 44.184 | 7979 | 0.762 |

## K4 Memory Footprint, s0_f0 (edge_iiotset)

| dataset | unit | variant | logcap | analytic_bytes | rss_before_kb | rss_after_alloc_kb | rss_after_prefill_kb | valid_slots_after_prefill | weights_bytes_snn | weights_bytes_dense |
|---|---|---|---|---|---|---|---|---|---|---|
| edge_iiotset | s0_f0 | SNN_MEMOV3 | 12 | 606208 | 194128 | 194128 | 194128 | 3846 | 12932 | 13188 |
| edge_iiotset | s0_f0 | SNN_MEMOV3 | 14 | 2424832 | 194176 | 194176 | 194176 | 8250 | 12932 | 13188 |
| edge_iiotset | s0_f0 | SNN_MEMOV3 | 16 | 9699328 | 194176 | 194192 | 202624 | 10539 | 12932 | 13188 |
| edge_iiotset | s0_f0 | SNN_MEMOV3 | 18 | 38797312 | 194176 | 194192 | 227840 | 11197 | 12932 | 13188 |
| edge_iiotset | s0_f0 | SNN_MEMOV3 | 20 | 155189248 | 194176 | 194208 | 311168 | 11403 | 12932 | 13188 |
| edge_iiotset | s0_f0 | SNN_RQT | 12 | 606208 | 194176 | 194176 | 194192 | 2605 | 12932 | 13188 |
| edge_iiotset | s0_f0 | SNN_RQT | 14 | 2424832 | 194192 | 194192 | 194192 | 3678 | 12932 | 13188 |
| edge_iiotset | s0_f0 | SNN_RQT | 16 | 9699328 | 194192 | 194240 | 198656 | 3978 | 12932 | 13188 |
| edge_iiotset | s0_f0 | SNN_RQT | 18 | 38797312 | 198656 | 198672 | 227776 | 4085 | 12932 | 13188 |
| edge_iiotset | s0_f0 | SNN_RQT | 20 | 155189248 | 198656 | 198720 | 258320 | 4108 | 12932 | 13188 |
| edge_iiotset | s0_f0 | DENSE_AQV33 | 12 | 606208 | 205440 | 205440 | 205440 | 3393 | 12932 | 13188 |
| edge_iiotset | s0_f0 | DENSE_AQV33 | 14 | 2424832 | 205440 | 205440 | 205440 | 5930 | 12932 | 13188 |
| edge_iiotset | s0_f0 | DENSE_AQV33 | 16 | 9699328 | 205440 | 205440 | 205440 | 6950 | 12932 | 13188 |
| edge_iiotset | s0_f0 | DENSE_AQV33 | 18 | 38797312 | 205440 | 205456 | 238144 | 7250 | 12932 | 13188 |
| edge_iiotset | s0_f0 | DENSE_AQV33 | 20 | 155189248 | 205440 | 205584 | 284112 | 7332 | 12932 | 13188 |

## K2 Per Traffic Class, s0_f0 (ciciot2023)

| class | n | variant | ns_median | hit_rate | spikes_enc_per_sample | exact_unique_test | exact_test_seen_in_val |
|---|---|---|---|---|---|---|---|
| DDoS-ACK_Fragmentation | 4250 | DENSE_ZS | 596.065 | nan | 0.000 | 129 | 0.009 |
| DDoS-ACK_Fragmentation | 4250 | DENSE_AQV33_16 | 291.686 | 0.927 | 15.496 | 129 | 0.009 |
| DDoS-ACK_Fragmentation | 4250 | SNN_MEMOV3_16 | 227.860 | 0.976 | 32.684 | 129 | 0.009 |
| DDoS-ACK_Fragmentation | 4250 | SNN_RQT_16 | 235.900 | 0.930 | 32.684 | 129 | 0.009 |
| DDoS-HTTP_Flood- | 4250 | DENSE_ZS | 682.684 | nan | 0.000 | 1754 | 0.438 |
| DDoS-HTTP_Flood- | 4250 | DENSE_AQV33_16 | 392.867 | 0.784 | 20.171 | 1754 | 0.438 |
| DDoS-HTTP_Flood- | 4250 | SNN_MEMOV3_16 | 371.852 | 0.716 | 30.549 | 1754 | 0.438 |
| DDoS-HTTP_Flood- | 4250 | SNN_RQT_16 | 310.728 | 0.844 | 30.549 | 1754 | 0.438 |
| DDoS-ICMP_Flood | 4250 | DENSE_ZS | 609.037 | nan | 0.000 | 33 | 0.001 |
| DDoS-ICMP_Flood | 4250 | DENSE_AQV33_16 | 261.481 | 0.994 | 18.813 | 33 | 0.001 |
| DDoS-ICMP_Flood | 4250 | SNN_MEMOV3_16 | 226.187 | 0.957 | 19.820 | 33 | 0.001 |
| DDoS-ICMP_Flood | 4250 | SNN_RQT_16 | 216.244 | 0.996 | 19.820 | 33 | 0.001 |
| DDoS-ICMP_Fragmentation | 4250 | DENSE_ZS | 601.490 | nan | 0.000 | 186 | 0.026 |
| DDoS-ICMP_Fragmentation | 4250 | DENSE_AQV33_16 | 275.787 | 0.977 | 16.994 | 186 | 0.026 |
| DDoS-ICMP_Fragmentation | 4250 | SNN_MEMOV3_16 | 230.109 | 0.977 | 40.292 | 186 | 0.026 |
| DDoS-ICMP_Fragmentation | 4250 | SNN_RQT_16 | 227.896 | 0.981 | 40.292 | 186 | 0.026 |
| DDoS-PSHACK_Flood | 4250 | DENSE_ZS | 692.196 | nan | 0.000 | 1833 | 0.001 |
| DDoS-PSHACK_Flood | 4250 | DENSE_AQV33_16 | 535.691 | 0.476 | 14.600 | 1833 | 0.001 |
| DDoS-PSHACK_Flood | 4250 | SNN_MEMOV3_16 | 405.072 | 0.565 | 18.075 | 1833 | 0.001 |
| DDoS-PSHACK_Flood | 4250 | SNN_RQT_16 | 330.863 | 0.742 | 18.075 | 1833 | 0.001 |
| DDoS-RSTFINFlood | 4250 | DENSE_ZS | 667.560 | nan | 0.000 | 910 | 0.002 |
| DDoS-RSTFINFlood | 4250 | DENSE_AQV33_16 | 549.935 | 0.425 | 9.476 | 910 | 0.002 |
| DDoS-RSTFINFlood | 4250 | SNN_MEMOV3_16 | 308.571 | 0.787 | 16.617 | 910 | 0.002 |
| DDoS-RSTFINFlood | 4250 | SNN_RQT_16 | 259.351 | 0.906 | 16.617 | 910 | 0.002 |
| DDoS-SYN_Flood | 4250 | DENSE_ZS | 692.606 | nan | 0.000 | 848 | 0.013 |
| DDoS-SYN_Flood | 4250 | DENSE_AQV33_16 | 472.980 | 0.596 | 15.926 | 848 | 0.013 |
| DDoS-SYN_Flood | 4250 | SNN_MEMOV3_16 | 314.279 | 0.802 | 23.746 | 848 | 0.013 |
| DDoS-SYN_Flood | 4250 | SNN_RQT_16 | 265.921 | 0.903 | 23.746 | 848 | 0.013 |
| DDoS-SlowLoris | 4250 | DENSE_ZS | 692.662 | nan | 0.000 | 2044 | 0.365 |
| DDoS-SlowLoris | 4250 | DENSE_AQV33_16 | 431.438 | 0.730 | 21.578 | 2044 | 0.365 |
| DDoS-SlowLoris | 4250 | SNN_MEMOV3_16 | 407.264 | 0.657 | 31.852 | 2044 | 0.365 |
| DDoS-SlowLoris | 4250 | SNN_RQT_16 | 336.710 | 0.805 | 31.852 | 2044 | 0.365 |
| DDoS-SynonymousIP_Flood | 4250 | DENSE_ZS | 681.760 | nan | 0.000 | 740 | 0.000 |
| DDoS-SynonymousIP_Flood | 4250 | DENSE_AQV33_16 | 466.980 | 0.602 | 15.588 | 740 | 0.000 |
| DDoS-SynonymousIP_Flood | 4250 | SNN_MEMOV3_16 | 300.462 | 0.823 | 23.576 | 740 | 0.000 |
| DDoS-SynonymousIP_Flood | 4250 | SNN_RQT_16 | 251.638 | 0.925 | 23.576 | 740 | 0.000 |
| DDoS-TCP_Flood | 4250 | DENSE_ZS | 720.658 | nan | 0.000 | 1528 | 0.001 |
| DDoS-TCP_Flood | 4250 | DENSE_AQV33_16 | 645.538 | 0.316 | 13.725 | 1528 | 0.001 |
| DDoS-TCP_Flood | 4250 | SNN_MEMOV3_16 | 374.261 | 0.638 | 12.888 | 1528 | 0.001 |
| DDoS-TCP_Flood | 4250 | SNN_RQT_16 | 308.701 | 0.795 | 12.888 | 1528 | 0.001 |
| DDoS-UDP_Flood | 4250 | DENSE_ZS | 625.028 | nan | 0.000 | 950 | 0.092 |
| DDoS-UDP_Flood | 4250 | DENSE_AQV33_16 | 338.588 | 0.837 | 13.384 | 950 | 0.092 |
| DDoS-UDP_Flood | 4250 | SNN_MEMOV3_16 | 310.854 | 0.795 | 26.871 | 950 | 0.092 |
| DDoS-UDP_Flood | 4250 | SNN_RQT_16 | 261.935 | 0.902 | 26.871 | 950 | 0.092 |
| DDoS-UDP_Fragmentation | 4250 | DENSE_ZS | 585.020 | nan | 0.000 | 117 | 0.012 |
| DDoS-UDP_Fragmentation | 4250 | DENSE_AQV33_16 | 271.717 | 0.982 | 15.136 | 117 | 0.012 |
| DDoS-UDP_Fragmentation | 4250 | SNN_MEMOV3_16 | 226.532 | 0.983 | 32.521 | 117 | 0.012 |
| DDoS-UDP_Fragmentation | 4250 | SNN_RQT_16 | 225.055 | 0.985 | 32.521 | 117 | 0.012 |
| Mirai-greeth_flood | 4250 | DENSE_ZS | 645.773 | nan | 0.000 | 1579 | 0.028 |
| Mirai-greeth_flood | 4250 | DENSE_AQV33_16 | 301.547 | 0.927 | 14.956 | 1579 | 0.028 |
| Mirai-greeth_flood | 4250 | SNN_MEMOV3_16 | 413.198 | 0.632 | 37.833 | 1579 | 0.028 |
| Mirai-greeth_flood | 4250 | SNN_RQT_16 | 284.619 | 0.884 | 37.833 | 1579 | 0.028 |
| Mirai-greip_flood | 4250 | DENSE_ZS | 645.351 | nan | 0.000 | 1663 | 0.022 |
| Mirai-greip_flood | 4250 | DENSE_AQV33_16 | 308.475 | 0.917 | 14.758 | 1663 | 0.022 |
| Mirai-greip_flood | 4250 | SNN_MEMOV3_16 | 424.200 | 0.620 | 37.792 | 1663 | 0.022 |
| Mirai-greip_flood | 4250 | SNN_RQT_16 | 284.126 | 0.872 | 37.792 | 1663 | 0.022 |
| Mirai-udpplain | 4250 | DENSE_ZS | 624.902 | nan | 0.000 | 237 | 0.008 |
| Mirai-udpplain | 4250 | DENSE_AQV33_16 | 274.305 | 0.970 | 13.900 | 237 | 0.008 |
| Mirai-udpplain | 4250 | SNN_MEMOV3_16 | 239.281 | 0.951 | 25.894 | 237 | 0.008 |
| Mirai-udpplain | 4250 | SNN_RQT_16 | 231.386 | 0.971 | 25.894 | 237 | 0.008 |
| normal | 64114 | DENSE_ZS | 655.767 | nan | 0.000 | 5549 | 0.444 |
| normal | 64114 | DENSE_AQV33_16 | 291.258 | 0.949 | 20.160 | 5549 | 0.444 |
| normal | 64114 | SNN_MEMOV3_16 | 239.400 | 0.957 | 29.930 | 5549 | 0.444 |
| normal | 64114 | SNN_RQT_16 | 226.907 | 0.969 | 29.930 | 5549 | 0.444 |

## K4 Memory Footprint, s0_f0 (ciciot2023)

| dataset | unit | variant | logcap | analytic_bytes | rss_before_kb | rss_after_alloc_kb | rss_after_prefill_kb | valid_slots_after_prefill | weights_bytes_snn | weights_bytes_dense |
|---|---|---|---|---|---|---|---|---|---|---|
| ciciot2023 | s0_f0 | SNN_MEMOV3 | 12 | 606208 | 232352 | 232352 | 232352 | 3463 | 12932 | 13188 |
| ciciot2023 | s0_f0 | SNN_MEMOV3 | 14 | 2424832 | 232400 | 232400 | 232400 | 6097 | 12932 | 13188 |
| ciciot2023 | s0_f0 | SNN_MEMOV3 | 16 | 9699328 | 232400 | 232400 | 232400 | 7168 | 12932 | 13188 |
| ciciot2023 | s0_f0 | SNN_MEMOV3 | 18 | 38797312 | 232400 | 232416 | 265328 | 7495 | 12932 | 13188 |
| ciciot2023 | s0_f0 | SNN_MEMOV3 | 20 | 155189248 | 232400 | 232416 | 312976 | 7577 | 12932 | 13188 |
| ciciot2023 | s0_f0 | SNN_RQT | 12 | 606208 | 232400 | 232400 | 232416 | 2585 | 12932 | 13188 |
| ciciot2023 | s0_f0 | SNN_RQT | 14 | 2424832 | 232416 | 232416 | 232416 | 3598 | 12932 | 13188 |
| ciciot2023 | s0_f0 | SNN_RQT | 16 | 9699328 | 232416 | 232416 | 232416 | 3928 | 12932 | 13188 |
| ciciot2023 | s0_f0 | SNN_RQT | 18 | 38797312 | 232416 | 232432 | 261616 | 4009 | 12932 | 13188 |
| ciciot2023 | s0_f0 | SNN_RQT | 20 | 155189248 | 232416 | 232432 | 284576 | 4033 | 12932 | 13188 |
| ciciot2023 | s0_f0 | DENSE_AQV33 | 12 | 606208 | 232416 | 232416 | 232416 | 3592 | 12932 | 13188 |
| ciciot2023 | s0_f0 | DENSE_AQV33 | 14 | 2424832 | 232416 | 232416 | 232416 | 6805 | 12932 | 13188 |
| ciciot2023 | s0_f0 | DENSE_AQV33 | 16 | 9699328 | 232416 | 232416 | 232416 | 8199 | 12932 | 13188 |
| ciciot2023 | s0_f0 | DENSE_AQV33 | 18 | 38797312 | 232416 | 232432 | 265568 | 8628 | 12932 | 13188 |
| ciciot2023 | s0_f0 | DENSE_AQV33 | 20 | 155189248 | 232416 | 232432 | 319344 | 8715 | 12932 | 13188 |
