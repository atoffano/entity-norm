import argparse, os
import shutil
import glob
import subprocess
import json
import utils.run_biosyn
import utils.run_lightweight


def main():
    '''
    Parses arguments from command line

            Parameters:
                    Console arguments
                    -i / --input (str) : Input path containing files to convert. Handles folder containing multiple datasets.
                    -o / --output (str): Output path for both standardized and converted formats.
                    -f / --from (str) : Input format.
                    -t / --to (str) : Output format.
    '''
    global base_dir
    base_dir = os.path.dirname(__file__)


    # Construct the argument parser
    parser = argparse.ArgumentParser()

    # Add the arguments to the parser
    parser.add_argument("-i", "--input", required=True,
    help="Name of dataset folder to use located in data/standardized. ex: Full Bacteria Biotope 4 as 'BB4' or a sub category as 'BB4-Phenotype', 'BB4-Habitat' or 'BB4-Microorganism', NCBI Disease Corpus as 'ncbi-disease'. \
            Can handle a non-natively supported dataset if in a standardized format.")
    parser.add_argument("-kb", "--knowledge_base", required=True,
    help="Filename of knowledge base to use in a standardized format (i.e. in a NCBI-disease format). Must be located in data/knowledge_base/standardized")
    parser.add_argument("-m", "--method", required=False,
    help="Specifies which method to use. Supported: 'BioSyn' or 'Lightweight'") 
    parser.add_argument("-e", "--eval", required=False,
    help="Specify which evaluator should be used use to determine accuracy. Supported : 'Lightweight', 'BioSyn'")
    parser.add_argument("-s", "--set", required=False,
    help="Specify which set should be used use for training. Supported : 'train', 'traindev'")
    parser.add_argument("-r", "--raw", required=False,
    help="Starts the process from an original, non-standardized dataset. Supported formats: NCBI Disease as 'ncbi-disease', Bacteria Biotope 4 (full) as 'BB4' or a sub-category as 'BB4-Phenotype', 'BB4-Habitat' or 'BB4-Microorganism'.")

    parser.add_argument("--runs", default=1,
    help="Number of models to train.")

    args = vars(parser.parse_args())
    router(args)

def router(args):
    os.mkdir(f"{base_dir}/tmp")


    if args.raw:
        if args.raw not in ['ncbi-disease', 'BB4', 'BB4-Phenotype', 'BB4-Habitat', 'BB4-Microorganism']:
            raise NotImplementedError()
        
        if args.raw in ['BB4-Phenotype', 'BB4-Habitat', 'BB4-Microorganism']:
            bb4_subcategory = True

        shutil.rmtree(glob.glob(f"{base_dir}/data/standardize/{args.raw}*"))
        input_raw_data = f"{base_dir}/data/raw/BB4" if bb4_subcategory else f"{base_dir}/data/raw/{args.raw}"

        # Converts raw data to a standart format
        subprocess.run([
            'python', f'{base_dir}/utils/standardize_data.py',
            '-i', input_raw_data,
            '-o', f'{base_dir}/tmp/{args.raw}',
            '-d', args.raw], capture_output=True, text=True)

        # Separates BB4 data into subcategories
        if bb4_subcategory:
            subprocess.run([
                'python', f'{base_dir}/utils/bb4_exclude.py',
                '-i', input_raw_data,
                '-o', f'{base_dir}/tmp/{args.raw}',
                '-s', args.raw.split('BB4-')[1]], capture_output=True, text=True)
    
    input_std_data = f'{base_dir}/tmp/{args.raw}'


    # Loads all models parameters
    params = json.load(open('config.json', 'r'))

    if args.method == 'BioSyn':
        setup_biosyn(base_dir, args)

    elif args.method == 'Lighweight':
        subprocess.run([
            'python', f'{base_dir}/utils/run_lightweight.py',
            '-i', input_raw_data, '-o', f'{base_dir}/data/standardized/{args.raw}',
            '-d', args.raw], capture_output=True, text=True
)
    [subprocess.run([
    'python', f'{base_dir}/utils/adapt_input.py',
    '-i', input_std_data,
    '-o', f'{base_dir}/tmp',
    '-s', subset], capture_output=True, text=True) for subset in ['Habitat', 'Phenotype', 'Microorganism']]





if __name__ == "__main__":
    main()