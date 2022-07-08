import shutil
import subprocess
import os
import time
import glob
from datetime import date
import sys
def setup(base_dir, input_std_data, args):
    os.makedirs(f'{base_dir}/Biomedical-Entity-Linking/output/{args["input"]}/candidates')
    os.makedirs(f'{base_dir}/Biomedical-Entity-Linking/output/{args["input"]}/candidates')
    os.makedirs(f'{base_dir}/Biomedical-Entity-Linking/output/{args["input"]}/embed')
    if not os.path.exists(f'{base_dir}/Biomedical-Entity-Linking/input/{args["input"]}/BioWordVec_PubMed_MIMICIII_d200.vec.bin'):
        raise Exception("BioWordVec 200-dimensional word embeddings were not found in Biomedical-Entity-Linking/input.")
    p = subprocess.run([
    'python', f'{base_dir}/utils/adapt_input.py',
    '--input', input_std_data,
    '--output', f'{base_dir}/BioSyn/{args["input"]}/original',
    '--to', args["method"]], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print( 'exit status:', p.returncode )
    print( 'stdout:', p.stdout.decode() )