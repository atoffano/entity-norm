import argparse, os
import glob
import nltk
import re
import hashlib
from abbr_resolver import *

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
    parser.add_argument("-k", "--kb", required=True,
    help="Path to raw knowledge base file from which to build entity_kb.txt.")
    parser.add_argument("-m", "--merge", action='store_true',
    help="Whether to merge train and dev sets as a unique set. Defaults to True if left unspecified.")
    args = vars(parser.parse_args())

    nltk.download('punkt')
    global abbr_resolver, base_abb_dict, script_dir, word_vocab
    script_dir = os.path.split(os.path.abspath(__file__))[0]
    word_vocab = set()
    base_abb_dict = load_base_abb_dict()
    abbr_resolver = Abbr_resolver(
        ab3p_path = os.path.join(script_dir, 'Ab3P/identify_abbr')
    )

    generate(args)
    remove_duplicates_kb(args)
    mention_entity_prior(args)
    
def generate(args):
    gen_kb_from_dict(args)
    gen_data_and_mention_context(args)

def gen_kb_from_dict(args):
    '''
    Takes in a dictionnary file in standart format (medic_06_12) and outputs a knowledge base usable by lightweight.
    '''
    with open(args['kb'], "r") as fh:
        raw_dict = fh.readlines()
        for line in raw_dict:
            cuis, labels = line.strip().split('||')
            cuis = str(cuis)
            labels = str(labels)
            
            labels = resolve_base_abbr(labels.split('|'), base_abb_dict)
            for label in labels:
                label = preprocess(label)
                if len(cuis.split('|')) > 1:
                    list_cuis = cuis.split('|')
                    tmp = f"{list_cuis.pop(0)}\t{label}\t{'|'.join(list_cuis)}\n"
                else:
                    tmp = f"{cuis}\t{label}\t\n"
                with open(f"{args['output']}/entity_kb.txt", "a") as kb:
                    kb.write(tmp)

def gen_data_and_mention_context(args):
    for dataset in os.listdir(args['input']):
        for file in glob.glob(f"{args['input']}/{dataset}/*_header.txt"):
            pmid, title, abstract, data = extract(filename=file)
            text = " ".join([title.strip(),abstract.strip()])

            # apply abbreviation resolve (base + corpus specific)
            mentions = []
            for line in data:
                mentions.append(preprocess(line[2], ab3p_abbr_dict=abbr_resolver.resolve(file), additional_abbr_dict=base_abb_dict))

            for line, resolved_mention in zip(data, mentions):
                start, end, mention, _class, cui = line
                cui = cui.strip().replace("OMIM:", "")
                context = list(text)
                if ";" in start:
                    start = start.split(";")[0]
                elif ";" in end:
                    end = end.split(";")[1]
                    
                context[int(start):int(end)] = "{@marker}"
                context = "".join(context)
                context = nltk.sent_tokenize(context)

                for token in context:
                    if "{@marker}" in token:
                        context = token.replace("{@marker}", "")
                        break
                context = remove_punctuation(context)
                context = replace_numeral(context)
                if context == "":
                    context = " "
                    # Leaving context empty will break generator during training.

                # Generate processed files
                if args['merge'] and dataset in ['train', 'dev']:
                    with open(f"{args['output']}/train_data.txt", 'a') as dt:
                        dt.write(f"{pmid}\t{mention.lower()}\t{cui}\t{resolved_mention}\n")
                        
                    with open(f"{args['output']}/train_mention_context.txt", 'a') as dt:
                        dt.write(f"{pmid}\t{resolved_mention}\t{context}\n")

                else:
                    with open(f"{args['output']}/{dataset}_data.txt", 'a') as dt:
                        dt.write(f"{pmid}\t{mention.lower()}\t{cui}\t{resolved_mention}\n")
                        
                    with open(f"{args['output']}/{dataset}_mention_context.txt", 'a') as dt:
                        dt.write(f"{pmid}\t{resolved_mention}\t{context}\n")

                # kb augmentation
                if dataset in ['train', 'dev']:
                    with open(f"{args['output']}/entity_kb.txt", 'a') as dt:
                        if '|' in cui:
                            cuis = cui.split('|')
                            dt.write(f"{str(cuis.pop(0))}\t{resolved_mention}\t{'|'.join(cuis)}\n")                         
                        elif '+' in cui:
                            cuis = cui.split('+')
                            dt.write(f"{str(cuis.pop(0))}\t{resolved_mention}\t{'|'.join(cuis)}\n")
                        else:
                            dt.write(f"{cui}\t{resolved_mention}\t\n")

def remove_duplicates_kb(args):
    with open(f"{args['output']}/entity_kb.txt", "r") as kb:
        lines = kb.readlines()
    os.remove(f"{args['output']}/entity_kb.txt")
    seen_lines_hash = set()
    with open(f"{args['output']}/entity_kb.txt", "a") as kb:
        for line in lines:
            hashValue = hashlib.md5(line.rstrip().encode('utf-8')).hexdigest()
            if hashValue not in seen_lines_hash:
                kb.write(line)
                seen_lines_hash.add(hashValue)

def mention_entity_prior(args):
    mep = {}
    with open(f"{args['output']}/train_data.txt", 'r') as fh:
        lines = fh.readlines()

    for line in lines:
        cui = line.split('\t')[2].replace("OMIM:", "")
        mention = line.split('\t')[3].strip('\n')
        if '|' in cui:
            cuis = cui.split('|')
        else:
            cuis = cui.split('+')
        for cui in cuis:
            if cui not in mep:
                mep[str(cui)] = {mention : 1}
            elif mention not in mep[str(cui)]:
                mep[str(cui)][mention] = 1
            else:
                mep[str(cui)][mention] += 1

    with open(f"{args['output']}/mention_entity_prior.txt", 'a') as f:
        for cui, mentions in mep.items():
            for mention, cnt in mentions.items():
                f.write(f"{mention}\t{cui}\t{cnt}\n")


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

def expand_abbreviation(text, ab3p_abbr_dict={}, additional_abbr_dict={}):
    '''
    to expand abbreviations in a text
    :param text:
    :param ab3p_abbr_dict: abbreviations fund by Ab3p tool, this dictionary is more reliable
    :param additional_abbr_dict: pre-defined abbreviations stored in 'input/abbreviation.dict'.
    Be cautious to use it because this method can cause errors.
    :return:
    '''
    expanded_text = text
    for k, v in ab3p_abbr_dict.items():
        expanded_text = expanded_text.replace(k, v) if k in text else text

    # Note that this step can cause errors
    expanded_text = nltk.word_tokenize(expanded_text)

    for k, v in additional_abbr_dict.items():
        for index, token in enumerate(expanded_text):
            if k == token:
                expanded_text[index] = v
    expanded_text = ' '.join(expanded_text)
    return expanded_text


def remove_punctuation(text):
    '''
    :param text: a natural word sequence (a single word is acceptable)
    :return: a new sentence after removing punctuations
    '''

    # feel free to add new punctuations if needed
    punctuations = '[???!"#$%&\'()*+,-./:;<=>?@??????????????????????????????????????????????[\\]^_`{|}~]+'
    new_sentence = re.sub(punctuations, ' ', text)
    new_sentence = ' '.join(new_sentence.split())
    return new_sentence


def load_number_mapping(number_mapping_file=os.path.join(os.path.split(os.path.abspath(__file__))[0], 'number_mapping.txt')):
    '''
    read different types of numeral values
    :param number_mapping_file: mapping file
    :return: a dict that stores the mapping relationships
    '''
    number_mappings = {}
    for line in open(number_mapping_file, encoding='utf8'):
        row = line.strip('\n').split('@')
        cardinal_num = row[0]
        number_mappings[cardinal_num] = []
        number_mappings[cardinal_num].append(cardinal_num)
        for diff_type_nums in row[1].split('|'):
            diff_type_nums = diff_type_nums.split('__')
            for num in diff_type_nums:
                num = str.lower(num)
                number_mappings[cardinal_num].append(num)
        if len(row) > 2:
            number_mappings[cardinal_num].append(row[2])
    return number_mappings


def get_number(text):
    '''
    extract arabic numbers from a natural text
    :param text:
    :return:
    '''
    result = re.findall(r"\d+\.?\d*", text)
    return result


def replace_arabic_numeral(text):
    '''
    find arabic numerals and replace by spelt-out english words
    :param text:
    :return:
    '''
    numbers = get_number(text)

    if len(numbers) == 0:return text

    number_mappings = load_number_mapping()

    def get_mapping(x):
        for k, v in number_mappings.items():
            if x in v:
                return k
        return None

    for num in numbers:
        mapping = get_mapping(num)
        if not mapping:continue
        text = text.replace(num, ' ' + mapping + ' ')

    text = ' '.join(text.split())

    return text


def replace_numeral(text):
    '''
    find arabicm, roman, ordinal numerals and replace them
    :param text: must be lower words
    :return:
    '''
    text = str.lower(text)
    tokens = nltk.word_tokenize(text)
    number_tokens = tokens[:]
    number_dict = load_number_mapping()
    for k, numbers in number_dict.items():
        for num in numbers:
            if num in number_tokens:
                index = number_tokens.index(num)
                number_tokens[index] = k

    replaced_number_tokens = []
    for token in number_tokens:
        rep_token = replace_arabic_numeral(token)
        replaced_number_tokens.append(rep_token)
    return ' '.join(replaced_number_tokens).strip()


def preprocess(text, ab3p_abbr_dict={}, additional_abbr_dict={}):
    '''
    the preprocessing step described in our paper
    :param text:
    :param ab3p_abbr_dict:
    :param additional_abbr_dict:
    :return:
    '''

    # Abbreviation Expansion
    expanded_text = expand_abbreviation(text, ab3p_abbr_dict, additional_abbr_dict)

    # Puctuation Removal
    punc_text = remove_punctuation(expanded_text)

    # Numeral Replacement
    numeral_text = replace_numeral(punc_text)

    return numeral_text



if __name__ == "__main__":
    main()