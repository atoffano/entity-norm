# Script standardizing BioSyn predictions data. Can handle a few other outputs as well.
import json
import argparse, os
from genericpath import exists
from tabnanny import check
from typing import Type
from tqdm import tqdm

def main():
    '''
    Parses arguments from command line

            Parameters:
                    Console arguments
                    -i / --input (str) : Input file prediction_eval.json.
                    -d / --dataset (str): Input path of Bacteria biotope test dataset.
                    -e / --entities (str): Type of entities predicted. Either "Microorganisms", "Phenotype", "Habitat" or a combination of those.
                    -o / --output (str): Output path for both standardized and converted formats. Defaults to input path.
    '''
    # Construct the argument parser
    parser = argparse.ArgumentParser()
    # Add the arguments to the parser
    parser.add_argument("-i", "--input", required=True,
    help="Input path containing prediction_eval.json")
    parser.add_argument("-d", "--dataset", required=True,
    help="Input path of Bacteria biotope test dataset.")
    parser.add_argument("-e", "--entities", required=True,
    help="Type of entities predicted. Either 'Microorganisms', 'Phenotype', 'Habitat' or a combination of those.")
    parser.add_argument("-o", "--output", default=os.getcwd(),
    help="Output path for .a2 files. Defaults to current directory.")
    args = vars(parser.parse_args())
    convert(args)


def convert(args):
    '''
    Parses prediction output of BioSyn (predictions_eval.json), extracting relevant informations including cui and file pmid.
    Then matches predictions with corresponding .a1 file before building .a2 file.
    '''
    if not os.path.exists(f"{args['output']}/converted_pred"):
        os.makedirs(f"{args['output']}/converted_pred")
    with open(args['input'], 'r') as f:
        pred = json.load(f)
    data = {}
    for query in tqdm(range(len(pred['queries']))):
        cui = pred['queries'][query]['mentions'][0]['candidates'][0]['cui']
        pmid = pred['queries'][query]['mentions'][0]['pmid']
        if pmid in data:
            data[pmid].append(cui)
        else:
            data[pmid] = [cui]
    for key, values in data.items():
        a1_lines, ftype = get_a1_matching_lines(args, key)
        filetype = "BB-norm-F-" if ftype else "BB-norm-"
        for pred_line, value in enumerate(values):
            annotation = a1_lines[pred_line].split('\t')[0]
            with open(f"{args['output']}/converted_pred/{filetype}{key}.a2", 'a') as fh:
                with open(f"{args['output']}/converted_pred/{filetype}{key}.a2", 'r') as f:
                    n = len(f.readlines())
                if len(value.split("|")) > 1:
                    for label in value.split("|"):
                        ontology = 'OntoBiotope' if 'OBT:' in label else 'NCBI_Taxonomy'
                        fh.write(f"N{n+1}\t{ontology} Annotation:{annotation} Referent:{label}\n")
                        n+=1
                else:
                    ontology = 'OntoBiotope' if 'OBT:' in value else 'NCBI_Taxonomy'
                    fh.write(f"N{n+1}\t{ontology} Annotation:{annotation} Referent:{value}\n")
                    n+=1

def get_a1_matching_lines(args, key):
    '''
    Matches .a1 line with its corresponding prediction.

            Parameters:
                key (str): corresponding .a1 file identifier (pmid).
    '''
    a1_lines = []
    if "-" in key:
        ftype = True
        with open(f"{args['dataset']}/BB-norm-F-{key}.a1", 'r') as f:
            lines = f.readlines()
    else:
        ftype = False
        with open(f"{args['dataset']}/BB-norm-{key}.a1", 'r') as f:
            lines = f.readlines()
    for line in lines:
        if line.split("\t")[1].split(" ")[0] in args['entities']:
            a1_lines.append(line)
    return a1_lines, ftype

if __name__ == "__main__":
    main()