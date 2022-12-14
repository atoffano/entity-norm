import argparse, os
import glob
import shutil

def main():
    '''
    Creates a bacteria biotope dataset containing only the specified entities.
            Parameters:
                    Console arguments
                    -i / --input (str) : Input path containing files to convert (in standart format). Handles folder containing multiple datasets.
                    -o / --output (str): Output path for both standardized and converted formats.
                    -s / --separate (str) : Type of entities to whitelist. Either 'Microorganism', 'Phenotype' or 'Habitat'. Handles a combination of arguments.
    '''
    # Construct the argument parser
    parser = argparse.ArgumentParser()
    # Add the arguments to the parser
    parser.add_argument("-i", "--input", required=True,
    help="Input directory containing dataset file(s).")
    parser.add_argument("-o", "--output", default=os.getcwd(),
    help="Output directory")
    parser.add_argument("-s", "--separate", required=True, nargs='+',
    help="Type of entities to whitelist from dataset. Either 'Microorganism', 'Phenotype' or 'Habitat'. Handles multiple arguments.")
    args = vars(parser.parse_args())
    exclude(args)

def exclude(args):
    '''
    Iters over each line in each file contained in directory input. For each line, only saves those that refers to entities not blacklisted.
    '''
    # Verifies whether specified entities exist.
    for entity in args['separate']:
        if entity not in ['Microorganism', 'Phenotype', 'Habitat']:
            raise Exception("Entity to exclude not recognized. Check spelling.")

    # Whitelisting
    for directory in os.listdir(args['input']):    
        for file in glob.glob(f"{args['input']}/{directory}/*_data.txt"):
            directory = directory.split("/")[-1]
            if not os.path.exists(f"{args['output']}/{directory}"):
                os.makedirs(f"{args['output']}/{directory}")
            content = []
            entities = args['separate']
            with open(file, 'r') as fh:
                lines = fh.readlines()
            for line in lines:
                if line.split("\t")[3] in entities:
                    content.append(line)
            if len(content) > 1:
                with open(args['output'] + f"/{directory}/" + file.split('/')[-1], 'a') as f:
                    f.write('start\tend\tmention\t_class\tnorm\n')
                    for line in content:
                        f.write(line)
                shutil.copyfile(f"{file.split('_data.txt')[0]}_header.txt", f"{args['output']}/{directory}/{file.split('/')[-1].split('_data.txt')[0]}_header.txt")

if __name__ == "__main__":
    main()