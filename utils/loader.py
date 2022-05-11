import argparse, os
from genericpath import exists
from typing import Type
import glob
import shutil

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
    # Construct the argument parser
    parser = argparse.ArgumentParser()
    # Add the arguments to the parser
    parser.add_argument("-i", "--input", required=True,
    help="Input directory containing dataset file(s). Currently handled formats include Bacteria Biotope 4, NCBI Disease Corpus")
    parser.add_argument("-o", "--output", default=os.getcwd(),
    help="Converted dataset output directory")
    parser.add_argument("-f", "--from", required=True,
    help="Dataset input format. Supported formats: Bacteria Biotope 4 as [BB4] | NCBI Disease Corpus as [NCBI]")
    parser.add_argument("-t", "--to", required=True,
    help="Dataset output format. Supported formats: Bacteria Biotope 4 as [BB4] | NCBI Disease Corpus as [NCBI]")
    args = vars(parser.parse_args())
    router(args)


def router(args):
    '''
    Handles the flow of operations:

        1) Extracts data from input format -f in input folder -i.
        2) Converts it in a standardized data format.
        3) Extracts information from standart format and converts it into desired output format -t in output folder -o. 
    '''
    loc = args['input']
    if not os.path.isdir(loc):
        raise Exception("Input error: Please specify a directory containing the file(s) to convert.")
    if args['from'] == args['to']:
        raise Exception("File already in the right format!")
    elif args['from'] == 'NCBI':
        for file in os.listdir(loc):
            if is_ncbi(args, file):
                from_NCBI(args, file)
            else:
                raise NotImplementedError()
    elif args['from'] == 'BB4':
        if len(glob.glob(f"{loc}/*.a1")) == 0 and os.path.isdir(loc):
            for dataset in os.listdir(loc):
                from_BB4(args, dir=f"{loc}/{dataset}")
        elif len(loc) >= 3 and len(glob.glob(f"{loc}/*.a*")) >= 2:
            from_BB4(args, dir=f"{loc}/{dataset}") 
    elif args['from'] == 'STD':
        for dataset in os.listdir(loc):
            if args['to'] == 'NCBI':
                    to_NCBI(args, dataset)
            elif args['to'] == 'BB4':
                    to_BB4(args, dataset)
        exit()
    else:
        raise NotImplementedError()
    for dataset in os.listdir(f"{args['output']}/raw_from_{args['from']}"):
        if args['to'] == 'NCBI':
                to_NCBI(args, dataset)
        elif args['to'] == 'BB4':
                to_BB4(args, dataset)

def is_ncbi(args, filename):
    '''Verifies whether a file is conform to a ncbi disease corpus format. Returns a boolean.'''
    with open(f"{args['input']}/{filename}", 'r') as fh:
        head = fh.readlines()[:3]
    if head[0] == '\n':
        del head[0]
    if len(head[0].split("|")) == 3 and head[0].split("|")[1] == "t":
        if len(head[1].split("|")) == 3 and head[1].split("|")[1] == "a":
            return True
    return False

def from_NCBI(args, file):
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
    lines = lines + ['\n']
    for line in lines:
        line = line.strip()
        if '|t|' in line:
            pmid, title = line.split("|t|")
        elif '|a|' in line:
            abstract = line.split("|a|")[1]
            header = [title, abstract]
            standardize(args, dataset, pmid, header=header)
        elif '\t' in line:
            line = line.split("\t")
            _class = line[4]
            start = line[1]
            end = line[2]
            mention = line[3]
            labels = line [5]
            line  = start, end, mention, _class, labels
            standardize(args, dataset, pmid, line=line)

def is_ftype(filepath):
    '''Verifies whether a BB4 triplet (.txt, .a1, .a2) comes from a splitted or full article. Returns a boolean.'''
    with open(filepath, 'r') as fh:
        lines = fh.readlines()
    if lines[0].split("\t")[1].split(" ")[0] != "Title":
        return True
    return False

def from_BB4(args, dir):
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
                standardize(args, dataset, pmid, header=header)
            else:
                header = [lines[0].strip("\n"), lines[1].strip("\n")]
                standardize(args, dataset, pmid, header=header)
        with open(f"{file.split('.')[0]}.a1", 'r') as a1:
            lines = a1.readlines()
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
                line = start, end, mention, _class, labels
                standardize(args, dataset, pmid, line=line)

def standardize(args, dataset, pmid, header=None, line=None):
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
    filepath = f"{args['output']}/raw_from_{args['from']}/{dataset}/"
    if not os.path.exists(filepath):
        os.makedirs(filepath)
    if not os.path.exists(f"{filepath}{pmid}_header.txt"):
        with open(f"{filepath}{pmid}_header.txt", 'a') as f:
            f.write("title\tabstract\n")
        with open(f"{filepath}{pmid}_data.txt", 'a') as f:
            f.write("start\tend\tmention\t_class\tlabels\n")
    if header:
        title = header[0]
        abstract = header[1]
        with open(f"{filepath}{pmid}_header.txt", 'w') as f:
                    f.write(f"{title}\n{abstract}\n")
    if line:
        start, end, mention, _class, labels = line
        with open(f"{filepath}{pmid}_data.txt", 'a') as f:
                    f.write(f"{start}\t{end}\t{mention}\t{_class}\t{labels}\n")
  
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
    

def to_NCBI(args, dataset):
    '''
    Transforms a standardized dataset in the NCBI disease corpus output format.

            Parameters:
                    args (dict): Console arguments
                    dataset (str): Indicates which dataset from test train or dev is being transformed.. 
    '''
    if dataset == "dev":
        outfile = "NCBIdevelopset_corpus.txt"
    else:
        outfile = f"NCBI{dataset}set_corpus.txt"
    if args['from'] == 'STD':
        input_dir = f"{args['input']}/{dataset}"
        output_dir = f"{args['output']}/{args['input'].split('/')[-1]}_to_NCBI"
    else:
        input_dir = f"{args['output']}/raw_from_{args['from']}/{dataset}"
        output_dir = f"{args['output']}/{args['from']}_to_NCBI"
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    for file in glob.glob(f"{input_dir}/*_header.txt"):
        pmid, title, abstract, data = extract(filename=file)
        with open(f"{output_dir}/{outfile}", 'a') as f:
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
    if args['from'] == 'STD':
        input_dir = f"{args['input']}/{dataset}"
        output_dir = f"{args['output']}/{args['input'].split('_')[-1]}_to_BB4/{dataset}"
    else:
        input_dir = f"{args['output']}/raw_from_{args['from']}/{dataset}"
        output_dir = f"{args['output']}/{args['from']}_to_BB4/{dataset}"
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