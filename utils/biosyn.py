import shutil
import subprocess
import os
import time
from datetime import date

def setup(base_dir, input_std_data, args):
    subprocess.run([
    'python', f'{base_dir}/utils/adapt_input.py',
    '--input', input_std_data,
    '--output', f'{base_dir}/BioSyn/{args.input}/raw',
    '--to', 'ncbi-disease'], capture_output=True, text=True)

    # Checks knowledge base existence and recreates it if needed.
    if 'BB4' in args.input:
        if not os.path.exists(f'{base_dir}/data/knowledge_base/standardized/BB4_kb.txt'):
            with open(f'{base_dir}/data/knowledge_base/standardized/OntoBiotope_BioNLP-OST-2019.obo', 'r') as fh:
                lines = fh.readlines()
            synonym = []
            for line in lines:
                if line.startswith('id'):
                    cui = line.strip().split(': ')[1]
                elif line.startswith('name'):
                    label = line.strip().split(': ')[1]
                elif line.startswith('synonym'):
                    synonym.append(line.split('"')[1])
                elif line.startswith('is_a') and cui != False:
                    if synonym != []:
                        label = label + "" + "".join(synonym)
                    with open(f'{base_dir}/data/knowledge_base/standardized/bb4_kb.txt', 'a') as f:
                        f.write(f"{cui}{label}\n")
                    synonym = []
                    cui = False
    if 'ncbi-disease' in args.input:
        if not os.path.exists(f'{base_dir}/data/knowledge_base/standardized/ncbi-disease_kb.txt'):
            shutil.copy(f'{base_dir}/data/knowledge_base/raw/medic_06Jul2012.txt', f'{base_dir}/data/knowledge_base/standardized/ncbi-disease_kb.txt')
            # the ncbi-disease kb provided by BioSyn authors is considered to be the standart format for knowledge bases.
    shutil.copy(f'{base_dir}/data/knowledge_base/standardized/{args.input}_kb.txt', f'{base_dir}/BioSyn/preprocess/resources/{args.input}_kb.txt')



def run(base_dir, args, params, run_nb):
    # Loading BioSyn working environement
    params = params['biosyn']

    # Installing BioSyn package
    subprocess.run(['python', f'{base_dir}/BioSyn/setup.py', 'develop'], capture_output=True, text=True)
    
    #Preprocessing
    print('Starting data preprocessing')
    print('Parsing adapted dataset to generate mentions and concepts')
    [subprocess.run([
    'python', f'{base_dir}/BioSyn/ncbi_disease_preprocess.py',
    '--input_file', f'{base_dir}/BioSyn/{args.input}/raw/{dataset}set_corpus.txt',
    '--output_dir', f'{base_dir}/BioSyn/{args.input}/{dataset}'], capture_output=True, text=True) for dataset in ['train', 'dev', 'test']]
    
    #Training set preprocessing
    print('Preprocessing training set and its dictionary')
    subprocess.run([
    'python', f'{base_dir}/BioSyn/dictionnary_preprocess.py',
    '--input_dictionary_path', f'{base_dir}/BioSyn/preprocess/resources/{args.input}_kb.txt',
    '--output_dictionary_path', f'{base_dir}/BioSyn/{args.input}/train_dictionary.txt',
    '--lowercase',
    '--remove_punctuation'], capture_output=True, text=True,)

    subprocess.run([
    'python', f'{base_dir}/BioSyn/query_preprocess.py',
    '--input_dir', f'{base_dir}/BioSyn/{args.input}/train/',
    '--output_dir', f'{base_dir}/BioSyn/{args.input}/processed_train/',
    '--dictionary_path', f'{base_dir}/BioSyn/{args.input}/train_dictionnary.txt',
    '--ab3p_path', f'{base_dir}/BioSyn/Ab3P/identify_abbr',
    '--typo_path', f'{base_dir}/BioSyn/preprocess/resources/ncbi-spell-check.txt',
    '--remove_cuiless',
    '--lowercase', 'True',
    '--remove_punctuation', 'True'], capture_output=True, text=True)

    #Dev set preprocessing
    print('Preprocessing devlopement set and its dictionary')
    subprocess.run([
    'python', f'{base_dir}/BioSyn/dictionnary_preprocess.py',
    '--input_dictionary_path', f'{base_dir}/BioSyn/preprocess/resources/{args.input}_kb.txt',
    '--additional_data_dir', f'{base_dir}/BioSyn/{args.input}/processed_train',
    '--output_dictionary_path', f'{base_dir}/BioSyn/{args.input}/dev_dictionary.txt',
    '--lowercase',
    '--remove_punctuation'], capture_output=True, text=True,)

    subprocess.run([
    'python', f'{base_dir}/BioSyn/query_preprocess.py',
    '--input_dir', f'{base_dir}/BioSyn/{args.input}/dev/',
    '--output_dir', f'{base_dir}/BioSyn/{args.input}/processed_dev/',
    '--dictionary_path', f'{base_dir}/BioSyn/{args.input}/dev_dictionnary.txt',
    '--ab3p_path', f'{base_dir}/BioSyn/Ab3P/identify_abbr',
    '--typo_path', f'{base_dir}/BioSyn/preprocess/resources/ncbi-spell-check.txt',
    '--remove_cuiless',
    '--lowercase', 'True',
    '--remove_punctuation', 'True'], capture_output=True, text=True)

    #Test set preprocessing
    print('Preprocessing test set and its dictionary')
    subprocess.run([
    'python', f'{base_dir}/BioSyn/dictionnary_preprocess.py',
    '--input_dictionary_path', f'{base_dir}/BioSyn/preprocess/resources/{args.input}_kb.txt',
    '--additional_data_dir', f'{base_dir}/BioSyn/{args.input}/processed_dev',
    '--output_dictionary_path', f'{base_dir}/BioSyn/{args.input}/test_dictionary.txt',
    '--lowercase',
    '--remove_punctuation'], capture_output=True, text=True,)

    subprocess.run([
    'python', f'{base_dir}/BioSyn/query_preprocess.py',
    '--input_dir', f'{base_dir}/BioSyn/{args.input}/test/',
    '--output_dir', f'{base_dir}/BioSyn/{args.input}/processed_test/',
    '--dictionary_path', f'{base_dir}/BioSyn/{args.input}/test_dictionnary.txt',
    '--ab3p_path', f'{base_dir}/BioSyn/Ab3P/identify_abbr',
    '--typo_path', f'{base_dir}/BioSyn/preprocess/resources/ncbi-spell-check.txt',
    '--remove_cuiless',
    '--lowercase', 'True',
    '--remove_punctuation', 'True'], capture_output=True, text=True)

    # Constructing traindev
    if args.evalset == 'test':
        print("Merging train + dev")
        os.makedirs(f'{base_dir}/BioSyn/{args.input}/processed_traindev/')
        shutil.copytree(f'{base_dir}/BioSyn/{args.input}/processed_dev/', f'{base_dir}/BioSyn/{args.input}/processed_traindev/')
        shutil.copytree(f'{base_dir}/BioSyn/{args.input}/processed_train/', f'{base_dir}/BioSyn/{args.input}/processed_traindev/')

    # Model training
    print(f'Training BioSyn model on {traindir}..')
    seed = int(round(time.time() * 1000)) % 10000 if params['seed'] == None else params['seed']
    traindir = 'traindev' if args.evalset == 'test' else 'train'
    subprocess.run([
    'python', f'{base_dir}/BioSyn/train.py',
    '--model_name_or_path', 'dmis-lab/biobert-base-cased-v1.1',
    '--train_dictionary_path', f'{base_dir}/BioSyn/{args.input}/train_dictionnary.txt',
    '--train_dir', f'{base_dir}/BioSyn/{args.input}/processed_{traindir}',
    '--output_dir', f'{base_dir}/BioSyn/{args.input}-run_{run_nb}',
    '--use_cuda', params['use_cuda'],
    '--topk', params['topk'],
    '--seed', seed,
    '--epoch', params['epoch'],
    '--train_batch_size', params['train_batch_size'],
    '--learning_rate', params['learning_rate'],
    '--max_length', params['max_length']], capture_output=True, text=True)
    print('Training done.')

    # Model inference
    print(f'Predicting on {args.evalset}..')
    subprocess.run([
    'python', f'{base_dir}/BioSyn/eval.py',
    '--model_name_or_path', f'{base_dir}/BioSyn/{args.input}-run_{run_nb}',
    '--dictionary_path', f'{base_dir}/BioSyn/{args.input}/train_dictionnary.txt',
    '--data_dir', f'{base_dir}/BioSyn/{args.input}/processed_{traindir}',
    '--output_dir', f'{base_dir}/BioSyn/{args.input}-run_{run_nb}',
    '--use_cuda', params['use_cuda'],
    '--topk', params['topk'],
    '--save_predictions',
    '--max_length', params['max_length']], capture_output=True, text=True)
    print('Prediction done.')

def cleanup(base_dir, args, run_nb):
    dt = date.today()
    print(f'Cleaning up BioSyn directory and moving all outputs to {base_dir}/results/BioSyn/{args.input}-{dt}')
    os.makedirs(f'{base_dir}/results/BioSyn/{args.input}-{dt}')
    shutil.move(f'{base_dir}/BioSyn/{args.input}', f'{base_dir}/results/BioSyn/{args.input}-{dt}/run_{run_nb}')
    shutil.move(f'{base_dir}/BioSyn/preprocess/resources/{args.input}_kb.txt', f'{base_dir}/results/BioSyn/{args.input}-{dt}/run_{run_nb}/{args.input}_kb.txt')
    print('Cleaning done.')