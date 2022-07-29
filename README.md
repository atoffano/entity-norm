### Entity-Norm

Comparative analysis of neural methods for entity normalization in the biological field.

This repository is made to store and make accessible all scripts and resulting data made to adapt different neural methods for entity normalization in the biological field.

Results sheet can be found [here](https://docs.google.com/spreadsheets/d/1dDVcLoVeu9MloluEPtpPtgt2v-_XlFCQ35QN0NUJbpg/edit?usp=sharing)

Scripts for evaluation and data manipulation can be found in the `utils` directory and used independently as needed.
For convenience of use interactions should be made through the main.py script.

## Requirements
With the goal to make reproducing results as easy as possible, conda environements for both methods are directly available for installation through a .yaml configuration file.
```
$ conda env create -f lightweight_env.yaml
$ conda env create -f biosyn_env.yaml
```
An installation using pip is also available for both environnements. Please use a unique virtual environnement per method if you plan to use both, as package conflicts may emerge.
```
$ pip install biosyn_requirements.txt
$ pip install lightweight_requirements.txt
```

Additionnaly, Lightweight authors represent each word by a 200-dimensional word embedding computed on PubMed and MIMIC-III corpus, which can be downloaded [here](https://github.com/ncbi-nlp/BioSentVec) or directly [here](https://ftp.ncbi.nlm.nih.gov/pub/lu/Suppl/BioSentVec/BioWordVec_PubMed_MIMICIII_d200.vec.bin) and must be placed in `Biomedical-Entity-Linking/input/` if you plan to use this method.

Lastly, environnement should be initialized by running `setup.sh`
```
$ bash setup.sh
```

## Usage
Most if not all interactions should be made through the main.py script.
Example :
```
$ python main.py \
    --input ncbi-disease \
    --method BioSyn \
    --score BioSyn Lightweight \
    --evalset test \
    --original
```

# Arguments
`--input` refers to the folder name containing standardized data in 'data/standardized'. Currently available are Bacteria Biotope 4 as 'BB4' or a sub category as 'BB4-Phenotype', 'BB4-Habitat' or 'BB4-Microorganism', NCBI Disease Corpus as 'ncbi-disease'.

You can specify a certain method to us (e.g. BioSyn or Lightweight) by using the `--method` argument.

'--score' allows to choose which evaluating functions to calculate accuracy with. Multiple functions can be used at once.
Individual characteristics are as follow:
- BioSyn : BioSyn's scoring function. Very lenient towards mentions normalized by multiple concepts.
- Lightweight : Lightweight's scoring function. Strict towards mentions normalized by multiple concepts.
- Ref : A custom made scoring function that takes into account the inherent difficulty of multiple concept          normalization while not being too lenient.

'--evalset' handles whether the model should be tested on the `test` set or `dev` set and subsequently whether training should be done on training set or train+dev set.

`--original` does not take any additional argument. Data used by the pipeline comes from already standardized data stored in 'data/standardized'. Using this argument redirects data used to original data (available online) stored in 'data/original'.
Original data can be downloaded here:
- [ncbi-disease](https://www.ncbi.nlm.nih.gov/CBBresearch/Dogan/DISEASE/)
- [Bacteria Biotope 4](https://sites.google.com/view/bb-2019/dataset?authuser=0)

# Parameters
Parameters specific to each method can be configured through the `config.json` file. Those include among others the learning rate, number of epochs, decay rate and seed.
Default parameters are based on those specified by the authors of each method.

## Standard format
To allow for interoperability of methods, datasets are converted from their original format to a common one.
Each dataset is split in `train`, `dev` and `test` folder each containing two files per text sharing a uniq id (usually its pmid for biomedical articles):
- [id]_header.txt
- [id]_data.txt
'[id]_header.txt' contains the raw text. The first line is the title (in case of an article) while the second line contains the abstract.
'[id]_data.txt' is a tabulation-separated ('\t') file containing the data itself, with a header in the first line. Mentions normalized by multiple concepts are separated by a '|' sign.
Example: `23402_data.txt`
1    start	end	mention	            _class	        norm
2    77	    94	neonatal jaundice	SpecificDisease	D007567
3    137	155	lamellar cataracts	SpecificDisease	C535342|OMIM:116800

Data can be standardized anew from original by running the following command line:
```
$ python main.py --input [dataset] --original
```
Output will be found in the `tmp` folder.

## Adding a custom dataset
Adding your own customized dataset can be done in a few steps:
- Standardize your dataset.
- Add your converted dataset in a folder within 'data/standardized' with a name of your choosing.
- Create a knowledge base of your data with concept separated from labels by '||'. Labels and synonym concepts are separated by a simple '|'.
        Example:
       ```C566983|611252||Spastic Paraplegia 32, Autosomal Recessive|SPG32
        D054363||Solitary Fibrous Tumor, Pleural|Benign Fibrous Mesothelioma```
- Store your knowledge base in `data/knowledge_base/standardized/{NAME}.txt` with {NAME} matching your dataset folder name.
- Run main.py with the `--input` argument matching your dataset folder name.

# Utils
Contains multiple file format handlers, allowing to convert datasets/files to input formats of different entity normalization methods.

**loader.py** : Allows conversion of datasets between different formats. Each dataset will be converted both to a standardized format and the desired output.
Handles the following file formats and associated denominators:
* NCBI Disease Corpus - 'NCBI'  
* Bacteria Biotope 4 - 'BB4'  
* Standardized format - 'STD'  

Usage:
```
python loader.py \
    --input DATASET_PATH \
    --output OUTPUT_PATH \ # Optional, defaults to current working directory if not specified.
    --from XXX \ # Dataset type denominator
    --to XXX \ # Dataset type denominator
```

**generate_dictionnary_BioSyn.py** : Handles BioSyn dictionnary creation from the Bacteria Biotope 4 dataset.  


**bb4_exclude.py** : Allows blacklisting of specific entity types in the Bacteria Biotope 4 dataset.  
Handles the following entities:   
* Phenotype  
* Habitat  
* Microorganism  

Usage:
```
python bb4_exclude.py \
    --input INPUT_PATH\ # Input path of Bacteria Biotope 4 dataset in a standardized format only (STD)
    --output OUTPUT_PATH \ # Optional. Defaults to current working directory if left unspecified.
    --exclude ENTITY \ # Exclude specified entities. Can handle multiple arguments.
```


**convert_BioSyn_pred_to_a2** : Formats BioSyn predictions in a .a2 file format which can be evaluated by the Bacteria biotope 4 online evaluation software.  
*Some BioSyn files needs to be replaced for this to work properly*  
Usage:
```
python convert_BioSyn_pred_to_a2.py \
    --input INPUT_PATH \ # BioSyn prediction file path (predictions_eval.json)
    --output OUTPUT_PATH \ # Optional. Defaults to current working directory if left unspecified.
    --entities ENTITY \ # Subset of entity types evaluated. Either "Microorganisms", "Phenotype", "Habitat". Handles multiple arguments.
    --dataset DATASET_PATH \ # Original Bacteria biotope 4 dataset containing unmodified .a1 files.
```
