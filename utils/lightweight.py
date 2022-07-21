import shutil
import subprocess
import os, sys
import glob
import datetime

def setup(base_dir, env_path, input_std_data, kb, args):
    '''
    Checks environnement and preprocesses data.

            Parameters:
                    base_dir (str): Path of entity-norm folder
                    env_path (str): Path of lightweight folder (Biomedical-Entity-Linking)
                    input_std_data (str) : Path to folder containing stadardized datasets
                    kb (str) : Path to relevant knowledge base.
            Output:
                Processed files from input.
    '''
    os.makedirs(f'{env_path}/candidates')
    os.makedirs(f'{env_path}/context')
    os.makedirs(f'{env_path}/embed')
    if not os.path.exists(f'{base_dir}/Biomedical-Entity-Linking/input/BioWordVec_PubMed_MIMICIII_d200.vec.bin'):
        raise Exception("BioWordVec 200-dimensional word embeddings were not found in Biomedical-Entity-Linking/input.\nPlease refer to Lightweight author's github to download them.")
    shutil.copy(f'{base_dir}/Biomedical-Entity-Linking/output/ncbi/char_vocabulary.dict', f'{env_path}')
    shutil.copy(f'{base_dir}/Biomedical-Entity-Linking/output/ncbi/word_vocabulary.dict', f'{env_path}')

    # Preprocess
    preprocess_arguments = [
    'python3', f'{base_dir}/Biomedical-Entity-Linking/input/preprocess.py',
    '--input', input_std_data,
    '--output', env_path,
    '--kb', f'{base_dir}/data/knowledge_base/standardized/{kb}',
    '--merge']
    if args["evalset"] != 'test':
        preprocess_arguments.remove('--merge')
    p = subprocess.Popen(preprocess_arguments, stdout=subprocess.PIPE, bufsize=1)
    for line in iter(p.stdout.readline, b''):
        sys.stdout.write(line.decode(sys.stdout.encoding))
    p.stdout.close()
    p.wait()

    # Setup environnement
    [shutil.move(file, f'{env_path}/context') for file in glob.glob(f'{env_path}/*_context.txt')]

    return env_path

def run(base_dir, env_path, params, args):
    '''
    1) Generates word embeddings and candidates.
    2) Trains model with parameters from config.json
    3) Inference

            Parameters:
                    base_dir (str): Path of entity-norm folder
                    env_path (str): Path of lightweight folder (Biomedical-Entity-Linking)
                    params (str) : Parameters specifying how the model should be trained.
                    args (dict) : arguments from main.py
            Output:
                Prediction files.
    '''
    print("Generating Word Embeddings and Candidates")
    p = subprocess.Popen(['python3', f'{base_dir}/Biomedical-Entity-Linking/source/generate_candidate.py',
    "--input", env_path,
    "--base_dir", f'{base_dir}/Biomedical-Entity-Linking'], stdout=subprocess.PIPE, bufsize = 1)
    for line in iter(p.stdout.readline, b''):
        sys.stdout.write(line.decode(sys.stdout.encoding))
    p.stdout.close()
    p.wait()

    # Loading Lightweight training parameters
    params = params['Lightweight']
    train_arguments = [
    'python3', f'{base_dir}/Biomedical-Entity-Linking/source/train.py',
    '-dataset', args["input"]]
    for key, value in params.items():
        if value == '' or value == False:
            continue
        else:
            train_arguments.append(f'-{key}')
            train_arguments.append(str(value))

    # Training
    print(f'Training Lightweight model on {args["input"]}...')
    os.chdir(f'{base_dir}/Biomedical-Entity-Linking/output')
    p = subprocess.Popen(train_arguments, stdout=subprocess.PIPE, bufsize=1)
    for line in iter(p.stdout.readline, b''):
        sys.stdout.write(line.decode(sys.stdout.encoding))
    p.stdout.close()
    p.wait()

def cleanup(base_dir, env_path, args):
    '''
    Moves outputs to entity-nom/results/ and cleans up inputs from Biomedical-Entity-Linking folder.
    '''
    dt = datetime.datetime.now()
    dt = f"{dt.year}-{dt.month}-{dt.day}-{dt.hour}:{dt.minute}"
    print(f'Cleaning up Biomedical-Entity-Linking directory and moving all outputs to {base_dir}/results/Biomedical-Entity-Linking/{args["input"]}-{dt}')
    os.makedirs(f'{base_dir}/results/Biomedical-Entity-Linking/{args["input"]}-{dt}')    
    [shutil.move(file, f'{base_dir}/results/Biomedical-Entity-Linking/{args["input"]}-{dt}') for file in glob.glob(f'{base_dir}/Biomedical-Entity-Linking/checkpoints/*')]
    shutil.move(f'{env_path}', f'{base_dir}/results/Biomedical-Entity-Linking/{args["input"]}-{dt}')
    print('Cleaning done.')
    return f'{base_dir}/results/Biomedical-Entity-Linking/{args["input"]}-{dt}'
