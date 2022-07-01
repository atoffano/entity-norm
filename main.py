import argparse, os
import shutil
import glob
import subprocess

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
    parser.add_argument("-i", "--input", required=False,
    help="Input directory containing a custom dataset file(s). Must be in a standardized format.")
    parser.add_argument("-o", "--output", default=f"{base_dir}/output",
    help="Output directory of checkpoints and predictions files.")
    parser.add_argument("-d", "--dataset", required=False,
    help="Dataset to use: Full Bacteria Biotope 4 as 'BB4' or a sub category as 'BB4-Phenotype', 'BB4-Habitat' or 'BB4-Microorganism' | NCBI Disease Corpus as 'NCBI'.")
    parser.add_argument("-e", "--eval", required=False,
    help="Specify which evaluator should be used use to calculate accuracy. Supported : 'Lightweight', 'BioSyn'")
    parser.add_argument("-s", "--set", required=False,
    help="Specify which set should be used use for training. Supported : 'train', 'traindev'")
    parser.add_argument("-r", "--raw", required=False,
    help="Starts the process from an original, non-stadardized dataset. Supported formats: NCBI Disease as 'ncbi-disease', Bacteria Biotope 4. 'BB4'")

    args = vars(parser.parse_args())
    router(args)

def router(args):
    if args.raw:
        if args.raw not in ['ncbi-disease', 'BB4']:
            raise NotImplementedError()
        shutil.rmtree(glob.glob(f"{base_dir}/data/standardize/{args.raw}*"))
        input_data = f"{base_dir}/data/raw/{args.raw}"
        subprocess.run([
            'python', f'{base_dir}/utils/standardize_data.py',
            '-i', input_data, '-o', f'{base_dir}/data/standardized/{args.raw}',
            '-d', args.raw], capture_output=True, text=True
)
        if args.raw == 'BB4':
            [subprocess.run([
            'python', f'{base_dir}/utils/bb4_exclude.py',
            '-i', input_data,
            '-o', f'{base_dir}/data/standardized/{args.raw}_{subset}',
            '-s', subset], capture_output=True, text=True) for subset in ['Habitat', 'Phenotype', 'Microorganism']]
    if args.dataset:
        input_std_data = f"{base_dir}/data/standardized/{args.dataset}"
        




if __name__ == "__main__":
    main()