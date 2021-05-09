#!/bin/bash
source /home/miniconda/etc/profile.d/conda.sh &> ./logs/null.txt
conda init bash &> ./logs/null.txt
conda activate denoise &> ./logs/null.txt
soft/denoise.py -i $1 -o $2 &&  echo 'passed' > ./logs/$3 || echo 'failed' > ./logs/$3
