# Script standardizing BioSyn predictions data. Can handle a few other outputs as well.
import json
import argparse, os
from genericpath import exists
from tabnanny import check
from typing import Type

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
    parser.add_argument("-d", "--dataset", required=False,
    help="Input path of Bacteria biotope test dataset.")
    parser.add_argument("-e", "--entities", required=False,
    help="Type of entities predicted. Either 'Microorganisms', 'Phenotype', 'Habitat' or a combination of those.")
    parser.add_argument("-o", "--output", default=os.getcwd(),
    help="Output path for .a2 files. Defaults to current directory.")
    args = vars(parser.parse_args())
    router(args)

def router(args):
    if args["dataset"] and args["entities"]:
        convert_to_a2(args)
    else:
        print('BioSyn Accuracy : ' + str(accuracy_biosyn(args["input"])))
        print('Lightweight Accuracy : ' + str(accuracy_lightweight(args["input"])))

def convert_to_a2(args):
    '''
    Parses prediction output (standardized_predictions.txt), extracting relevant informations.
    Then matches predictions with corresponding .a1 file before building .a2 file.
    '''
    if not os.path.exists(f"{args['output']}/converted_pred"):
        os.makedirs(f"{args['output']}/converted_pred")
    with open(args['input'], 'r') as f:
        lines = f.readlines()
    data = {}
    for line in lines:
        pmid, mention, prediction, prediction_label, ground_truth = line.strip('\n').split('\t')
        if pmid in data:
            data[pmid].append(prediction)
        else:
            data[pmid] = [prediction]
    for pmid, prediction in data.items():
        a1_lines, ftype = get_a1_matching_lines(args, pmid)
        filetype = "BB-norm-F-" if ftype else "BB-norm-"
        for pred_line, value in enumerate(prediction):
            annotation = a1_lines[pred_line].split('\t')[0]
            with open(f"{args['output']}/converted_pred/{filetype}{pmid}.a2", 'a') as fh:
                with open(f"{args['output']}/converted_pred/{filetype}{pmid}.a2", 'r') as f:
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

def get_a1_matching_lines(args, pmid):
    '''
    Matches .a1 line with its corresponding prediction.

            Parameters:
                pmid (str): corresponding .a1 file identifier (pmid).
    '''
    a1_lines = []
    if "-" in pmid:
        ftype = True
        with open(f"{args['dataset']}/BB-norm-F-{pmid}.a1", 'r') as f:
            lines = f.readlines()
    else:
        ftype = False
        with open(f"{args['dataset']}/BB-norm-{pmid}.a1", 'r') as f:
            lines = f.readlines()
    for line in lines:
        if line.split("\t")[1].split(" ")[0] in args['entities']:
            a1_lines.append(line)
    return a1_lines, ftype

def accuracy_biosyn(pred):
    with open(pred, 'r') as fh:
        lines = fh.readlines()
    accuracy = 0
    for line in lines:
        label = 0
        pmid, mention, ground_truth_id, ground_truth_label, prediction_id, prediction_label = line.strip('\n').split('\t')
        for pred in prediction_id.split('|'):
            if pred in ground_truth_id.split('|'):
                label = 1
        if label == 1:
            accuracy += 1
    return accuracy / len(lines)

def accuracy_lightweight(pred):
    with open(pred, 'r') as fh:
        lines = fh.readlines()
    accuracy = 0
    acc_cnt = 0
    for line in lines:
        pmid, mention, ground_truth_id, ground_truth_label, prediction_id, prediction_label = line.strip('\n').split('\t')
        if "|" in prediction_id or "|" in ground_truth_id:
            if len(prediction_id.split('|')) != len(ground_truth_id.split('|')):
                continue
            for pred in prediction_id.split('|'):
                if pred not in ground_truth_id:
                    continue
                else:
                    acc_cnt += 1
        elif prediction_id == ground_truth_id:
            acc_cnt += 1
    accuracy = 1.0 * acc_cnt / (len(lines)+1)
    return accuracy

def accuracy_ref(pred):
    with open(pred, 'r') as fh:
        lines = fh.readlines()
    accuracy = 0
    acc_cnt = 0
    for line in lines:
        pmid, mention, ground_truth_id, ground_truth_label, prediction_id, prediction_label = line.strip('\n').split('\t')
        score = 0
        if "|" in prediction_id or "|" in ground_truth_id:
            for pred in prediction_id.split('|'):
                if pred in ground_truth_id.split('|'):
                    score += 1

        score = score / max(len(prediction_id), len(ground_truth_id))  # multi-norm and too many pred
        accuracy += score
    return accuracy / len(lines)
    
if __name__ == "__main__":
    main()
    