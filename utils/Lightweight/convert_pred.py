import argparse, os

def main():
    '''
    Parses arguments from command line

            Parameters:
                    Console arguments
                    -i / --input (str) : Path containing input files. Handles folder containing multiple datasets.
                    -o / --output (str): Output path for both standardized and converted formats. Defaults to current working directory.
                    -d / --dataset (str): Dataset input format. Supported formats: Bacteria Biotope 4 as [bb4] | NCBI Disease Corpus as [ncbi].
    '''
    # Construct the argument parser
    parser = argparse.ArgumentParser()
    # Add the arguments to the parser
    parser.add_argument("-i", "--input", required=True,
    help="Input directory containing lightweight prediction file(s).")
    parser.add_argument("-d", "--dataset", required=True,
    help="Input path of Bacteria biotope test dataset.")
    parser.add_argument("-e", "--entities", required=True,
    help="Type of entities predicted. Either 'Microorganisms', 'Phenotype', 'Habitat' or a combination of those.")
    parser.add_argument("-o", "--output", default=os.getcwd(),
    help="output dir")
    args = vars(parser.parse_args())
    convert(args)

def convert(args):
    with open(args["input"], 'r') as f:
        lines = f.readlines()
    data = {}
    for line in lines:
        pmid = line.split('\t')[0]
        cui = line.split('\t')[4]
        if pmid in data:
            data[pmid].append(cui)
        else:
            data[pmid] = [cui]
    
    if not os.path.exists(f"{args['output']}/converted_pred/"):
        os.makedirs(f"{args['output']}/converted_pred/")
    for key, values in data.items():
        a1_lines, ftype = get_a1_matching_lines(args, key)
        filetype = "BB-norm-F-" if ftype else "BB-norm-"
        for pred_line, value in enumerate(values):
            annotation = a1_lines[pred_line].split('\t')[0]
            with open(f"{args['output']}/converted_pred/{filetype}{key}.a2", 'a') as fh:
                with open(f"{args['output']}/converted_pred/{filetype}{key}.a2", 'r') as f:
                    n = len(f.readlines())
                if len(value.split("|")) > 1:
                    for cui in value.split("|"):
                        ontology = 'OntoBiotope' if 'OBT:' in cui else 'cui_less'
                        fh.write(f"N{n+1}\t{ontology} Annotation:{annotation} Referent:{cui}\n")
                        n+=1
                else:
                    ontology = 'OntoBiotope' if 'OBT:' in value else 'cui_less'
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