import os, argparse
import glob

from numpy import average

def main():
    '''
    Parses arguments from command line

            Parameters:
                    Console arguments
                    -i / --input (str) : Input path containing files to convert (in standart format STD). Handles folder containing multiple datasets.
    '''
    # Construct the argument parser
    parser = argparse.ArgumentParser()
    # Add the arguments to the parser
    parser.add_argument("-i", "--input", required=True,
    help="Input directory containing dataset file(s).")
    args = vars(parser.parse_args())
    
    
    for dataset in os.listdir(args['input']):
        mentions_per_corpus = []
        comp_mentions = 0
        for file in glob.glob(f"{args['input']}/{dataset}/*_data.txt"):
            with open(file, 'r') as f:
                lines = f.readlines()
            for i, line in enumerate(lines):
                if "|" in line and comp_mentions != None:
                    comp_mentions += 1
            mentions_per_corpus.append(i-1)
        print(dataset)
        print(f"Number of corpus = {len(mentions_per_corpus)}")
        print(f"Total number of mentions = {sum(mentions_per_corpus)}")
        print(f"Total number of composite mentions = {comp_mentions}")
        print(f"Average nb of mentions per corpus = {average(mentions_per_corpus)}")

if __name__ == "__main__":
    main()