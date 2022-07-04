import shutil
import subprocess

def setup_biosyn(base_dir, input_std_data, args):
    [subprocess.run([
    'python', f'{base_dir}/utils/adapt_input.py',
    '--input_file', f'{base_dir}/data/raw/ncbi-disease/NCBItrainset_corpus.txt',
    '--output_dir', f'{base_dir}/tmp/{dataset}',
    '--to', f'{base_dir}/tmp/{dataset}'], capture_output=True, text=True)]
    ####TODOOOOO

    

def run_biosyn(params):
    
    # Setting up BioSyn working environement
    params = params['biosyn']
    shutil.copy()
    # Installing BioSyn package
    [subprocess.run([
    'python', f'{base_dir}/BioSyn/setup.py', 'develop'], capture_output=True, text=True)]
    
    #Preprocessing
    print('Starting data preprocessing')
    print('Parsing raw dataset to generate mentions and concepts')
    [subprocess.run([
    'python', f'{base_dir}/BioSyn/ncbi_disease_preprocess.py',
    '--input_file', f'{base_dir}/data/raw/ncbi-disease/NCBItrainset_corpus.txt',
    '--output_dir', f'{base_dir}/tmp/{dataset}'], capture_output=True, text=True) for dataset in ['train', 'dev', 'test']]
    
    print('Preprocessing training set and its dictionary')
    [subprocess.run([
    'python', f'{base_dir}/BioSyn/query_preprocess.py',
    '--input_dictionary_path', f'{base_dir}/data/',
    '--output_dir', f'{base_dir}/tmp/{dataset}'], capture_output=True, text=True) for dataset in ['train', 'dev', 'test']]

