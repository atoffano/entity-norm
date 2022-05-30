import argparse, os
from email.mime import base
from gettext import find
from compileall import compile_path
import glob
import nltk
import re

import Abbr_resolver


def main():
    '''
    Parses arguments from command line

            Parameters:
                    Console arguments
                    -i / --input (str) : Path containing input files. Handles folder containing multiple datasets.
                    -o / --output (str): Output path for both standardized and converted formats. Defaults to current working directory.
                    -d / --dataset (str): Dataset input format. Supported formats: Bacteria Biotope 4 as [bb4] | NCBI Disease Corpus as [ncbi].
                    -k / --kb (str) : Path to raw knowledge base file from which to build entity_kb.txt.
    '''
    # Construct the argument parser
    parser = argparse.ArgumentParser()
    # Add the arguments to the parser
    parser.add_argument("-i", "--input", required=True,
    help="Input directory containing dataset file(s). Files must be in a standart (STD) format.")
    parser.add_argument("-o", "--output", default=os.getcwd(),
    help="Converted dataset output directory")
    parser.add_argument("-d", "--dataset", required=True,
    help="Dataset input format. Supported formats: Bacteria Biotope 4 as [bb4] | NCBI Disease Corpus as [ncbi]")
    parser.add_argument("-k", "--kb", required=True,
    help="Path to raw knowledge base file from which to build entity_kb.txt.")
    args = vars(parser.parse_args())

    nltk.download('punkt')
    global number_dict, abbr_resolver, base_abb_dict
    number_dict = load_number_mapping()
    base_abb_dict = load_base_abb_dict()
    abbr_resolver = Abbr_resolver(
    ab3p_path = "../input/Ab3p/WordData/"
    )

    generate(args)

def load_base_abb_dict():
    base_abb_dict = {}
    with open("../input/abbreviation.dict", 'r') as f:
        lines = f.readlines()
    for line in lines:
        base_abb_dict[line[0]] = line[1]
    return base_abb_dict

def load_number_mapping():
    number_dict = {}
    for line in open('../input/number_mapping.txt', encoding='utf8'):
        row = line.strip('\n').split('@')
        cardinal = row[0]
        number_dict[cardinal] = []
        number_dict[cardinal].append(cardinal)
        for diff_type_nums in row[1].split('|'):
            diff_type_nums = diff_type_nums.split('__')
            for num in diff_type_nums:
                num = str.lower(num)
                number_dict[cardinal].append(num)
    return number_dict
    
def generate(args):
    if args['dataset']=='bb4':
        gen_kb_from_bb4_dict(args)
    elif args['dataset']=='ncbi':
        gen_kb_from_ncbi_dict(args)
    gen_data_and_mention_context(args)

def gen_data_and_mention_context(args):
    for dataset in os.listdir(args['input']):
        for file in glob.glob(f"{args['input']}/{dataset}/*_header.txt"):
            pmid, title, abstract, data = extract(filename=file)
            text = " ".join([title.strip(),abstract.strip()])

            # apply abbreviation resolve (base + corpus specific)
            mentions = []
            for line in data:
                mentions.append(line[2])
            mentions = resolve_abbr(mentions, base_abb_dict)
            for mention in mentions:
                del mention[0]
            dynamic_abbr_dict = abbr_resolver.resolve(text)
            mentions = resolve_abbr(mentions, dynamic_abbr_dict)

            for line, resolved_mention in zip(data, mentions):
                start, end, mention, _class, cui = line
                cui = cui.strip()
                context = list(text)
                context[int(start):int(end)] = "{@marker}"
                context = "".join(context)
                context = nltk.sent_tokenize(context)

                for token in context:
                    if "{@marker}" in token:
                        context = token.replace("{@marker}", "")
                        break
                
                # rm punctuation, resolve numerals & lowercase
                mention, resolved_mention, context = list(map(basic_processing, (mention, resolved_mention, context)))

                with open(f"{args['output']}/{dataset}_data.txt", 'a') as dt:
                    dt.write(f"{pmid}\t{mention}\t{cui}\t{resolved_mention}\n")
                    
                with open(f"{args['output']}/{dataset}_mention_context.txt", 'a') as dt:
                    dt.write(f"{pmid}\t{mention}\t{context}\n")

def gen_kb_from_bb4_dict(args):
    '''
    Takes in .obo file of OntoBiotope annotations used to makes the bacteria biotope 4 dataset and outputs a knowledge base.
    '''
    with open(args['kb'], 'r') as fh:
        lines = fh.readlines()
    cui = ""
    with open(f"{args['output']}/entity_kb.txt", "a") as kb:
        for line in lines:
            if line.startswith('id'):
                cui = line.strip().split(': ')[1]
            elif line.startswith('name'):
                label = line.strip().split(': ')[1]
                label = basic_processing(label)
                kb.write(f"{cui}\t{label}\n")
            elif line.startswith('synonym'):
                synonym = line.split('"')[1]
                synonym = basic_processing(synonym)
                kb.write(f"{cui}\t{synonym}\n")
            else:
                cui = ""

def gen_kb_from_ncbi_dict(args):
    '''
    Takes in a dictionnary file in ncbi dataset format (medic_06_12) and outputs a knowledge base.
    '''
    with open(args['kb'], "r") as fh:
        raw_dict = fh.readlines()
        for line in raw_dict:
            cuis, labels = line.strip().split('||')
            cuis = str(cuis)
            labels = str(labels)
            
            for label in labels.split('|'):
                label = basic_processing(label)
                if len(cuis.split('|')) > 1:
                    list_cuis = cuis.split('|')
                    tmp = f"{list_cuis.pop(0)}\t{label}\t{'|'.join(list_cuis)}\n"
                else:
                    tmp = f"{cuis}\t{label}\t\n"
                with open(f"{args['output']}/entity_kb.txt", "a") as kb:
                    kb.write(tmp)

def extract(filename):
    '''
    Extracts the content of a standardized file.

            Parameters:
                    filename (str): Path of file to extract data from.
            Returns:
                pmid (str): Id of file. Usually a pmid but depending on file format before standardization can be something else.
                title (str): Title of the article
                abstrat (str) : Abstract of the article
                data (list) : list of lists containing for each mention its location in the text, class and labels as [start, end, mention, _class, labels].
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

def resolve_abbr(mentions, abbr_dict):
    result = []
    for mention in mentions:
        prev_mention = mention
        while True:
            mention_tokens = prev_mention.split()
            result_tokens = []
            for token in mention_tokens:
                token = token.strip()

                if '/' in token:
                    _slash_result = []
                    for t in token.split('/'):
                        t = t.strip()
                        t = abbr_dict.get(t, t)
                        _slash_result.append(t)
                    token = '/'.join(_slash_result)

                if token.endswith(','):
                    token = token.replace(',', '')
                    abbr_dict : dict
                    token = abbr_dict.get(token, token)
                    token += ','
                else:
                    token = abbr_dict.get(token, token)
                result_tokens.append(token)
            result_mention = ' '.join(result_tokens)
            if result_mention == prev_mention:
                break
            else:
                prev_mention = result_mention
        result.append([mention, result_mention])
    return result

def basic_processing(sentence):
    # remove punctuation
    remove_chars = '[’!"#$%&\'()*+,-./:;<=>?@，。?★、…【】《》？“”‘’！[\\]^_`{|}~]+'
    result = re.sub(remove_chars, ' ', sentence)
    result = ' '.join(result.split())

    #resolve numerals & lowercase
    ret = []
    for token in result.split():
        if token in number_dict:
            token = number_dict.get(token)
        ret.append(token)
    return " ".join(ret).lower()


if __name__ == "__main__":
    main()