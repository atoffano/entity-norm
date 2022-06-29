import argparse, os
from genericpath import exists
from typing import Type
import glob
import shutil
import hashlib

def main():
    '''
    Parses arguments from command line

            Parameters:
                    Console arguments
                    -i / --input (str) : Input path containing files to convert. Handles folder containing multiple datasets.
                    -o / --output (str): Output path for both standardized and converted formats.
                    -f / --from (str) : Input format.
    '''
    # Construct the argument parser
    parser = argparse.ArgumentParser()
    # Add the arguments to the parser
    parser.add_argument("-i", "--input", required=True,
    help="Input directory containing dataset file(s). Currently handled formats include Bacteria Biotope 4, NCBI Disease Corpus")
    parser.add_argument("-o", "--output", default=os.getcwd(),
    help="Converted dataset output directory")
    parser.add_argument("-d", "--dataset", required=True,
    help="Input dataset. Supported datasets: Bacteria Biotope 4 as [BB4] | NCBI Disease Corpus as [NCBI]")
    args = vars(parser.parse_args())
    router(args)


def router(args):
    '''
    Handles the flow of operations:

        1) Extracts data from input format -f in input folder -i.
        2) Converts it in a standardized data format.
    '''
    loc = args['input']
    if not os.path.isdir(loc):
        raise Exception("Input error: Please specify a directory containing the file(s) to convert.")
    
    elif args['dataset'] == 'NCBI':
        for file in os.listdir(loc):
            standardize_NCBI(args, file)

    elif args['dataset'] == 'BB4':
        if len(glob.glob(f"{loc}/*.a1")) == 0 and os.path.isdir(loc):
            for dataset in os.listdir(loc):
                standardize_BB4(args, dir=f"{loc}/{dataset}")
        elif len(loc) >= 3 and len(glob.glob(f"{loc}/*.a*")) >= 2:
            standardize_BB4(args, dir=f"{loc}/{dataset}") 
        exit()

    else:
        raise NotImplementedError()

def standardize_NCBI(args, file):
    '''
    Converts data from a ncbi disease corpus format to a standardized one.

            Parameters:
                    args (dict): Console arguments
                    file (str): path to ncbi data file
    '''
    if "trainset" in file:
        dataset = "train"
    elif "developset" in file:
        dataset = "dev"
    elif "testset" in file:
        dataset = "test"
    else:
        raise NotImplementedError
    with open(f"{args['input']}/{file}", 'r') as fh:
        lines = fh.readlines() 
    entries = []   
    lines = lines + ['\n']
    for line in lines:
        line = line.strip()
        if '|t|' in line:
            pmid, title = line.split("|t|")
        elif '|a|' in line:
            abstract = line.split("|a|")[1]
            header = [title, abstract]
        elif '\t' in line:
            line = line.split("\t")
            _class = line[4]
            start = line[1]
            end = line[2]
            mention = line[3]
            labels = line [5]
            entries.append([start, end, mention, _class, labels])
        elif line == '' and entries != []:
            standardize(args, dataset, pmid, header, entries)
            entries = []

def is_ftype(filepath):
    '''
    Verifies whether a BB4 triplet (.txt, .a1, .a2) comes from a splitted or full article. Returns a boolean.
    '''
    with open(filepath, 'r') as fh:
        lines = fh.readlines()
    if lines[0].split("\t")[1].split(" ")[0] != "Title":
        return True
    return False

def standardize_BB4(args, dir):
    '''
    Converts data from a Bacteria Biotope 4 format to a standardized one.

            Parameters:
                    args (dict): Console arguments
                    file (str): path to ncbi data file
    '''
    testset = False
    if "dev" in dir:
        dataset = "dev"
    elif "train" in dir:
        dataset = "train"
    elif "test" in dir:
        dataset = "test"
        testset = True
    for file in glob.glob(f"{dir}/*.txt*"):
        ftype = is_ftype(f"{file.split('.txt')[0]}.a1")
        if ftype:
            tmp = file.split("/")[-1].split("-")
            pmid = "".join(f"{tmp[3]}-{tmp[4].split('.')[0]}")
        else:
            pmid = file.split("/")[-1].split("-")[2].split(".")[0]
        with open(file, 'r') as fh:
            lines = fh.readlines()
            if ftype:
                abstract = "".join(line.strip("\n") for line in lines)
                header = ["", abstract]
            else:
                title = lines[0].strip("\n")
                corpus = [line.strip("\n") for line in lines[1:]]
                corpus = "".join(corpus)
                header = [title, corpus]
        with open(f"{file.split('.')[0]}.a1", 'r') as a1:
            lines = a1.readlines()
            entries = []
            for line in lines:
                line = line.split("\t")
                if line[1].split(" ")[0] in ["Title", "Paragraph"]:
                    continue
                index = int(line[0].strip("T"))
                block = line[1].split(" ")
                _class = block[0]
                start = block[1]
                end = block[2]
                mention = line[2].strip()
                if testset:
                    labels = "MockLabel"
                else:
                    with open(f"{file.split('.')[0]}.a2", 'r') as a2:
                        a2lines = a2.readlines()
                    labels = []
                    for a2line in a2lines:
                        if a2line.split(" ")[1].split("Annotation:T")[1] == str(index):
                            labels.append(a2line.split("Referent:")[1].strip("\n"))
                    labels = "|".join(labels)
                entries.append([start, end, mention, _class, labels])
        standardize(args, dataset, pmid, header, entries)

def standardize(args, dataset, pmid, header, entries):
    '''
    Takes in the content of a file and outputs it in a standardized format.

            Parameters:
                    args (dict): Console arguments
                    dataset (str): Indicates which dataset to integrate output file with.
                    header (tuple) : Contains (title, abstract) of a file.
                    line (list) : Contains (start, end, mention, _class, labels) of a file.
            Output:
                Generates a corresponding file in a standardized format.
    '''
    filepath = f"{args['output']}/raw_from_{args['dataset']}/{dataset}/"
    if not os.path.exists(filepath):
        os.makedirs(filepath)
    if not os.path.exists(f"{filepath}{pmid}_header.txt"):
        init_file(filepath, pmid)
    elif os.path.exists(f"{filepath}{pmid}_header.txt"):
        temp = pmid.split("_")
        if len(temp) == 1:
            pmid = f"{pmid}_2"
        else:
            pmid = f"{temp[0]}_{int(temp[1]) + 1}"
            init_file(filepath, pmid)

    title = header[0]
    abstract = header[1]
    with open(f"{filepath}{pmid}_header.txt", 'w') as f:
                f.write(f"{title}\n{abstract}\n")
    with open(f"{filepath}{pmid}_data.txt", 'a') as f:
        for entry in entries:
            start, end, mention, _class, labels = entry
            f.write(f"{start}\t{end}\t{mention}\t{_class}\t{labels}\n")

def init_file(filepath, pmid):
    '''
    Creates an empty template meant to store a file's data
    '''
    with open(f"{filepath}{pmid}_header.txt", 'a') as f:
        f.write("title\tabstract\n")
    with open(f"{filepath}{pmid}_data.txt", 'a') as f:
        f.write("start\tend\tmention\t_class\tlabels\n")

if __name__ == "__main__":
    main()