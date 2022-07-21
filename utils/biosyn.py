import shutil
import subprocess
import os
import time
import glob
import datetime
import sys
import json

def setup(base_dir, input_std_data, kb):
    '''
    Transforms a standardized dataset in the NCBI disease corpus output format.

            Parameters:
                    base_dir (str): entity-norm path.
                    input_std_data (str) : path to standardized data.
                    kb (str): path to relevant knowledge base.
            Output:
                    Data converted to ncbi-disease format and as such loadable by BioSyn.
    '''
    for dataset in ['train', 'dev', 'test']:
        outfile = f"{dataset}set_corpus.txt"
        output = f'{base_dir}/BioSyn/{input_std_data}/data/original_input'
        if not os.path.exists(output):
            os.makedirs(output)
        for file in glob.glob(f'{input_std_data}/{dataset}/*_header.txt'):
            pmid, title, abstract, data = extract(filename=file)
            with open(f'{output}/{outfile}', 'a') as f:
                f.write(f"\n{pmid}|t|{title}{pmid}|a|{abstract}")
                for line in data:
                    line = "\t".join(line)
                    f.write(f"{pmid}\t{line}")

    # Load kb
    shutil.copy(f'{base_dir}/data/knowledge_base/standardized/{kb}', f'{base_dir}/BioSyn/preprocess/resources/{kb}')



def run(base_dir, args, params, kb):
    '''
    1) Preprocesses data
    2) Trains model with parameters from config.json
    3) Inference

            Parameters:
                    base_dir (str): Path of entity-norm folder
                    env_path (str): Path of lightweight folder (Biomedical-Entity-Linking)
                    params (str) : Parameters specifying how the model should be trained.
                    args (dict) : arguments from main.py
                    kb (str) : path to relevant knowledge base.
            Output:
                Prediction files.
    '''

    # Loading BioSyn training parameters
    params = params['BioSyn']

    #Preprocessing
    os.chdir(f'{base_dir}/BioSyn/preprocess/')
    print('Starting data preprocessing')
    print('Parsing adapted dataset to generate mentions and concepts')
    for dataset in ['train', 'dev', 'test']:
        p = subprocess.Popen([
        'python', './ncbi_disease_preprocess.py',
        '--input_file', f'../{args["input"]}/data/original_input/{dataset}set_corpus.txt',
        '--output_dir', f'../{args["input"]}/data/{dataset}'], stdout=subprocess.PIPE, bufsize=1)
    for line in iter(p.stdout.readline, b''):
        sys.stdout.write(line.decode(sys.stdout.encoding))
    p.stdout.close()
    p.wait()
    
    #Training set preprocessing
    print('Preprocessing training set and its dictionary')
    p = subprocess.Popen([
    'python', f'./dictionary_preprocess.py',
    '--input_dictionary_path', f'./resources/{kb}',
    '--output_dictionary_path', f'../{args["input"]}/data/train_dictionary.txt',
    '--lowercase',
    '--remove_punctuation'], stdout=subprocess.PIPE, bufsize=1)
    for line in iter(p.stdout.readline, b''):
        sys.stdout.write(line.decode(sys.stdout.encoding))
    p.stdout.close()
    p.wait()

    p = subprocess.Popen([
    'python', './query_preprocess.py',
    '--input_dir', f'../{args["input"]}/data/train/',
    '--output_dir', f'../{args["input"]}/data/processed_train/',
    '--dictionary_path', f'../{args["input"]}/data/train_dictionary.txt',
    '--ab3p_path', '../Ab3P/identify_abbr',
    '--typo_path', './resources/ncbi-spell-check.txt',
    '--remove_cuiless', 
    '--resolve_composites',
    '--lowercase', 'true',
    '--remove_punctuation', 'true'], stdout=subprocess.PIPE, bufsize=1)
    for line in iter(p.stdout.readline, b''):
        sys.stdout.write(line.decode(sys.stdout.encoding))
    p.stdout.close()
    p.wait()

    #Dev set preprocessing
    print('Preprocessing devlopement set and its dictionary')
    p = subprocess.Popen([
    'python', './dictionary_preprocess.py',
    '--input_dictionary_path', f'./resources/{kb}',
    '--additional_data_dir', f'../{args["input"]}/data/processed_train',
    '--output_dictionary_path', f'../{args["input"]}/data/dev_dictionary.txt',
    '--lowercase',
    '--remove_punctuation'], stdout=subprocess.PIPE, bufsize=1)
    for line in iter(p.stdout.readline, b''):
        sys.stdout.write(line.decode(sys.stdout.encoding))
    p.stdout.close()
    p.wait()

    p = subprocess.Popen([
    'python', f'./query_preprocess.py',
    '--input_dir', f'../{args["input"]}/data/dev/',
    '--output_dir', f'../{args["input"]}/data/processed_dev/',
    '--dictionary_path', f'../{args["input"]}/data/dev_dictionary.txt',
    '--ab3p_path', '../Ab3P/identify_abbr',
    '--typo_path', './resources/ncbi-spell-check.txt',
    '--remove_cuiless', 
    '--resolve_composites',
    '--lowercase', 'true',
    '--remove_punctuation', 'true'], stdout=subprocess.PIPE, bufsize=1)
    for line in iter(p.stdout.readline, b''):
        sys.stdout.write(line.decode(sys.stdout.encoding))
    p.stdout.close()
    p.wait()

    #Test set preprocessing
    print('Preprocessing test set and its dictionary')
    p = subprocess.Popen([
    'python', f'./dictionary_preprocess.py',
    '--input_dictionary_path', f'./resources/{kb}',
    '--additional_data_dir', f'../{args["input"]}/data/processed_dev',
    '--output_dictionary_path', f'../{args["input"]}/data/test_dictionary.txt',
    '--lowercase',
    '--remove_punctuation'], stdout=subprocess.PIPE, bufsize=1)
    for line in iter(p.stdout.readline, b''):
        sys.stdout.write(line.decode(sys.stdout.encoding))
    p.stdout.close()
    p.wait()

    p = subprocess.Popen([
    'python', './query_preprocess.py',
    '--input_dir', f'../{args["input"]}/data/test/',
    '--output_dir', f'../{args["input"]}/data/processed_test/',
    '--dictionary_path', f'../{args["input"]}/data/test_dictionary.txt',
    '--ab3p_path', '../Ab3P/identify_abbr',
    '--typo_path', f'./resources/ncbi-spell-check.txt',
    '--remove_cuiless', 
    '--resolve_composites',
    '--lowercase', 'true',
    '--remove_punctuation', 'true'], stdout=subprocess.PIPE, bufsize=1)
    for line in iter(p.stdout.readline, b''):
        sys.stdout.write(line.decode(sys.stdout.encoding))
    p.stdout.close()
    p.wait()

    # Constructing traindev
    if args["evalset"] == 'test':
        print("Merging train + dev")
        shutil.copytree(f'../{args["input"]}/data/processed_dev/', f'../{args["input"]}/data/processed_traindev/')
        [shutil.copy(file, f'../{args["input"]}/data/processed_traindev/') for file in glob.glob(f'../{args["input"]}/data/processed_train/*')]

    # Model training
    print(type(params['topk']))
    seed = int(round(time.time() * 1000)) % 10000 if params['seed'] == '' else params['seed']
    traindir = 'traindev' if args["evalset"] == 'test' else 'train'
    print(f'Training BioSyn model on {traindir}..')
    train_arguments = ['python', '../train.py',
    '--model_name_or_path', 'dmis-lab/biobert-base-cased-v1.1',
    '--train_dictionary_path', f'../{args["input"]}/data/train_dictionary.txt',
    '--train_dir', f'../{args["input"]}/data/processed_{traindir}',
    '--output_dir', f'../{args["input"]}',
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
    eval_args = [
    'python', '../eval.py',
    '--model_name_or_path', f'../{args["input"]}',
    '--dictionary_path', f'../{args["input"]}/data/train_dictionary.txt',
    '--data_dir', f'../{args["input"]}/data/processed_{"test" if traindir == "traindev" else "dev"}',
    '--output_dir', f'../{args["input"]}',
    '--use_cuda',
    '--topk', params['topk'],
    '--save_predictions',
    '--max_length', params['max_length']]
    if params["use_cuda"] != True:
        eval_args.remove('--use_cuda')

    p = subprocess.Popen(eval_args, stdout=subprocess.PIPE, bufsize=1)
    for line in iter(p.stdout.readline, b''):
        sys.stdout.write(line.decode(sys.stdout.encoding))
    p.stdout.close()
    p.wait()

    # Standardizing prediction
    with open(f'../{args["input"]}/predictions_eval.json', 'r') as f:
        pred = json.load(f)
    with open(f'../{args["input"]}/standardized_predictions.txt', 'a') as fh:
        for query in range(len(pred['queries'])):
            prediction_id = pred['queries'][query]['mentions'][0]['candidates'][0]['cui']
            prediction_label = pred['queries'][query]['mentions'][0]['candidates'][0]['name']
            pmid = pred['queries'][query]['mentions'][0]['pmid']
            mention = pred['queries'][query]['mentions'][0]['mention']
            ground_truth_id = pred['queries'][query]['mentions'][0]['golden_cui']
            fh.write(f'{pmid}\t{mention}\t{ground_truth_id}\t\t{prediction_id}\t{prediction_label}\n')

def cleanup(base_dir, args, kb):
    '''
    Moves outputs to entity-nom/results/ and cleans up inputs from BioSyn folder.
    '''
    dt = datetime.datetime.now()
    dt = f"{dt.year}-{dt.month}-{dt.day}-{dt.hour}:{dt.minute}"
    print(f'Cleaning up BioSyn directory and moving all outputs to {base_dir}/results/BioSyn/{args["input"]}-{dt}')
    os.makedirs(f'{base_dir}/results/BioSyn/{args["input"]}-{dt}')
    for file in glob.glob(f'../{args["input"]}/*'):
        shutil.move(file, f'{base_dir}/results/BioSyn/{args["input"]}-{dt}')
    shutil.move(f'./resources/{kb}', f'{base_dir}/results/BioSyn/{args["input"]}-{dt}/data/{kb}')
    os.chdir(f'{base_dir}')
    print('Cleaning done.')
    return f'{base_dir}/results/BioSyn/{args["input"]}-{dt}'

def extract(filename):
    '''
    Extracts the content of a standardized file.

            Parameters:
                    filename (str): Path of file to extract data from.
            Returns:
                pmid (str): Id of file. Usually a pmid but depending on file format before standardization can be something else.
                title (str): Title of the article
                abstract (str) : Abstract of the article
                data (list) : list of lists containing each mention, its location, its class and labels.
    '''
    entries = []
    pmid = filename.split("/")[-1].split("_header.txt")[0]
    with open(f"{filename}", 'r') as fh:
        lines = fh.readlines()
    title, abstract = lines[0], lines[1] 
    with open(f"{filename.split('_header')[0]}_data.txt", 'r') as fh:
        lines = fh.readlines()
        del lines[0]
    for line in lines:
        line = line.split("\t")
        entries.append(line)
    return pmid, title, abstract, entries