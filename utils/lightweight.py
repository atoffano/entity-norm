import shutil
import subprocess
import os, sys
import time
import glob
from datetime import date
from main import capture_stdout

def setup(base_dir, input_std_data, kb, args):
    os.makedirs(f'{base_dir}/Biomedical-Entity-Linking/output/{args["input"]}/candidates')
    os.makedirs(f'{base_dir}/Biomedical-Entity-Linking/output/{args["input"]}/candidates')
    os.makedirs(f'{base_dir}/Biomedical-Entity-Linking/output/{args["input"]}/embed')
    if not os.path.exists(f'{base_dir}/Biomedical-Entity-Linking/input/{args["input"]}/BioWordVec_PubMed_MIMICIII_d200.vec.bin'):
        raise Exception("BioWordVec 200-dimensional word embeddings were not found in Biomedical-Entity-Linking/input.")
    shutil.copy(f'{base_dir}/Biomedical-Entity-Linking/output/ncbi/char_vocabulary.dict', f'{base_dir}/BioSyn/preprocess/resources/{kb}')
    shutil.copy(f'{base_dir}/Biomedical-Entity-Linking/output/ncbi/word_vocabulary.dict', f'{base_dir}/BioSyn/preprocess/resources/{kb}')

    # Preprocess
    preprocess_arguments = [
    'python3', f'{base_dir}/Biomedical-Entity-Linking/input/preprocess.py',
    '--input', input_std_data,
    '--output', f'{base_dir}/Biomedical-Entity-Linking/{args["input"]}/processed_data',
    '--kb', f'{base_dir}/data/knowledge_base/standardized/{kb}',
    '--merge']
    if args["evalset"] != 'dev':
        preprocess_arguments.remove('--merge')
    p = subprocess.run(preprocess_arguments, stdout=subprocess.PIPE, bufsize=1)
    capture_stdout(p)

def run(base_dir, args):
    p = subprocess.run('python3', f'{base_dir}/Biomedical-Entity-Linking/source/generate_candidate.py', stdout=subprocess.PIPE, bufsize=1)
    capture_stdout(p)

    # Loading BioSyn training parameters
    params = params['Biomedical-Entity-Linking']
    train_arguments = [
    'python3', f'{base_dir}/Biomedical-Entity-Linking/source/train.py',
    '-dataset', args["input"]]
    for key, value in params.items():
        if value == '' or value == False:
            del params[key]
        else:
            train_arguments.append(f'-{params[key]}')
            if params[value] != True:
                train_arguments.append(params[value])

    # Training
    p = subprocess.run(train_arguments, stdout=subprocess.PIPE, bufsize=1)
    capture_stdout(p)

    # Standardizing predictions
    with open(f'{base_dir}/Biomedical-Entity-Linking/checkpoints/predict_result.txt', 'r') as f:
        predictions = f.readlines()
    with open(f'{base_dir}/Biomedical-Entity-Linking/checkpoints/standardized_predictions.txt', 'a') as fh:
        for pred in predictions:
            pred = pred.strip('\n').split('\t')
            pmid, mention, prediction, prediction_label, ground_truth = pred[0], pred[1], pred[3], pred[4], pred[2]
            fh.write(f'{pmid}\t{mention}\t{prediction}\t{prediction_label}\t{ground_truth}')
    
def cleanup(base_dir, args, kb, run_nb):
    dt = date.today()
    print(f'Cleaning up Biomedical-Entity-Linking directory and moving all outputs to {base_dir}/results/Biomedical-Entity-Linking/{args["input"]}-{dt}')
    if not os.path.exists(f'{base_dir}/results/Biomedical-Entity-Linking/{args["input"]}-{dt}'):
        os.makedirs(f'{base_dir}/results/Biomedical-Entity-Linking/{args["input"]}-{dt}')    
    [shutil.move(file, f'{base_dir}/results/Biomedical-Entity-Linking/{args["input"]}-{dt}/run_{run_nb}') for file in glob.glob(f'{base_dir}/Biomedical-Entity-Linking/checkpoints/*')]
    os.remove(f'{base_dir}/results/Biomedical-Entity-Linking/{args["input"]}')
    print('Cleaning done.')