#!/bin/bash
# S7p fase energi (DESIGN_S7P_POWER.md), dijalankan di dalam e37-lock oleh start_s7p.sh. Blok gagal -> berhenti.
set -u
export FNIRSI_NO_RESET=1 LC_ALL=C
R=/home/a3m-nix/snn-ae-final
PY=/home/a3m-nix/miniforge3/envs/env_snn/bin/python
st() { echo "STATUS $* $(date '+%F %T')"; }

st start
bash "$R/s7p/preflight_fnirsi.sh" || { st failed:preflight; exit 4; }

cd "$R/s7j"
for ds in edge_iiotset ciciot2023; do
    st s7j-power "$ds"
    "$PY" -u s7j_rpi.py --dataset "$ds" --phase power --orders capture --rounds 3 \
        --variants DENSE_ZS,SNN_MEMOV3_16,SNN_RQC_16,SNN_RQT_16,DENSE_AQV32_16,DENSE_AQV33_16 \
        || { st "failed:s7j-power:$ds"; exit 3; }
done

cd "$R/s7d_pi"
for ds in edge_iiotset ciciot2023; do
    st s7h-power "$ds"
    "$PY" -u s7h_rpi.py --dataset "$ds" --phase power || { st "failed:s7h-power:$ds"; exit 3; }
done

cd "$R/s7g"
for ds in edge_iiotset ciciot2023; do
    st s7g-more-power "$ds"
    "$PY" -u s7g_more_rpi.py --dataset "$ds" --phase power \
        --pkg "$R/s7f/rpi_package_more" --units s0_f1,s1_f1,s2_f1,s0_f2,s1_f2,s2_f2 \
        --result "$R/0-revision-results-v2/s7g_more" \
        --variants DENSE_ZS,DENSE_AQV22_16,DENSE_AQV23_16,SNN_MEMOV2_16 --orders capture --rounds 3 \
        || { st "failed:s7g-more-power:$ds"; exit 3; }
done
st done
