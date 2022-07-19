import argparse, os, sys
import shutil, glob
import subprocess
import json
import utils.biosyn
import utils.lightweight
import utils.evaluation

def main():
    '''
    Parses arguments from command line

            Parameters:
                    Console arguments
                    -i / --input (str) : Input path containing files to convert. Handles folder containing multiple datasets.
                    -m / --method (str): Output path for both standardized and converted formats.
                    -s / --score (str) : Input format.
                    -e / --evalset (str) : Output format.
                    -o / --original (str) : Output format.

    '''
    global base_dir
    base_dir = os.path.split(os.path.abspath(__file__))[0]


    # Construct the argument parser
    parser = argparse.ArgumentParser()

    # Add the arguments to the parser
    parser.add_argument("-i", "--input", required=False,
    help="Name of dataset folder to use located in data/standardized. ex: Full Bacteria Biotope 4 as 'BB4' or a sub category as 'BB4-Phenotype', 'BB4-Habitat' or 'BB4-Microorganism', NCBI Disease Corpus as 'ncbi-disease'. \
            Can handle a non-natively supported dataset if in a standardized format and in the right directory. 'test_ncbi' is a smaller available for testing purposes.")
    parser.add_argument("-m", "--method", required=False,
    help="Specifies which method to use. Supported: 'BioSyn' or 'Lightweight'") 
    parser.add_argument("-s", "--score", required=False, nargs='+',
    help="Specify which evaluator(s) should be used use to determine accuracy. Supports multiple arguments: 'Lightweight', 'BioSyn', 'Ref', 'BB4'. Using 'BB4' will produce a folder containing predictions that can be evaluated through the BB4 online evaluation software.")
    parser.add_argument("-e", "--evalset", default='test',
    help="Specify which set should be used use for evaluation. Supported : 'dev', 'test'. defaults to 'test' if left empty.")
    parser.add_argument("-o", "--original", action='store_true',
    help="Starts the process from an original, non-standardized dataset. Supported formats: NCBI Disease as 'ncbi-disease', Bacteria Biotope 4 (full) as 'BB4' or a sub-category as 'BB4-Phenotype', 'BB4-Habitat' or 'BB4-Microorganism'.")

    parser.add_argument("--runs", default=1,
    help="Number of models to train.")

    args = vars(parser.parse_args())
    router(args)

def router(args):
    """
    Handles the flow of operations from provided arguments.
    Individual steps an all be called independently 
    Starts by checking whether to process an original dataset (--original) or start from an already processed one.
    If a Bacteria Biotope subcategory is specified as --input, standardization from the original data is made before filtering mentions of the subcategory.
    Knowledge base related to the --input will be standardized and the specified method called.
    Finally the output files will be scored according to the specified scoring methods (--score).
    """

    for _ in range(1, args['runs']+1):
        try:
            shutil.rmtree(f"{base_dir}/tmp")
        except:
            pass
        os.mkdir(f"{base_dir}/tmp")

        if args["original"]:
            # Starts from original data located in data/original.
            bb4_subcategory = True if args["input"] in ['BB4-Phenotype', 'BB4-Habitat', 'BB4-Microorganism'] else False
            input_original_data = f"{base_dir}/data/original/BB4" if bb4_subcategory else f'{base_dir}/data/original/{args["input"]}'
            if not os.path.exists(input_original_data):
                raise Exception('Original data of input not found in data/original')
            # Converts original data to a standart format
            p = subprocess.Popen([
                'python', f'{base_dir}/utils/standardize_data.py',
                '-i', input_original_data,
                '-o', f'{base_dir}/tmp/{args["input"]}/',
                '-d', args["input"]], stdout=subprocess.PIPE, bufsize=1)
            for line in iter(p.stdout.readline, b''):
                sys.stdout.write(line.decode(sys.stdout.encoding))
            p.stdout.close()
            p.wait()

            # Separates BB4 data into subcategories
            if bb4_subcategory:
                shutil.move(f'{base_dir}/tmp/{args["input"]}/', f'{base_dir}/tmp/bb4_full')
                p = subprocess.Popen([
                    'python', f'{base_dir}/utils/bb4_exclude.py',
                    '-i', f'{base_dir}/tmp/bb4_full',
                    '-o', f'{base_dir}/tmp/{args["input"]}',
                    '-s', args["input"].split('BB4-')[1]], stdout=subprocess.PIPE, bufsize=1)
                for line in iter(p.stdout.readline, b''):
                    sys.stdout.write(line.decode(sys.stdout.encoding))
                p.stdout.close()
                p.wait()

                shutil.rmtree(f'{base_dir}/tmp/bb4_full')
        elif args["input"] and args["method"]:
            try:
                shutil.copytree(f'{base_dir}/data/standardized/{args["input"]}', f'{base_dir}/tmp/{args["input"]}')
            except:
                raise NotImplementedError(f'Standardized {args["input"]} data not found in {base_dir}/data/standardized/{args["input"]}')
            
        if args["input"]:
            input_std_data = f'{base_dir}/tmp/{args["input"]}'

            # Loads model parameters
            params = json.load(open('config.json', 'r'))

            # Load knowledge base
            # Checks knowledge base existence and recreates it if needed.
            if 'BB4' in args["input"]:
                kb = 'BB4_kb.txt'
                if not os.path.exists(f'{base_dir}/data/knowledge_base/standardized/{kb}'):
                    with open(f'{base_dir}/data/knowledge_base/original/OntoBiotope_BioNLP-OST-2019.obo', 'r') as fh:
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
                                label = label + "|" + "|".join(synonym)
                            with open(f'{base_dir}/data/knowledge_base/standardized/{kb}', 'a') as f:
                                f.write(f"{cui}||{label}\n")
                            synonym = []
                            cui = False
            elif args["input"] == 'ncbi-disease':
                kb = 'ncbi-disease_kb.txt'
                if not os.path.exists(f'{base_dir}/data/knowledge_base/standardized/{kb}'):
                    shutil.copy(f'{base_dir}/data/knowledge_base/original/medic_06Jul2012.txt', f'{base_dir}/data/knowledge_base/standardized/{kb}')
                    # the ncbi-disease kb provided by BioSyn authors is considered to be in the model for standart knowledge bases format.
           
            elif args["input"] == 'test_ncbi':
                kb = 'test_ncbi_kb.txt'
                if not os.path.exists(f'{base_dir}/data/knowledge_base/standardized/{kb}'):
                    shutil.copy(f'{base_dir}/data/knowledge_base/original/test_ncbi.txt', f'{base_dir}/data/knowledge_base/standardized/{kb}')

        if args["method"] == 'BioSyn':
            # Prepares BioSyn environnement via setup(), trains model and evaluates is via run().
            # Cleans up environnement via cleanup().
            utils.biosyn.setup(base_dir, input_std_data, kb, args)
            utils.biosyn.run(base_dir, args, params, kb)
            prediction_path = utils.biosyn.cleanup(base_dir, args, kb)

        elif args["method"] == 'Lightweight':
            env_path = f'{base_dir}/Biomedical-Entity-Linking/output/{args["input"]}'
            utils.lightweight.setup(base_dir, env_path, input_std_data, kb, args)
            utils.lightweight.run(base_dir, env_path, params, args)
            prediction_path = utils.lightweight.cleanup(base_dir, env_path, args)

        if args["score"]:
            if 'Lightweight' in args["score"]:
                print(f'Lightweight accuracy evaluation = {utils.evaluation.accuracy_lightweight(f"{prediction_path}/standardized_predictions.txt")}')
            if 'BioSyn' in args["score"]:
                print(f'BioSyn accuracy evaluation = {utils.evaluation.accuracy_biosyn(f"{prediction_path}/standardized_predictions.txt")}')
            if 'Ref' in args["score"]:
                print(f'Ref accuracy evaluation = {utils.evaluation.accuracy_ref(f"{prediction_path}/standardized_predictions.txt")}')
            if 'BB4' in args["score"]:
                entity = 'BB4' if args["input"] == 'BB4' else args["input"].split('BB4-')[1]
                p = subprocess.Popen([
                'python', f'{base_dir}/utils/evaluation.py',
                '--input', f"{prediction_path}/standardized_predictions.txt",
                '--dataset', f'{base_dir}/data/original/BB4/BioNLP-OST-2019_BB-norm_test',
                '--entities', entity,
                '--output', prediction_path], stdout=subprocess.PIPE, bufsize=1)
                for line in iter(p.stdout.readline, b''):
                    sys.stdout.write(line.decode(sys.stdout.encoding))
                p.stdout.close()
                p.wait()
                print(f'Bacteria Biotope 4 prediction file (.a2) available for online evaluation.')
                print(p.returncode)
    shutil.rmtree(f"{base_dir}/tmp")
    print('Done')
    
if __name__ == "__main__":
    main()