import argparse, os
from genericpath import exists
from typing import Type
import glob

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

def router(args):
    loc = args['input']
    if not os.path.isdir(loc):
        raise Exception("Please specify a directory containing the file(s) to convert. Maybe you used a file as an input?")
    convert(args)

def convert(args):
    if args['from'] == args['to']:
        raise Exception("File already in the right format!")
    if args['from'] == 'NCBI' and args['to'] == 'BB4':
        for file in os.listdir(args['input']):
            if is_ncbi(args, file):
                from_NCBI(args, file)
            else:
                raise NotImplementedError()
    if args['from'] == 'BB4' and args['to'] == 'NCBI':
        if len(os.listdir(args['input'])) == 3:
            for dataset in os.listdir(args['input']):
                from_BB4(args, dir=f"{args['input']}/{dataset}")
        elif len(args['input']) >= 3 and len(glob.glob(f"{args['input']}/*.a*")) >= 2:
            from_BB4(args, dir=f"{args['input']}/{dataset}") 

def is_ncbi(args, filename):
    with open(f"{args['input']}/{filename}", 'r') as fh:
        head = fh.readlines()[:3]
    if head[0] == '\n':
        del head[0]
    if len(head[0].split("|")) == 3 and head[0].split("|")[1] == "t":
        if len(head[1].split("|")) == 3 and head[1].split("|")[1] == "a":
            return True
    return False

def standardize(args, dataset, id, header=None, line=None):
    if not os.path.exists(f"{args['output']}/{dataset}"):
        os.mkdir(f"{args['output']}/{dataset}")
    filepath = f"{args['output']}/{dataset}/{id}"
    if not os.path.exists(f"{filepath}_header.txt"):
        with open(f"{filepath}_header.txt", 'a') as f:
            f.write("title\tabstract\n")
        with open(f"{filepath}_data.txt", 'a') as f:
            f.write("start\tend\tmention\t_class\tlabels\n")
    if header:
        title = header[0]
        abstract = header[1]
        with open(f"{filepath}_header.txt", 'w') as f:
                    f.write(f"{title}\n{abstract}\n")
    if line:
        start, end, mention, _class, labels = line
        with open(f"{filepath}_data.txt", 'a') as f:
                    f.write(f"{start}\t{end}\t{mention}\t{_class}\t{labels}\n")

def from_BB4(args, dir):
    testset = False
    if "dev" in dir:
        dataset = "dev"
    elif "train" in dir:
        dataset = "train"
    elif "test" in dir:
        dataset = "test"
        testset = True
    for file in glob.glob(f"{dir}/*.txt*"):
        ftype = True if "BB-norm-F-" in file else False
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

def from_NCBI(args, file):
    if "trainset" in file:
        dataset = "train"
    elif "developset" in file:
        dataset = "dev"
    elif "testset" in file:
        dataset = "test"
    else:
        raise NotImplementedError
    if not os.path.exists(f"{args['output']}/{dataset}"):
        os.mkdir(f"{args['output']}/{dataset}")
    with open(f"{args['input']}/{file}", 'r') as fh:
        lines = fh.readlines()    
    lines = lines + ['\n']
    for line in lines:
        line = line.strip()
        if '|t|' in line:
            pmid, title = line.split("|t|")
        elif '|a|' in line:
            abstract = line.split("|a|")[1]
            header = title, abstract
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
        

# def BB4_to_NCBI(args, dir):
#     testset = False
#     if "dev" in dir:
#         output = f"{args['output']}/NCBI_developset_corpus.txt"
#     elif "train" in dir:
#         output = f"{args['output']}/NCBI_trainset_corpus.txt"
#     elif "test" in dir:
#         output = f"{args['output']}/NCBI_testset_corpus.txt"
#         testset = True
#     for file in glob.glob(f"{dir}/*.txt*"):
#         ftype = True if "BB-norm-F-" in file else False
#         if ftype:
#             tmp = file.split("/")[-1].split("-")
#             pmid = "".join(f"{tmp[3]}-{tmp[4].split('.')[0]}")
#         else:
#             pmid = file.split("/")[-1].split("-")[2].split(".")[0]
#         with open(file, 'r') as fh:
#             lines = fh.readlines()
#             with open(output, 'a') as f:
#                 f.write("\n")
#                 if ftype:
#                     f.write(f"{pmid}|t|{pmid}\n")
#                     abstract = ""
#                     abstract = abstract.join(line.strip("\n") for line in lines)
#                     f.write(f"{pmid}|a|{abstract}\n")
#                 else:
#                     f.write(f"{pmid}|t|{lines[0]}")
#                     f.write(f"{pmid}|a|{lines[1]}")
#                 with open(f"{file.split('.')[0]}.a1", 'r') as a1:
#                     lines = a1.readlines()
#                     for line in lines:
#                         line = line.split("\t")
#                         if line[1].split(" ")[0] in ["Title", "Paragraph"]:
#                             continue
#                         index = int(line[0].strip("T"))
#                         block = line[1].split(" ")
#                         _class = block[0]
#                         start = block[1]
#                         end = block[2]
#                         mention = line[2].strip()
#                         if testset:
#                             f.write(f"{pmid}\t{start}\t{end}\t{mention}\t{_class}\tMockLabel\n")
#                         else:
#                             with open(f"{file.split('.')[0]}.a2", 'r') as a2:
#                                 a2lines = a2.readlines()
#                             label = []
#                             for a2line in a2lines:
#                                 if a2line.split(" ")[1].split("Annotation:T")[1] == str(index):
#                                     label.append(a2line.split("Referent:")[1].strip("\n"))
#                             label = "|".join(label)
#                             f.write(f"{pmid}\t{start}\t{end}\t{mention}\t{_class}\t{label}\n")

# def ncbi_to_BB4(args, file):
#     vset = file.replace('.txt', '')
#     os.mkdir(f"{args['output']}/{vset}")
#     with open(f"{args['input']}/{file}", 'r') as fh:
#         lines = fh.readlines()    
#     lines = lines + ['\n']
#     cnt = 1
#     num_lines = 1
#     header = False
#     for line in lines:
#         line = line.strip()
#         if '|t|' in line:
#             pmid, title = line.split("|t|")
#             with open(f"{args['output']}/{vset}/BB-norm-{pmid}.txt", 'a') as f:
#                 f.write(f"{title}\n")
#         elif '|a|' in line:
#             abstract = line.split("|")[2]
#             with open(f"{args['output']}/{vset}/BB-norm-{pmid}.txt", 'a') as f:
#                 f.write(f"{abstract}\n\n")
#         elif '\t' in line:
#             line = line.split("\t")
#             cui = line[-1].split('|')
#             with open(f"{args['output']}/{vset}/BB-norm-{pmid}.a1", 'a') as f:
#                 if header == False:
#                     title_size = len(title)
#                     f.write(f"T1\tTitle O {title_size}\t{title}\nT2\tParagraph {title_size} {len(abstract) + title_size}\t{abstract}\n")
#                     header = True
#                 f.write(f"T{cnt+3}\t{line[4]} {line[1]} {line[2]}\t{line[3]}\n")
#             with open(f"{args['output']}/{vset}/BB-norm-{pmid}.a2", 'a') as f:
#                 if len(cui) > 1:
#                     for i in cui:
#                         f.write(f"N{num_lines}\t{line[0]} Annotation:T{cnt+3} Referent:{i}\n")
#                         num_lines += 1
#                 elif len(cui) == 1:
#                         f.write(f"N{num_lines}\t{line[0]} Annotation:T{cnt+3} Referent:{line[5]}\n")
#                         num_lines += 1
#             cnt += 1
#         elif line == '':
#             header = False
#             cnt = 0
#             num_lines = 1
#             continue
#         else:
#             raise NotImplementedError()

if __name__ == "__main__":
    router(args)