import shutil
import subprocess
import os
import time
import glob
from datetime import date
import sys

def setup(base_dir, input_std_data, kb, args):
    # Load data
    p = subprocess.run([
    'python', f'{base_dir}/utils/adapt_input.py',
    '--input', input_std_data,
    '--output', f'{base_dir}/BioSyn/{args["input"]}/original',
    '--to', args["method"]], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print( 'exit status:', p.returncode )
    print( 'stdout:', p.stdout.decode() )

    # Load kb
    shutil.copy(f'{base_dir}/data/knowledge_base/standardized/{kb}', f'{base_dir}/BioSyn/preprocess/resources/{kb}')



def run(base_dir, args, params, kb, run_nb):
    # Loading BioSyn working environement
    params = params['BioSyn']

    #Preprocessing
    os.chdir(f'{base_dir}/BioSyn/preprocess/')
    print('Starting data preprocessing')
    print('Parsing adapted dataset to generate mentions and concepts')
    for dataset in ['train', 'dev', 'test']:
        p = subprocess.run([
        'python', './ncbi_disease_preprocess.py',
        '--input_file', f'../{args["input"]}/original/{dataset}set_corpus.txt',
        '--output_dir', f'../{args["input"]}/{dataset}'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print( 'exit status:', p.returncode )
        print( 'stdout:', p.stdout.decode() )
    
    #Training set preprocessing
    print('Preprocessing training set and its dictionary')
    p = subprocess.run([
    'python', f'./dictionary_preprocess.py',
    '--input_dictionary_path', f'./resources/{kb}',
    '--output_dictionary_path', f'../{args["input"]}/train_dictionary.txt',
    '--lowercase',
    '--remove_punctuation'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print( 'exit status:', p.returncode )
    print( 'stdout:', p.stdout.decode() )

    p = subprocess.run([
    'python', './query_preprocess.py',
    '--input_dir', f'../{args["input"]}/train/',
    '--output_dir', f'../{args["input"]}/processed_train/',
    '--dictionary_path', f'../{args["input"]}/train_dictionary.txt',
    '--ab3p_path', '../Ab3P/identify_abbr',
    '--typo_path', './resources/ncbi-spell-check.txt',
    '--remove_cuiless',
    '--resolve_composites',
    '--lowercase', 'true',
    '--remove_punctuation', 'true'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print( 'exit status:', p.returncode )
    print( 'stdout:', p.stdout.decode() )

    #Dev set preprocessing
    print('Preprocessing devlopement set and its dictionary')
    p = subprocess.run([
    'python', './dictionary_preprocess.py',
    '--input_dictionary_path', f'./resources/{kb}',
    '--additional_data_dir', f'../{args["input"]}/processed_train',
    '--output_dictionary_path', f'../{args["input"]}/dev_dictionary.txt',
    '--lowercase',
    '--remove_punctuation'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print( 'exit status:', p.returncode )
    print( 'stdout:', p.stdout.decode() )

    p = subprocess.run([
    'python', f'./query_preprocess.py',
    '--input_dir', f'../{args["input"]}/dev/',
    '--output_dir', f'../{args["input"]}/processed_dev/',
    '--dictionary_path', f'../{args["input"]}/dev_dictionary.txt',
    '--ab3p_path', '../Ab3P/identify_abbr',
    '--typo_path', './resources/ncbi-spell-check.txt',
    '--remove_cuiless',
    '--resolve_composites',
    '--lowercase', 'true',
    '--remove_punctuation', 'true'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print( 'exit status:', p.returncode )
    print( 'stdout:', p.stdout.decode() )

    #Test set preprocessing
    print('Preprocessing test set and its dictionary')
    p = subprocess.run([
    'python', f'./dictionary_preprocess.py',
    '--input_dictionary_path', f'./resources/{kb}',
    '--additional_data_dir', f'../{args["input"]}/processed_dev',
    '--output_dictionary_path', f'../{args["input"]}/test_dictionary.txt',
    '--lowercase',
    '--remove_punctuation'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print( 'exit status:', p.returncode )
    print( 'stdout:', p.stdout.decode() )

    p = subprocess.run([
    'python', './query_preprocess.py',
    '--input_dir', f'../{args["input"]}/test/',
    '--output_dir', f'../{args["input"]}/processed_test/',
    '--dictionary_path', f'../{args["input"]}/test_dictionary.txt',
    '--ab3p_path', '../Ab3P/identify_abbr',
    '--typo_path', f'./resources/ncbi-spell-check.txt',
    '--remove_cuiless',
    '--resolve_composites',
    '--lowercase', 'true',
    '--remove_punctuation', 'true'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print( 'exit status:', p.returncode )
    print( 'stdout:', p.stdout.decode() )

    # Constructing traindev
    if args["evalset"] == 'test':
        print("Merging train + dev")
        shutil.copytree(f'../{args["input"]}/processed_dev/', f'../{args["input"]}/processed_traindev/')
        [shutil.copy(file, f'../{args["input"]}/processed_traindev/') for file in glob.glob(f'../{args["input"]}/processed_train/*')]

    # Model training
    print(type(params['topk']))
    seed = int(round(time.time() * 1000)) % 10000 if params['seed'] == '' else params['seed']
    traindir = 'traindev' if args["evalset"] == 'test' else 'train'
    print(f'Training BioSyn model on {traindir}..')
    train_arguments = ['python', '../train.py',
    '--model_name_or_path', 'dmis-lab/biobert-base-cased-v1.1',
    '--train_dictionary_path', f'../{args["input"]}/train_dictionary.txt',
    '--train_dir', f'../{args["input"]}/processed_{traindir}',
    '--output_dir', f'../{args["input"]}-run_{run_nb}',
    '--topk', params['topk'],
    '--seed', str(seed),
    '--epoch', params['epoch'],
    '--initial_sparse_weight', params["initial_sparse_weight"],
    '--train_batch_size', params["train_batch_size"],
    '--learning_rate', params["learning_rate"],
    '--max_length', params["max_length"],
    '--use_cuda',
    '--draft',
    '--save_checkpoint_all']
    print(type(params['use_cuda']))
    print(params['save_checkpoint_all'])
    if params['use_cuda'] != True:
        train_arguments.remove('--use_cuda')
    if params['save_checkpoint_all'] != True:
        train_arguments.remove('--save_checkpoint_all')
    if params['draft'] != True:
        train_arguments.remove('--draft')

    p = subprocess.Popen(train_arguments, stdout=subprocess.PIPE, bufsize=1)
    for line in iter(p.stdout.readline, b''):
        sys.stdout.write(line.decode(sys.stdout.encoding))
    p.stdout.close()
    p.wait()

    print('Training done.')

    # Model inference
    print(f'Predicting on {args["evalset"]}..')
    p = subprocess.run([
    'python', '../eval.py',
    '--model_name_or_path', f'../{args["input"]}-run_{run_nb}',
    '--dictionary_path', f'../{args["input"]}/train_dictionary.txt',
    '--data_dir', f'../{args["input"]}/processed_{"test" if traindir == "traindev" else "dev"}',
    '--output_dir', f'../{args["input"]}-run_{run_nb}',
    '--use_cuda' if params['use_cuda'] == 'true' else '',
    '--topk', params['topk'],
    '--save_predictions',
    '--max_length', params['max_length']], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print( 'exit status:', p.returncode )
    print( 'stdout:', p.stdout.decode() )
    print('Prediction done.')

def cleanup(base_dir, args, kb, run_nb):
    dt = date.today()
    print(f'Cleaning up BioSyn directory and moving all outputs to {base_dir}/results/BioSyn/{args["input"]}-{dt}')
    os.makedirs(f'{base_dir}/results/BioSyn/{args["input"]}-{dt}')
    shutil.move(f'../{args["input"]}', f'{base_dir}/results/BioSyn/{args["input"]}-{dt}/run_{run_nb}')
    shutil.move(f'./resources/{kb}', f'{base_dir}/results/BioSyn/{args["input"]}-{dt}/run_{run_nb}/{kb}')
    os.chdir(f'{base_dir}')
    print('Cleaning done.')