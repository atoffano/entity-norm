import argparse, os
from genericpath import exists
from typing import Type
import glob
import shutil

def main():
    '''
    Parses arguments from command line and serves as a router.

            Parameters:
                    Console arguments
                    -i / --input (str) : Input path containing files to convert. Handles folder containing multiple datasets.
                    -o / --output (str): Output path for both standardized and converted formats.
                    -t / --to (str) : Output format.
    '''
    # Construct the argument parser
    parser = argparse.ArgumentParser()
    # Add the arguments to the parser
    parser.add_argument("-i", "--input", required=True,
    help="Input directory containing dataset file(s). Currently handled formats include Bacteria Biotope 4, NCBI Disease Corpus")
    parser.add_argument("-o", "--output", default=os.getcwd(),
    help="Converted dataset output directory")
    parser.add_argument("-t", "--to", required=True,
    help="Dataset output format. Supported formats: Bacteria Biotope 4 as 'BB4' | NCBI Disease Corpus as 'ncbi-disease'")
    args = vars(parser.parse_args())

    loc = args['input']
    for dataset in os.listdir(f"{loc}"):
        if args['to'] == 'ncbi-disease' or args['to'] == 'BioSyn':
                to_NCBI(args, dataset)
        elif args['to'] == 'BB4':
                to_BB4(args, dataset)


def extract(filename):
    '''
    Extracts the content of a standardized file.

            Parameters:
                    filename (str): Path of file to extract data from.
            Returns:
                pmid (str): Id of file. Usually a pmid but depending on file format before standardization can be something else.
                title (str): Title of the article
                abstract (str) : Abstract of the article
                data (list) : list of lists containing each mention, its location, its class and labels.
    '''
    entries = []
    pmid = filename.split("/")[-1].split("_header.txt")[0]
    with open(f"{filename}", 'r') as fh:
        lines = fh.readlines()
    title, abstract = lines[0], lines[1] 
    with open(f"{filename.split('_header')[0]}_data.txt", 'r') as fh:
        lines = fh.readlines()
        del lines[0]
    for line in lines:
        line = line.split("\t")
        entries.append(line)
    return pmid, title, abstract, entries
    

def to_NCBI(args, dataset):
    '''
    Transforms a standardized dataset in the NCBI disease corpus output format.

            Parameters:
                    args (dict): Console arguments
                    dataset (str): Indicates which dataset from test train or dev is being transformed.. 
    '''
    outfile = f"{dataset}set_corpus.txt"
    # if args['from'] == 'STD':
    #     input_dir = f"{args['input']}/{dataset}"
    #     output_dir = f"{args['output']}/{args['input'].split('/')[-1]}_to_NCBI"
    # else:
        # input_dir = f"{args['output']}/raw_from_{args['from']}/{dataset}"
        # output_dir = f"{args['output']}/{args['from']}_to_NCBI"
    if not os.path.exists(args["output"]):
        os.makedirs(args["output"])
    for file in glob.glob(f'{args["input"]}/{dataset}/*_header.txt'):
        pmid, title, abstract, data = extract(filename=file)
        with open(f'{args["output"]}/{outfile}', 'a') as f:
            f.write(f"\n{pmid}|t|{title}{pmid}|a|{abstract}")
            for line in data:
                line = "\t".join(line)
                f.write(f"{pmid}\t{line}")

def to_BB4(args, dataset):
    '''
    Transforms a standardized dataset in the Bacteria Biotope 4 output format.

            Parameters:
                    args (dict): Console arguments
                    dataset (str): Indicates which dataset from test train or dev is being transformed.. 
    '''
    # if args['from'] == 'STD':
    #     input_dir = f"{args['input']}/{dataset}"
    #     output_dir = f"{args['output']}/{args['input'].split('_')[-1]}_to_BB4/{dataset}"
    # else:
    #     input_dir = f"{args['output']}/raw_from_{args['from']}/{dataset}"
    #     output_dir = f"{args['output']}/{args['from']}_to_BB4/{dataset}"
    input_dir = f'{args["input"]}/dataset'
    output_dir = f'{args["output"]}/dataset'
    os.makedirs(output_dir)
    for file in glob.glob(f"{input_dir}/*_header.txt"):
        pmid, title, abstract, data = extract(filename=file)
        shutil.copyfile(f"{file}", f"{output_dir}/BB-norm-{pmid}.txt")
        with open(f"{output_dir}/BB-norm-{pmid}.txt", 'a') as f:
            f.write("\n")
        with open(f"{output_dir}/BB-norm-{pmid}.a1", 'a') as f:
            f.write(f"T1\tTitle 0 {len(title)}\t{title}T2\tParagraph {len(title)} {len(abstract) + len(title)}\t{abstract}")
            for i, line in enumerate(data):
                start, end, mention, _class, labels = line 
                f.write(f"T{i+3}\t{_class} {start} {end}\t{mention}\n")
                with open(f"{output_dir}/BB-norm-{pmid}.a2", 'a') as fh:
                    cui = labels.strip().split("|")
                    if len(cui) > 1:
                        for k, lab in enumerate(cui):
                            fh.write(f"N{i+k+1}\t{pmid} Annotation:T{i+3} Referent:{lab}\n")
                            k += 1
                    elif len(cui) == 1:
                            fh.write(f"N{i+1}\t{pmid} Annotation:T{i+3} Referent:{labels}")


if __name__ == "__main__":
    main()