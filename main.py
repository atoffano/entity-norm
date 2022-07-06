import argparse, os
import shutil
import subprocess
import json
import utils.biosyn
import utils.lightweight


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
    parser.add_argument("-m", "--method", required=False,
    help="Specifies which method to use. Supported: 'BioSyn' or 'Lightweight'") 
    parser.add_argument("-e", "--eval", required=False,
    help="Specify which evaluator should be used use to determine accuracy. Supported : 'Lightweight', 'BioSyn'")
    parser.add_argument("-s", "--evalset", default='test',
    help="Specify which set should be used use for evaluation. Supported : 'dev', 'test'")
    parser.add_argument("-r", "--raw", required=False,
    help="Starts the process from an original, non-standardized dataset. Supported formats: NCBI Disease as 'ncbi-disease', Bacteria Biotope 4 (full) as 'BB4' or a sub-category as 'BB4-Phenotype', 'BB4-Habitat' or 'BB4-Microorganism'.")

    parser.add_argument("--runs", default=1,
    help="Number of models to train.")

    args = vars(parser.parse_args())
    router(args)

def router(args):
    for run_nb in range(1, args['runs']+1):
        try:
            shutil.rmtree(f"{base_dir}/tmp")
        except:
            pass
        os.mkdir(f"{base_dir}/tmp")

        if args["raw"]:
            if args["input"] not in ['ncbi-disease', 'BB4', 'BB4-Phenotype', 'BB4-Habitat', 'BB4-Microorganism']:
                raise NotImplementedError()
            if args["input"] in ['BB4-Phenotype', 'BB4-Habitat', 'BB4-Microorganism']:
                bb4_subcategory = True
            input_raw_data = f"{base_dir}/data/raw/BB4" if bb4_subcategory else f'{base_dir}/data/raw/{args["input"]}'

            # Converts raw data to a standart format
            p = subprocess.run([
                'python', f'{base_dir}/utils/standardize_data.py',
                '-i', input_raw_data,
                '-o', f'{base_dir}/tmp/{args["input"]}',
                '-d', args["input"]], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            print( 'exit status:', p.returncode )
            print( 'stdout:', p.stdout.decode() )

            # Separates BB4 data into subcategories
            if bb4_subcategory:
                p = subprocess.run([
                    'python', f'{base_dir}/utils/bb4_exclude.py',
                    '-i', input_raw_data,
                    '-o', f'{base_dir}/tmp/{args["input"]}',
                    '-s', args["input"].split('BB4-')[1]], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                print( 'exit status:', p.returncode )
                print( 'stdout:', p.stdout.decode() )
        else:
            shutil.copytree(f'{base_dir}/data/standardized/{args["input"]}', f'{base_dir}/tmp/{args["input"]}')
        input_std_data = f'{base_dir}/tmp/{args["input"]}'


        # Loads model parameters
        params = json.load(open('config.json', 'r'))

        if args["method"] == 'BioSyn':
            kb = utils.biosyn.setup(base_dir, input_std_data, args)
            utils.biosyn.run(base_dir, args, params, kb, run_nb)
            utils.biosyn.cleanup(base_dir, args, kb, run_nb)

        elif args["method"] == 'Lighweight':
            pass
    shutil.rmtree(f"{base_dir}/tmp")

if __name__ == "__main__":
    main()