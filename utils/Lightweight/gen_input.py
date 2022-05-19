import argparse, os
from compileall import compile_path
import glob

def main():
    '''
    Parses arguments from command line

            Parameters:
                    Console arguments
                    -i / --input (str) : Path containing input files. Handles folder containing multiple datasets.
                    -o / --output (str): Output path for both standardized and converted formats. Defaults to current working directory.
    '''
    # Construct the argument parser
    parser = argparse.ArgumentParser()
    # Add the arguments to the parser
    parser.add_argument("-i", "--input", required=True,
    help="Input directory containing dataset file(s). Files must be in a standart (STD) format.")
    parser.add_argument("-o", "--output", default=os.getcwd(),
    help="Converted dataset output directory")
    parser.add_argument("-f", "--from", required=True,
    help="Dataset input format. Supported formats: Bacteria Biotope 4 as [BB4] | NCBI Disease Corpus as [NCBI]")
    parser.add_argument("-t", "--to", required=True,
    help="Dataset output format. Supported formats: Bacteria Biotope 4 as [BB4] | NCBI Disease Corpus as [NCBI]")
    args = vars(parser.parse_args())
    generate(args)

def generate(args):
    loc = args['input']
    for dataset in os.listdir(loc):
        for file in glob.glob(f"{loc}/{dataset}/*_header.txt"):
            pmid, title, abstract, data = extract(filename=file)
            text = title.strip().join(abstract.strip())
            for line in data:
                start, end, mention, _class, labels = line
                context = text
                del context[start:end]

                with open(f"{args['output']}/{dataset}_data.txt", 'a') as dt:
                    dt.write(f"{pmid}{mention}{labels}{}")

def gen_dict(args):
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



#     with open(f"{args['output']}/entity_kb.txt", 'a') as kb:
#     if "|" in mention:
#         comp_mention = mention.split("|")
#         tmp = f"{comp_mention[0]}\t{mention}\t"
#         del comp_mention[0]
#         tmp += "|".join(comp_mention)
#     else:
#         kb.write(f"{labels}\t{mention}"))


def extract(filename):
    '''
    Extracts the content of a standardized file.

            Parameters:
                    filename (str): Path of file to extract data from.
            Returns:
                pmid (str): Id of file. Usually a pmid but depending on file format before standardization can be something else.
                title (str): Title of the article
                abstrat (str) : Abstract of the article
                data (list) : list of lists containing each mention, its location, its class and labels.
    '''
    data = []
    pmid = filename.split("/")[-1].split("_header.txt")[0]
    with open(f"{filename}", 'r') as fh:
        lines = fh.readlines()
    title, abstract = lines[0], lines[1] 
    with open(f"{filename.split('_header')[0]}_data.txt", 'r') as fh:
        lines = fh.readlines()
        del lines[0]
    for line in lines:
        line = line.split("\t")
        data.append(line)
    return pmid, title, abstract, data

if __name__ == "__main__":
    main()