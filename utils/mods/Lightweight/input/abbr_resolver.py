import subprocess
import os
import pdb


class Abbr_resolver():

    def __init__(self, ab3p_path):
        self.ab3p_path = ab3p_path
        
    def resolve(self, corpus_path):
        result = subprocess.run([self.ab3p_path, corpus_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        line = result.stdout.decode('utf-8')
        if "Path file for type cshset does not exist!" in line:
            raise Exception(line)
        elif "Cannot open" in line:
            raise Exception(line)
        elif "failed to open" in line:
            raise Exception(line)
        lines = line.split("\n")
        result = {}
        for line in lines:
            if len(line.split("|"))==3:
                sf, lf, _ = line.split("|")
                sf = sf.strip()
                lf = lf.strip()
                result[sf] = lf
        
        return result

def load_base_abb_dict():
    script_dir = os.path.dirname(__file__)
    base_abb_dict = {}
    with open(os.path.join(script_dir, "abbreviation.dict"), 'r') as f:
        lines = f.readlines()
    for line in lines:
        base_abb_dict[line[0]] = line[1]
    return base_abb_dict

def resolve_base_abbr(mentions, abbr_dict):
    result = []
    for mention in mentions:
        mention_tokens = mention.split()
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
        result.append(result_mention)
    return result

def resolve_dynamic_abbr(mentions, abbr_dict):
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
        result.append(result_mention)
    return result
