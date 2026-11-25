#!/bin/bash
cd "$(dirname "$0")"
export LC_ALL=C
head -n -1 LOCK_S7T.sha256 | sha256sum -c --quiet || { echo 'STATUS lock-mismatch'; exit 4; }
for ds in edge_iiotset ciciot2023; do
  echo "STATUS start $ds $(date '+%F %T')"
  nice -n 10 /home/jupyteruser/jupyter_env/bin/python -u s7t_server.py --dataset $ds --repeats 15 --core 10 --out results > logs/s7t_$ds.log 2>&1 || { echo "STATUS failed $ds"; exit 3; }
done
/home/jupyteruser/jupyter_env/bin/python s7t_analyze.py > logs/analyze.log 2>&1 || { echo 'STATUS analyze-failed'; exit 5; }
echo "STATUS done $(date '+%F %T')"
