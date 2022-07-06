from loader import extract
import argparse, os
import glob

def from_obo():
    '''
    Takes in .obo file of OntoBiotope annotations used to makes the bacteria biotope 4 dataset and outputs a dictionnary in BioSyn format.
    '''
    raw = "/home/atoffano/Downloads/bb4_dictionnary/OntoBiotope_BioNLP-OST-2019.obo"
    with open(raw, 'r') as fh:
        lines = fh.readlines()
    synonym = []
    for line in lines:
        if line.startswith('id'):
            cui = line.strip().split(': ')[1]
        elif line.startswith('name'):
            label = line.strip().split(': ')[1]
        elif line.startswith('synonym'):
            synonym.append(line.split('"')[1])
        elif line.startswith('is_a') and cui != False:
            if synonym != []:
                label = label + "||" + "|".join(synonym)
            with open("/home/atoffano/Downloads/bb4_dictionnary/bb4_dict.txt", 'a') as f:
                f.write(f"{cui}{label}\n")
            synonym = []
            cui = False

def from_microorganisms():
    '''
    Takes in both names.dmp file from the Bacteria Biotope taxonomy dump and ids from entities of interest. Outputs a dictionnary of microorganisms in BioSyn format.
    '''
    raw = "/home/atoffano/Downloads/taxdump_2019-02-07/names.dmp"
    uids = "/home/atoffano/Downloads/BioNLP-OST-2019_BB-norm_Microorganism-ids.txt"
    with open(raw, 'r') as fh:
        lines = fh.readlines()
        lines.append('lastline')
    with open(uids, 'r') as f:
        uids = f.readlines()
        uids = [uid.strip('\n') for uid in uids]
    label = ""
    cui = None
    synonym = []
    for line in lines:
        line = line.split('\t')
        if line[0] in uids:
            cui = line[0]
            label, synonym = parse_line(line, synonym, label)
        elif cui != line[0] and cui != None:
            cui, synonym, label = save_entry(cui, synonym, label)
    if cui != None:
        cui, synonym, label = save_entry(cui, synonym, label)

def save_entry(cui, synonym, label):
    synonym = "|".join(synonym)
    label = f"{label}|{synonym}" if synonym != '' else label
    with open("/home/atoffano/Downloads/bb4_dictionnary/bb4_dict_microorganisms.txt", 'a') as f:
        f.write(f"{cui}||{label}\n")
    synonym = []
    label = ""
    cui = None
    return cui, synonym, label

def parse_line(line, synonym, label):
    if line[-2] == 'synonym':
        synonym.append(line[2])
    elif line[-2] == 'scientific name':
        label = line[2]
    return label, synonym

if __name__ == "__main__":
    from_microorganisms()

# 138	|	Borrelia Swellengrebel 1907 (Approved Lists 1980) emend. Adeolu and Gupta 2014	|		|	authority	|
# 138	|	Relapsing Fever Borrelia	|		|	synonym	|
# 139	|	ATCC 35210	|	ATCC 35210 <type strain>	|	type material	|
# 139	|	Borrelia burdorferi	|		|	synonym	|
# 139	|	Borrelia burgdorferi	|		|	synonym	|
# 139	|	Borrelia burgdorferi Johnson et al. 1984 emend. Baranton et al. 1992	|		|	authority	|
# 139	|	Borrelia burgdorferi sensu stricto	|		|	synonym	|
# 139	|	Borrelia burgdorffragment	|		|	synonym	|
# 139	|	Borreliella burgdorferi	|		|	scientific name	|
# 139	|	Borreliella burgdorferi (Johnson et al. 1984) Adeolu and Gupta 2015	|		|	authority	|
# 139	|	CIP 102532	|	CIP 102532 <type strain>	|	type material	|
# 139	|	DSM 4680	|	DSM 4680 <type strain>	|	type material	|
# 139	|	Lyme disease spirochete	|		|	genbank common name	|
# 139	|	strain B31	|	strain B31 <type strain>	|	type material	|
# 140	|	"Spirochaeta hermsi" (sic) Davis 1942	|		|	authority	|
# 140	|	Borrelia hermsii	|		|	scientific name	|
# 140	|	Borrelia hermsii (Davis 1942) Steinhaus 1946	|		|	authority	|
# 140	|	Spirochaeta hermsi	|		|	synonym	|
# 140	|	strain DAH	|	strain DAH <reference material>	|	type material	|
# 141	|	"Spirochaeta parkeri" Davis 1942	|		|	authority	|
# 141	|	Borrelia parkeri	|		|	scientific name	|