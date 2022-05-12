from loader import extract
import argparse, os
import glob

def main():
    '''
    Takes in .obo file of OntoBiotope annotations used to makes the bacteria biotope 4 dataset and outputs a dictionnary in BioSyn format.
    '''
    raw = "/home/atoffano/Downloads/bb4_dictionnary/OntoBiotope_BioNLP-OST-2019.obo"
    with open(raw, 'r') as fh:
        lines = fh.readlines()
    synonym = []
    for line in lines:
        if line.startswith('id'):
            label = line.strip().split(': ')[1]
        elif line.startswith('name'):
            mention = line.strip().split(': ')[1]
        elif line.startswith('synonym'):
            synonym.append(line.split('"')[1])
        elif line.startswith('is_a') and label != False:
            if synonym != []:
                mention = mention + "|" + "|".join(synonym)
            with open("/home/atoffano/Downloads/bb4_dictionnary/bb4_dict.txt", 'a') as f:
                f.write(f"{label}||{mention}\n")
            synonym = []
            label = False


if __name__ == "__main__":
    main()