# S7p Analysis Results (Automated)

Conditions: 384; valid: 384.

|                                          |   n |   valid |   idle_med |   idle_min |   idle_low |   rate_med |
|:-----------------------------------------|----:|--------:|-----------:|-----------:|-----------:|-----------:|
| ('S7g', 'ciciot2023', 'pipe (29 Oct)')   |  36 |      36 |      3.257 |      3.002 |         26 |     99.76  |
| ('S7g', 'edge_iiotset', 'pipe (29 Oct)') |  36 |      36 |      4.073 |      3.029 |         13 |     99.85  |
| ('S7g-more', 'ciciot2023', 'stream')     |  72 |      72 |      3.763 |      2.992 |         29 |    100.003 |
| ('S7g-more', 'edge_iiotset', 'stream')   |  72 |      72 |      3.897 |      2.984 |         28 |     99.98  |
| ('S7h', 'ciciot2023', 'stream')          |  30 |      30 |      4.085 |      3.866 |          0 |     99.996 |
| ('S7h', 'edge_iiotset', 'pipe')          |  30 |      30 |      4.082 |      3.186 |          3 |    100.757 |
| ('S7j', 'ciciot2023', 'pipe')            |  54 |      54 |      4.001 |      3.18  |         11 |     99.847 |
| ('S7j', 'edge_iiotset', 'pipe')          |  54 |      54 |      4.172 |      3.194 |          1 |     99.857 |

## S7g 9 Units (s0–s2 × f0–f2), Capture Order

|                                    |   n |    dE_nJ |   Eact_nJ |   lat_us |
|:-----------------------------------|----:|---------:|----------:|---------:|
| ('ciciot2023', 'DENSE_AQV22_16')   |  27 |  648.185 |   1694.82 |    0.301 |
| ('ciciot2023', 'DENSE_AQV23_16')   |  27 |  723.962 |   2008.56 |    0.351 |
| ('ciciot2023', 'DENSE_ZS')         |  27 | 1505.77  |   3719.32 |    0.643 |
| ('ciciot2023', 'SNN_MEMOV2_16')    |  27 |  697.614 |   1850.73 |    0.318 |
| ('edge_iiotset', 'DENSE_AQV22_16') |  27 |  660.288 |   1949.65 |    0.339 |
| ('edge_iiotset', 'DENSE_AQV23_16') |  27 |  776.362 |   2263.29 |    0.385 |
| ('edge_iiotset', 'DENSE_ZS')       |  27 | 1555.32  |   4081.85 |    0.699 |
| ('edge_iiotset', 'SNN_MEMOV2_16')  |  27 |  831.071 |   2567.03 |    0.441 |

## S7g 9 Units: Dominance (S7g §4 Rule)


### ΔE (Primary)

| dataset      | snn           | dense          | metric   |   acc_snn |   acc_dense |   ratio | snn_cheaper   |   need | relation              |
|:-------------|:--------------|:---------------|:---------|----------:|------------:|--------:|:--------------|-------:|:----------------------|
| edge_iiotset | SNN_MEMOV2_16 | DENSE_ZS       | auc      |    0.9995 |      0.9997 |   0.568 | 27/27         |     24 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV2_16 | DENSE_ZS       | f1_p99   |    0.9948 |      0.9961 |   0.568 | 27/27         |     24 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV2_16 | DENSE_AQV22_16 | auc      |    0.9995 |      0.9982 |   1.288 | 3/27          |     24 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV2_16 | DENSE_AQV22_16 | f1_p99   |    0.9948 |      0.9798 |   1.288 | 3/27          |     24 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV2_16 | DENSE_AQV23_16 | auc      |    0.9995 |      0.9996 |   1.149 | 4/27          |     24 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV2_16 | DENSE_AQV23_16 | f1_p99   |    0.9948 |      0.9954 |   1.149 | 4/27          |     24 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV2_16 | DENSE_ZS       | auc      |    0.9135 |      0.8942 |   0.48  | 27/27         |     24 | SNN dominates       |
| ciciot2023   | SNN_MEMOV2_16 | DENSE_ZS       | f1_p99   |    0.808  |      0.839  |   0.48  | 27/27         |     24 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV2_16 | DENSE_AQV22_16 | auc      |    0.9135 |      0.8409 |   1.104 | 7/27          |     24 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV2_16 | DENSE_AQV22_16 | f1_p99   |    0.808  |      0.773  |   1.104 | 7/27          |     24 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV2_16 | DENSE_AQV23_16 | auc      |    0.9135 |      0.8644 |   0.974 | 17/27         |     24 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV2_16 | DENSE_AQV23_16 | f1_p99   |    0.808  |      0.8295 |   0.974 | 17/27         |     24 | trade-off/inconclusive |

### E_active (Sensitivity)

| dataset      | snn           | dense          | metric   |   acc_snn |   acc_dense |   ratio | snn_cheaper   |   need | relation              |
|:-------------|:--------------|:---------------|:---------|----------:|------------:|--------:|:--------------|-------:|:----------------------|
| edge_iiotset | SNN_MEMOV2_16 | DENSE_ZS       | auc      |    0.9995 |      0.9997 |   0.621 | 27/27         |     24 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV2_16 | DENSE_ZS       | f1_p99   |    0.9948 |      0.9961 |   0.621 | 27/27         |     24 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV2_16 | DENSE_AQV22_16 | auc      |    0.9995 |      0.9982 |   1.308 | 0/27          |     24 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV2_16 | DENSE_AQV22_16 | f1_p99   |    0.9948 |      0.9798 |   1.308 | 0/27          |     24 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV2_16 | DENSE_AQV23_16 | auc      |    0.9995 |      0.9996 |   1.135 | 0/27          |     24 | Dense dominates     |
| edge_iiotset | SNN_MEMOV2_16 | DENSE_AQV23_16 | f1_p99   |    0.9948 |      0.9954 |   1.135 | 0/27          |     24 | Dense dominates     |
| ciciot2023   | SNN_MEMOV2_16 | DENSE_ZS       | auc      |    0.9135 |      0.8942 |   0.503 | 27/27         |     24 | SNN dominates       |
| ciciot2023   | SNN_MEMOV2_16 | DENSE_ZS       | f1_p99   |    0.808  |      0.839  |   0.503 | 27/27         |     24 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV2_16 | DENSE_AQV22_16 | auc      |    0.9135 |      0.8409 |   1.092 | 4/27          |     24 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV2_16 | DENSE_AQV22_16 | f1_p99   |    0.808  |      0.773  |   1.092 | 4/27          |     24 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV2_16 | DENSE_AQV23_16 | auc      |    0.9135 |      0.8644 |   0.931 | 19/27         |     24 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV2_16 | DENSE_AQV23_16 | f1_p99   |    0.808  |      0.8295 |   0.931 | 19/27         |     24 | trade-off/inconclusive |

### ΔE Excluding idle < 3.6 W (Sensitivity)

| dataset      | snn           | dense          | metric   |   acc_snn |   acc_dense |   ratio | snn_cheaper   |   need | relation              |
|:-------------|:--------------|:---------------|:---------|----------:|------------:|--------:|:--------------|-------:|:----------------------|
| edge_iiotset | SNN_MEMOV2_16 | DENSE_ZS       | auc      |    0.9995 |      0.9997 |   0.579 | 14/14         |     13 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV2_16 | DENSE_ZS       | f1_p99   |    0.9948 |      0.9961 |   0.579 | 14/14         |     13 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV2_16 | DENSE_AQV22_16 | auc      |    0.9995 |      0.9982 |   1.295 | 0/15          |     14 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV2_16 | DENSE_AQV22_16 | f1_p99   |    0.9948 |      0.9798 |   1.295 | 0/15          |     14 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV2_16 | DENSE_AQV23_16 | auc      |    0.9995 |      0.9996 |   1.106 | 0/15          |     14 | Dense dominates     |
| edge_iiotset | SNN_MEMOV2_16 | DENSE_AQV23_16 | f1_p99   |    0.9948 |      0.9954 |   1.106 | 0/15          |     14 | Dense dominates     |
| ciciot2023   | SNN_MEMOV2_16 | DENSE_ZS       | auc      |    0.9135 |      0.8942 |   0.484 | 9/9           |      8 | SNN dominates       |
| ciciot2023   | SNN_MEMOV2_16 | DENSE_ZS       | f1_p99   |    0.808  |      0.839  |   0.484 | 9/9           |      8 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV2_16 | DENSE_AQV22_16 | auc      |    0.9135 |      0.8409 |   1.124 | 0/7           |      7 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV2_16 | DENSE_AQV22_16 | f1_p99   |    0.808  |      0.773  |   1.124 | 0/7           |      7 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV2_16 | DENSE_AQV23_16 | auc      |    0.9135 |      0.8644 |   0.944 | 9/11          |     10 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV2_16 | DENSE_AQV23_16 | f1_p99   |    0.808  |      0.8295 |   0.944 | 9/11          |     10 | trade-off/inconclusive |

## S7g-more Only (6 Units, Stream): Dominance (S7g §4 Rule)


### ΔE (Primary)

| dataset      | snn           | dense          | metric   |   acc_snn |   acc_dense |   ratio | snn_cheaper   |   need | relation              |
|:-------------|:--------------|:---------------|:---------|----------:|------------:|--------:|:--------------|-------:|:----------------------|
| edge_iiotset | SNN_MEMOV2_16 | DENSE_ZS       | auc      |    0.9995 |      0.9997 |   0.567 | 18/18         |     16 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV2_16 | DENSE_ZS       | f1_p99   |    0.9948 |      0.9961 |   0.567 | 18/18         |     16 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV2_16 | DENSE_AQV22_16 | auc      |    0.9995 |      0.9982 |   1.267 | 3/18          |     16 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV2_16 | DENSE_AQV22_16 | f1_p99   |    0.9948 |      0.9798 |   1.267 | 3/18          |     16 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV2_16 | DENSE_AQV23_16 | auc      |    0.9995 |      0.9996 |   1.133 | 2/18          |     16 | Dense dominates     |
| edge_iiotset | SNN_MEMOV2_16 | DENSE_AQV23_16 | f1_p99   |    0.9948 |      0.9954 |   1.133 | 2/18          |     16 | Dense dominates     |
| ciciot2023   | SNN_MEMOV2_16 | DENSE_ZS       | auc      |    0.9135 |      0.8942 |   0.493 | 18/18         |     16 | SNN dominates       |
| ciciot2023   | SNN_MEMOV2_16 | DENSE_ZS       | f1_p99   |    0.808  |      0.839  |   0.493 | 18/18         |     16 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV2_16 | DENSE_AQV22_16 | auc      |    0.9135 |      0.8409 |   1.132 | 5/18          |     16 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV2_16 | DENSE_AQV22_16 | f1_p99   |    0.808  |      0.773  |   1.132 | 5/18          |     16 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV2_16 | DENSE_AQV23_16 | auc      |    0.9135 |      0.8644 |   0.949 | 11/18         |     16 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV2_16 | DENSE_AQV23_16 | f1_p99   |    0.808  |      0.8295 |   0.949 | 11/18         |     16 | trade-off/inconclusive |

### E_active (Sensitivity)

| dataset      | snn           | dense          | metric   |   acc_snn |   acc_dense |   ratio | snn_cheaper   |   need | relation              |
|:-------------|:--------------|:---------------|:---------|----------:|------------:|--------:|:--------------|-------:|:----------------------|
| edge_iiotset | SNN_MEMOV2_16 | DENSE_ZS       | auc      |    0.9995 |      0.9997 |   0.61  | 18/18         |     16 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV2_16 | DENSE_ZS       | f1_p99   |    0.9948 |      0.9961 |   0.61  | 18/18         |     16 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV2_16 | DENSE_AQV22_16 | auc      |    0.9995 |      0.9982 |   1.302 | 0/18          |     16 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV2_16 | DENSE_AQV22_16 | f1_p99   |    0.9948 |      0.9798 |   1.302 | 0/18          |     16 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV2_16 | DENSE_AQV23_16 | auc      |    0.9995 |      0.9996 |   1.146 | 0/18          |     16 | Dense dominates     |
| edge_iiotset | SNN_MEMOV2_16 | DENSE_AQV23_16 | f1_p99   |    0.9948 |      0.9954 |   1.146 | 0/18          |     16 | Dense dominates     |
| ciciot2023   | SNN_MEMOV2_16 | DENSE_ZS       | auc      |    0.9135 |      0.8942 |   0.509 | 18/18         |     16 | SNN dominates       |
| ciciot2023   | SNN_MEMOV2_16 | DENSE_ZS       | f1_p99   |    0.808  |      0.839  |   0.509 | 18/18         |     16 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV2_16 | DENSE_AQV22_16 | auc      |    0.9135 |      0.8409 |   1.139 | 3/18          |     16 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV2_16 | DENSE_AQV22_16 | f1_p99   |    0.808  |      0.773  |   1.139 | 3/18          |     16 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV2_16 | DENSE_AQV23_16 | auc      |    0.9135 |      0.8644 |   0.944 | 11/18         |     16 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV2_16 | DENSE_AQV23_16 | f1_p99   |    0.808  |      0.8295 |   0.944 | 11/18         |     16 | trade-off/inconclusive |

### ΔE Excluding idle < 3.6 W (Sensitivity)

| dataset      | snn           | dense          | metric   |   acc_snn |   acc_dense |   ratio | snn_cheaper   |   need | relation              |
|:-------------|:--------------|:---------------|:---------|----------:|------------:|--------:|:--------------|-------:|:----------------------|
| edge_iiotset | SNN_MEMOV2_16 | DENSE_ZS       | auc      |    0.9995 |      0.9997 |   0.575 | 9/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV2_16 | DENSE_ZS       | f1_p99   |    0.9948 |      0.9961 |   0.575 | 9/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV2_16 | DENSE_AQV22_16 | auc      |    0.9995 |      0.9982 |   1.267 | 0/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV2_16 | DENSE_AQV22_16 | f1_p99   |    0.9948 |      0.9798 |   1.267 | 0/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV2_16 | DENSE_AQV23_16 | auc      |    0.9995 |      0.9996 |   1.084 | 0/10          |      9 | Dense dominates     |
| edge_iiotset | SNN_MEMOV2_16 | DENSE_AQV23_16 | f1_p99   |    0.9948 |      0.9954 |   1.084 | 0/10          |      9 | Dense dominates     |
| ciciot2023   | SNN_MEMOV2_16 | DENSE_ZS       | auc      |    0.9135 |      0.8942 |   0.486 | 7/7           |      7 | SNN dominates       |
| ciciot2023   | SNN_MEMOV2_16 | DENSE_ZS       | f1_p99   |    0.808  |      0.839  |   0.486 | 7/7           |      7 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV2_16 | DENSE_AQV22_16 | auc      |    0.9135 |      0.8409 |   1.114 | 0/6           |      6 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV2_16 | DENSE_AQV22_16 | f1_p99   |    0.808  |      0.773  |   1.114 | 0/6           |      6 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV2_16 | DENSE_AQV23_16 | auc      |    0.9135 |      0.8644 |   0.917 | 7/9           |      8 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV2_16 | DENSE_AQV23_16 | f1_p99   |    0.808  |      0.8295 |   0.917 | 7/9           |      8 | trade-off/inconclusive |

## S7j (s0–s2_f0)

|                                    |   n |    dE_nJ |   Eact_nJ |   lat_us |
|:-----------------------------------|----:|---------:|----------:|---------:|
| ('ciciot2023', 'DENSE_AQV32_16')   |   9 |  577.115 |   1727.13 |    0.296 |
| ('ciciot2023', 'DENSE_AQV33_16')   |   9 |  618.412 |   2033.78 |    0.343 |
| ('ciciot2023', 'DENSE_ZS')         |   9 | 1256.19  |   3886.58 |    0.651 |
| ('ciciot2023', 'SNN_MEMOV3_16')    |   9 |  580.04  |   1695.02 |    0.282 |
| ('ciciot2023', 'SNN_RQC_16')       |   9 |  534.753 |   1578.87 |    0.261 |
| ('ciciot2023', 'SNN_RQT_16')       |   9 |  514.607 |   1538.3  |    0.254 |
| ('edge_iiotset', 'DENSE_AQV32_16') |   9 |  591.041 |   2011.24 |    0.336 |
| ('edge_iiotset', 'DENSE_AQV33_16') |   9 |  700.536 |   2277.34 |    0.381 |
| ('edge_iiotset', 'DENSE_ZS')       |   9 | 1349.17  |   4167.81 |    0.686 |
| ('edge_iiotset', 'SNN_MEMOV3_16')  |   9 |  687.787 |   2261.62 |    0.373 |
| ('edge_iiotset', 'SNN_RQC_16')     |   9 |  647.979 |   2082.36 |    0.341 |
| ('edge_iiotset', 'SNN_RQT_16')     |   9 |  584.829 |   1926.99 |    0.315 |

## S7j: Dominance (S7g §4 Rule)


### ΔE (Primary)

| dataset      | snn           | dense          | metric   |   acc_snn |   acc_dense |   ratio | snn_cheaper   |   need | relation              |
|:-------------|:--------------|:---------------|:---------|----------:|------------:|--------:|:--------------|-------:|:----------------------|
| edge_iiotset | SNN_MEMOV3_16 | DENSE_ZS       | auc      |    0.9995 |      0.9997 |   0.517 | 9/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV3_16 | DENSE_ZS       | f1_p99   |    0.9948 |      0.9961 |   0.517 | 9/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV3_16 | DENSE_AQV32_16 | auc      |    0.9995 |      0.9982 |   1.143 | 0/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV3_16 | DENSE_AQV32_16 | f1_p99   |    0.9948 |      0.9798 |   1.143 | 0/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV3_16 | DENSE_AQV33_16 | auc      |    0.9995 |      0.9996 |   0.964 | 6/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV3_16 | DENSE_AQV33_16 | f1_p99   |    0.9948 |      0.9954 |   0.964 | 6/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_RQC_16    | DENSE_ZS       | auc      |    0.9995 |      0.9997 |   0.468 | 9/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_RQC_16    | DENSE_ZS       | f1_p99   |    0.9947 |      0.9961 |   0.468 | 9/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_RQC_16    | DENSE_AQV32_16 | auc      |    0.9995 |      0.9982 |   1.079 | 0/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_RQC_16    | DENSE_AQV32_16 | f1_p99   |    0.9947 |      0.9798 |   1.079 | 0/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_RQC_16    | DENSE_AQV33_16 | auc      |    0.9995 |      0.9996 |   0.899 | 8/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_RQC_16    | DENSE_AQV33_16 | f1_p99   |    0.9947 |      0.9954 |   0.899 | 8/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_RQT_16    | DENSE_ZS       | auc      |    0.9994 |      0.9997 |   0.423 | 9/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_RQT_16    | DENSE_ZS       | f1_p99   |    0.9944 |      0.9961 |   0.423 | 9/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_RQT_16    | DENSE_AQV32_16 | auc      |    0.9994 |      0.9982 |   0.992 | 5/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_RQT_16    | DENSE_AQV32_16 | f1_p99   |    0.9944 |      0.9798 |   0.992 | 5/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_RQT_16    | DENSE_AQV33_16 | auc      |    0.9994 |      0.9996 |   0.835 | 9/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_RQT_16    | DENSE_AQV33_16 | f1_p99   |    0.9944 |      0.9954 |   0.835 | 9/9           |      8 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV3_16 | DENSE_ZS       | auc      |    0.9135 |      0.8942 |   0.454 | 9/9           |      8 | SNN dominates       |
| ciciot2023   | SNN_MEMOV3_16 | DENSE_ZS       | f1_p99   |    0.808  |      0.839  |   0.454 | 9/9           |      8 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV3_16 | DENSE_AQV32_16 | auc      |    0.9135 |      0.8409 |   1.005 | 4/9           |      8 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV3_16 | DENSE_AQV32_16 | f1_p99   |    0.808  |      0.773  |   1.005 | 4/9           |      8 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV3_16 | DENSE_AQV33_16 | auc      |    0.9135 |      0.8644 |   0.881 | 6/9           |      8 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV3_16 | DENSE_AQV33_16 | f1_p99   |    0.808  |      0.8295 |   0.881 | 6/9           |      8 | trade-off/inconclusive |
| ciciot2023   | SNN_RQC_16    | DENSE_ZS       | auc      |    0.9068 |      0.8942 |   0.404 | 9/9           |      8 | SNN dominates       |
| ciciot2023   | SNN_RQC_16    | DENSE_ZS       | f1_p99   |    0.7756 |      0.839  |   0.404 | 9/9           |      8 | trade-off/inconclusive |
| ciciot2023   | SNN_RQC_16    | DENSE_AQV32_16 | auc      |    0.9068 |      0.8409 |   0.94  | 6/9           |      8 | trade-off/inconclusive |
| ciciot2023   | SNN_RQC_16    | DENSE_AQV32_16 | f1_p99   |    0.7756 |      0.773  |   0.94  | 6/9           |      8 | trade-off/inconclusive |
| ciciot2023   | SNN_RQC_16    | DENSE_AQV33_16 | auc      |    0.9068 |      0.8644 |   0.851 | 8/9           |      8 | SNN dominates       |
| ciciot2023   | SNN_RQC_16    | DENSE_AQV33_16 | f1_p99   |    0.7756 |      0.8295 |   0.851 | 8/9           |      8 | trade-off/inconclusive |
| ciciot2023   | SNN_RQT_16    | DENSE_ZS       | auc      |    0.8905 |      0.8942 |   0.395 | 9/9           |      8 | trade-off/inconclusive |
| ciciot2023   | SNN_RQT_16    | DENSE_ZS       | f1_p99   |    0.7505 |      0.839  |   0.395 | 9/9           |      8 | trade-off/inconclusive |
| ciciot2023   | SNN_RQT_16    | DENSE_AQV32_16 | auc      |    0.8905 |      0.8409 |   0.925 | 6/9           |      8 | trade-off/inconclusive |
| ciciot2023   | SNN_RQT_16    | DENSE_AQV32_16 | f1_p99   |    0.7505 |      0.773  |   0.925 | 6/9           |      8 | trade-off/inconclusive |
| ciciot2023   | SNN_RQT_16    | DENSE_AQV33_16 | auc      |    0.8905 |      0.8644 |   0.806 | 9/9           |      8 | SNN dominates       |
| ciciot2023   | SNN_RQT_16    | DENSE_AQV33_16 | f1_p99   |    0.7505 |      0.8295 |   0.806 | 9/9           |      8 | trade-off/inconclusive |

### E_active (Sensitivity)

| dataset      | snn           | dense          | metric   |   acc_snn |   acc_dense |   ratio | snn_cheaper   |   need | relation              |
|:-------------|:--------------|:---------------|:---------|----------:|------------:|--------:|:--------------|-------:|:----------------------|
| edge_iiotset | SNN_MEMOV3_16 | DENSE_ZS       | auc      |    0.9995 |      0.9997 |   0.546 | 9/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV3_16 | DENSE_ZS       | f1_p99   |    0.9948 |      0.9961 |   0.546 | 9/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV3_16 | DENSE_AQV32_16 | auc      |    0.9995 |      0.9982 |   1.127 | 0/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV3_16 | DENSE_AQV32_16 | f1_p99   |    0.9948 |      0.9798 |   1.127 | 0/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV3_16 | DENSE_AQV33_16 | auc      |    0.9995 |      0.9996 |   0.969 | 7/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV3_16 | DENSE_AQV33_16 | f1_p99   |    0.9948 |      0.9954 |   0.969 | 7/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_RQC_16    | DENSE_ZS       | auc      |    0.9995 |      0.9997 |   0.497 | 9/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_RQC_16    | DENSE_ZS       | f1_p99   |    0.9947 |      0.9961 |   0.497 | 9/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_RQC_16    | DENSE_AQV32_16 | auc      |    0.9995 |      0.9982 |   1.039 | 0/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_RQC_16    | DENSE_AQV32_16 | f1_p99   |    0.9947 |      0.9798 |   1.039 | 0/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_RQC_16    | DENSE_AQV33_16 | auc      |    0.9995 |      0.9996 |   0.9   | 9/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_RQC_16    | DENSE_AQV33_16 | f1_p99   |    0.9947 |      0.9954 |   0.9   | 9/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_RQT_16    | DENSE_ZS       | auc      |    0.9994 |      0.9997 |   0.463 | 9/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_RQT_16    | DENSE_ZS       | f1_p99   |    0.9944 |      0.9961 |   0.463 | 9/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_RQT_16    | DENSE_AQV32_16 | auc      |    0.9994 |      0.9982 |   0.945 | 9/9           |      8 | SNN dominates       |
| edge_iiotset | SNN_RQT_16    | DENSE_AQV32_16 | f1_p99   |    0.9944 |      0.9798 |   0.945 | 9/9           |      8 | SNN dominates       |
| edge_iiotset | SNN_RQT_16    | DENSE_AQV33_16 | auc      |    0.9994 |      0.9996 |   0.82  | 9/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_RQT_16    | DENSE_AQV33_16 | f1_p99   |    0.9944 |      0.9954 |   0.82  | 9/9           |      8 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV3_16 | DENSE_ZS       | auc      |    0.9135 |      0.8942 |   0.438 | 9/9           |      8 | SNN dominates       |
| ciciot2023   | SNN_MEMOV3_16 | DENSE_ZS       | f1_p99   |    0.808  |      0.839  |   0.438 | 9/9           |      8 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV3_16 | DENSE_AQV32_16 | auc      |    0.9135 |      0.8409 |   0.974 | 5/9           |      8 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV3_16 | DENSE_AQV32_16 | f1_p99   |    0.808  |      0.773  |   0.974 | 5/9           |      8 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV3_16 | DENSE_AQV33_16 | auc      |    0.9135 |      0.8644 |   0.835 | 9/9           |      8 | SNN dominates       |
| ciciot2023   | SNN_MEMOV3_16 | DENSE_AQV33_16 | f1_p99   |    0.808  |      0.8295 |   0.835 | 9/9           |      8 | trade-off/inconclusive |
| ciciot2023   | SNN_RQC_16    | DENSE_ZS       | auc      |    0.9068 |      0.8942 |   0.406 | 9/9           |      8 | SNN dominates       |
| ciciot2023   | SNN_RQC_16    | DENSE_ZS       | f1_p99   |    0.7756 |      0.839  |   0.406 | 9/9           |      8 | trade-off/inconclusive |
| ciciot2023   | SNN_RQC_16    | DENSE_AQV32_16 | auc      |    0.9068 |      0.8409 |   0.9   | 9/9           |      8 | SNN dominates       |
| ciciot2023   | SNN_RQC_16    | DENSE_AQV32_16 | f1_p99   |    0.7756 |      0.773  |   0.9   | 9/9           |      8 | SNN dominates       |
| ciciot2023   | SNN_RQC_16    | DENSE_AQV33_16 | auc      |    0.9068 |      0.8644 |   0.779 | 9/9           |      8 | SNN dominates       |
| ciciot2023   | SNN_RQC_16    | DENSE_AQV33_16 | f1_p99   |    0.7756 |      0.8295 |   0.779 | 9/9           |      8 | trade-off/inconclusive |
| ciciot2023   | SNN_RQT_16    | DENSE_ZS       | auc      |    0.8905 |      0.8942 |   0.392 | 9/9           |      8 | trade-off/inconclusive |
| ciciot2023   | SNN_RQT_16    | DENSE_ZS       | f1_p99   |    0.7505 |      0.839  |   0.392 | 9/9           |      8 | trade-off/inconclusive |
| ciciot2023   | SNN_RQT_16    | DENSE_AQV32_16 | auc      |    0.8905 |      0.8409 |   0.892 | 9/9           |      8 | SNN dominates       |
| ciciot2023   | SNN_RQT_16    | DENSE_AQV32_16 | f1_p99   |    0.7505 |      0.773  |   0.892 | 9/9           |      8 | trade-off/inconclusive |
| ciciot2023   | SNN_RQT_16    | DENSE_AQV33_16 | auc      |    0.8905 |      0.8644 |   0.754 | 9/9           |      8 | SNN dominates       |
| ciciot2023   | SNN_RQT_16    | DENSE_AQV33_16 | f1_p99   |    0.7505 |      0.8295 |   0.754 | 9/9           |      8 | trade-off/inconclusive |

### ΔE Excluding idle < 3.6 W (Sensitivity)

| dataset      | snn           | dense          | metric   |   acc_snn |   acc_dense |   ratio | snn_cheaper   |   need | relation              |
|:-------------|:--------------|:---------------|:---------|----------:|------------:|--------:|:--------------|-------:|:----------------------|
| edge_iiotset | SNN_MEMOV3_16 | DENSE_ZS       | auc      |    0.9995 |      0.9997 |   0.517 | 9/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV3_16 | DENSE_ZS       | f1_p99   |    0.9948 |      0.9961 |   0.517 | 9/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV3_16 | DENSE_AQV32_16 | auc      |    0.9995 |      0.9982 |   1.143 | 0/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV3_16 | DENSE_AQV32_16 | f1_p99   |    0.9948 |      0.9798 |   1.143 | 0/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV3_16 | DENSE_AQV33_16 | auc      |    0.9995 |      0.9996 |   0.982 | 5/8           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_MEMOV3_16 | DENSE_AQV33_16 | f1_p99   |    0.9948 |      0.9954 |   0.982 | 5/8           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_RQC_16    | DENSE_ZS       | auc      |    0.9995 |      0.9997 |   0.468 | 9/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_RQC_16    | DENSE_ZS       | f1_p99   |    0.9947 |      0.9961 |   0.468 | 9/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_RQC_16    | DENSE_AQV32_16 | auc      |    0.9995 |      0.9982 |   1.079 | 0/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_RQC_16    | DENSE_AQV32_16 | f1_p99   |    0.9947 |      0.9798 |   1.079 | 0/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_RQC_16    | DENSE_AQV33_16 | auc      |    0.9995 |      0.9996 |   0.909 | 7/8           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_RQC_16    | DENSE_AQV33_16 | f1_p99   |    0.9947 |      0.9954 |   0.909 | 7/8           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_RQT_16    | DENSE_ZS       | auc      |    0.9994 |      0.9997 |   0.423 | 9/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_RQT_16    | DENSE_ZS       | f1_p99   |    0.9944 |      0.9961 |   0.423 | 9/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_RQT_16    | DENSE_AQV32_16 | auc      |    0.9994 |      0.9982 |   0.992 | 5/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_RQT_16    | DENSE_AQV32_16 | f1_p99   |    0.9944 |      0.9798 |   0.992 | 5/9           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_RQT_16    | DENSE_AQV33_16 | auc      |    0.9994 |      0.9996 |   0.842 | 8/8           |      8 | trade-off/inconclusive |
| edge_iiotset | SNN_RQT_16    | DENSE_AQV33_16 | f1_p99   |    0.9944 |      0.9954 |   0.842 | 8/8           |      8 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV3_16 | DENSE_ZS       | auc      |    0.9135 |      0.8942 |   0.433 | 6/6           |      6 | SNN dominates       |
| ciciot2023   | SNN_MEMOV3_16 | DENSE_ZS       | f1_p99   |    0.808  |      0.839  |   0.433 | 6/6           |      6 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV3_16 | DENSE_AQV32_16 | auc      |    0.9135 |      0.8409 |   1.057 | 1/5           |      5 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV3_16 | DENSE_AQV32_16 | f1_p99   |    0.808  |      0.773  |   1.057 | 1/5           |      5 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV3_16 | DENSE_AQV33_16 | auc      |    0.9135 |      0.8644 |   0.846 | 5/6           |      6 | trade-off/inconclusive |
| ciciot2023   | SNN_MEMOV3_16 | DENSE_AQV33_16 | f1_p99   |    0.808  |      0.8295 |   0.846 | 5/6           |      6 | trade-off/inconclusive |
| ciciot2023   | SNN_RQC_16    | DENSE_ZS       | auc      |    0.9068 |      0.8942 |   0.398 | 6/6           |      6 | SNN dominates       |
| ciciot2023   | SNN_RQC_16    | DENSE_ZS       | f1_p99   |    0.7756 |      0.839  |   0.398 | 6/6           |      6 | trade-off/inconclusive |
| ciciot2023   | SNN_RQC_16    | DENSE_AQV32_16 | auc      |    0.9068 |      0.8409 |   0.956 | 3/4           |      4 | trade-off/inconclusive |
| ciciot2023   | SNN_RQC_16    | DENSE_AQV32_16 | f1_p99   |    0.7756 |      0.773  |   0.956 | 3/4           |      4 | trade-off/inconclusive |
| ciciot2023   | SNN_RQC_16    | DENSE_AQV33_16 | auc      |    0.9068 |      0.8644 |   0.845 | 5/5           |      5 | SNN dominates       |
| ciciot2023   | SNN_RQC_16    | DENSE_AQV33_16 | f1_p99   |    0.7756 |      0.8295 |   0.845 | 5/5           |      5 | trade-off/inconclusive |
| ciciot2023   | SNN_RQT_16    | DENSE_ZS       | auc      |    0.8905 |      0.8942 |   0.395 | 7/7           |      7 | trade-off/inconclusive |
| ciciot2023   | SNN_RQT_16    | DENSE_ZS       | f1_p99   |    0.7505 |      0.839  |   0.395 | 7/7           |      7 | trade-off/inconclusive |
| ciciot2023   | SNN_RQT_16    | DENSE_AQV32_16 | auc      |    0.8905 |      0.8409 |   0.978 | 3/6           |      6 | trade-off/inconclusive |
| ciciot2023   | SNN_RQT_16    | DENSE_AQV32_16 | f1_p99   |    0.7505 |      0.773  |   0.978 | 3/6           |      6 | trade-off/inconclusive |
| ciciot2023   | SNN_RQT_16    | DENSE_AQV33_16 | auc      |    0.8905 |      0.8644 |   0.82  | 8/8           |      8 | SNN dominates       |
| ciciot2023   | SNN_RQT_16    | DENSE_AQV33_16 | f1_p99   |    0.7505 |      0.8295 |   0.82  | 8/8           |      8 | trade-off/inconclusive |

## S7h (s0_f0, FP32 + INT8)

|                                    |   n |    dE_nJ |   Eact_nJ |   lat_us |
|:-----------------------------------|----:|---------:|----------:|---------:|
| ('ciciot2023', 'DENSE')            |   3 | 1710.5   |   5178.85 |    0.841 |
| ('ciciot2023', 'DENSE_AQV22_16')   |   3 |  547.614 |   1823.91 |    0.306 |
| ('ciciot2023', 'DENSE_AQV23_16')   |   3 |  664.924 |   2105.09 |    0.353 |
| ('ciciot2023', 'DENSE_Q8')         |   3 | 1658.88  |   5497.68 |    0.941 |
| ('ciciot2023', 'DENSE_Q8_ZS')      |   3 | 1344.78  |   4515.84 |    0.776 |
| ('ciciot2023', 'DENSE_ZS')         |   3 | 1270.59  |   3998.12 |    0.652 |
| ('ciciot2023', 'SNN_COUNT')        |   3 | 2344.56  |   7831.41 |    1.361 |
| ('ciciot2023', 'SNN_MEMOV2_16')    |   3 |  593.157 |   1917.53 |    0.32  |
| ('ciciot2023', 'SNN_Q8')           |   3 | 2210.56  |   8280    |    1.481 |
| ('ciciot2023', 'SNN_Q8_MEMO_16')   |   3 |  846.091 |   2985.25 |    0.53  |
| ('edge_iiotset', 'DENSE')          |   3 | 1620.32  |   5060.14 |    0.829 |
| ('edge_iiotset', 'DENSE_AQV22_16') |   3 |  596.978 |   2006.34 |    0.344 |
| ('edge_iiotset', 'DENSE_AQV23_16') |   3 |  748.283 |   2376.25 |    0.398 |
| ('edge_iiotset', 'DENSE_Q8')       |   3 | 1576.05  |   5453.75 |    0.95  |
| ('edge_iiotset', 'DENSE_Q8_ZS')    |   3 | 1470.91  |   4801.33 |    0.835 |
| ('edge_iiotset', 'DENSE_ZS')       |   3 | 1339.47  |   4164.31 |    0.686 |
| ('edge_iiotset', 'SNN_COUNT')      |   3 | 2873.2   |   8939.51 |    1.568 |
| ('edge_iiotset', 'SNN_MEMOV2_16')  |   3 |  897.109 |   2640.77 |    0.45  |
| ('edge_iiotset', 'SNN_Q8')         |   3 | 2369.42  |   8867.61 |    1.584 |
| ('edge_iiotset', 'SNN_Q8_MEMO_16') |   3 | 1044.85  |   3545.98 |    0.634 |

## Low-Idle Artifact: ΔE Relative to Variant Median (per Block × Dataset)

|                                     |   size |   median |
|:------------------------------------|-------:|---------:|
| ('S7g', 'ciciot2023', False)        |     10 |    0.794 |
| ('S7g', 'ciciot2023', True)         |     26 |    1.038 |
| ('S7g', 'edge_iiotset', False)      |     23 |    0.965 |
| ('S7g', 'edge_iiotset', True)       |     13 |    1.204 |
| ('S7g-more', 'ciciot2023', False)   |     43 |    0.936 |
| ('S7g-more', 'ciciot2023', True)    |     29 |    1.161 |
| ('S7g-more', 'edge_iiotset', False) |     44 |    0.94  |
| ('S7g-more', 'edge_iiotset', True)  |     28 |    1.201 |
| ('S7h', 'ciciot2023', False)        |     30 |    1     |
| ('S7h', 'edge_iiotset', False)      |     27 |    1     |
| ('S7h', 'edge_iiotset', True)       |      3 |    1.259 |
| ('S7j', 'ciciot2023', False)        |     43 |    0.972 |
| ('S7j', 'ciciot2023', True)         |     11 |    1.215 |
| ('S7j', 'edge_iiotset', False)      |     53 |    1     |
| ('S7j', 'edge_iiotset', True)       |      1 |    1.298 |

Correlation idle_W vs relative ΔE (all): -0.75
