#!/bin/bash
set -u
cd /home/a3m-nix/snn-ae-final/s7k
export LC_ALL=C
PY=/home/a3m-nix/miniforge3/envs/env_snn/bin/python
sha256sum -c --quiet <(head -n -1 LOCK_S7K.sha256 | sed 's#  s7k/#  ../s7k/#') 2>/dev/null || { cd ..; sha256sum -c --quiet <(head -n -1 s7k/LOCK_S7K.sha256) || { echo "STATUS lock-mismatch"; exit 4; }; cd s7k; }
for ph in check k2 k3 k4; do
  for ds in edge_iiotset ciciot2023; do
    echo "STATUS $ph:$ds $(date '+%F %T')"
    "$PY" -u s7k_rpi.py --dataset "$ds" --phase "$ph" || { echo "STATUS failed:$ph:$ds"; exit 3; }
  done
done
echo "STATUS done $(date '+%F %T')"
