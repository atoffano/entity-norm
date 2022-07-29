# Entity-Norm

### Comparative analysis of neural methods for entity normalization in the biological field.

This work is an attempt to make interoperable multiple datasets and methods in the entity normalization task, in order to evaluate the robustness of those methods.
This repository is made to store and make accessible all scripts and resulting data.

Two SoTA normalization methods (2022) have been adapted so far:
- [Lightweight](https://github.com/tigerchen52/Biomedical-Entity-Linking)[1], a method using Word2Vec embeddings from the paper [A Lightweight Neural Model for Biomedical Entity Linking](https://arxiv.org/abs/2012.08844)
- [BioSyn](https://github.com/dmis-lab/BioSyn)[2], a method using BioBERT embeddings and morpho-syntaxic representation of mentions and labels from the paper [Biomedical Entity Representations with Synonym Marginalization](https://arxiv.org/abs/2005.00239)
    

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

Additionnaly, Lightweight authors represent each word by a 200-dimensional word embedding computed on PubMed and MIMIC-III corpus. \
The embeddings file can be downloaded from [here](https://github.com/ncbi-nlp/BioSentVec) or directly [here](https://ftp.ncbi.nlm.nih.gov/pub/lu/Suppl/BioSentVec/BioWordVec_PubMed_MIMICIII_d200.vec.bin) and must be placed in `Biomedical-Entity-Linking/input` if you plan to use this method.

Lastly, environnement should be initialized by running `setup.sh`
```
$ bash setup.sh
```

## Usage
Most if not all interactions should be made through the main.py script. \
Example :
```
$ python main.py \
    --input ncbi-disease \
    --method BioSyn \
    --score BioSyn Lightweight \
    --evalset test \
    --original
    --runs 10
```
This example trains n=10 BioSyn models on the train+dev set using ncbi-disease data, and evaluates each model on the test set using both BioSyn and Lightweight's scoring functions.

All files produced along the way, including output predictions, can be found in the `results` folder.

### Arguments
`--input` refers to the folder name containing standardized data in `data/standardized`. Currently available are Bacteria Biotope 4 as 'BB4' or a sub category as 'BB4-Phenotype', 'BB4-Habitat' or 'BB4-Microorganism', NCBI Disease Corpus as 'ncbi-disease'.

You can specify a certain method to us (e.g. BioSyn or Lightweight) by using the `--method` argument.

`--score` allows to choose which evaluating functions to calculate accuracy with. Multiple functions can be used at once.
Arguments are as follow:
- `BioSyn` : BioSyn's scoring function. Very lenient towards mentions normalized by multiple concepts.
- `Lightweight` : Lightweight's scoring function. Strict towards mentions normalized by multiple concepts.
- `Ref` : A custom made scoring function that acts as a middleground between the previous functions by balancing the rewards of multiple concept normalization according to the difficulty of the normalization.

`--evalset` indicates whether the model should be tested on the `test` set or `dev` set and subsequently whether the training should be done on the training set or the traindev set.

`--original` does not take any additional argument. Data used by the pipeline comes from already standardized data stored in `data/standardized`. \
Using this argument specify that the used data must come from the non-standardized, original data (e.g. as is published online) stored in `data/original`.
Original data can be downloaded here:
- [ncbi-disease](https://www.ncbi.nlm.nih.gov/CBBresearch/Dogan/DISEASE/)
- [Bacteria Biotope 4](https://sites.google.com/view/bb-2019/dataset?authuser=0)

`--runs` argument allows the user to train multiple models.

### Parameters
Parameters specific to each method can be configured through the `config.json` file. Those include among others the learning rate, number of epochs, decay rate and seed.
Default parameters are based on those specified by the authors of each method.

## Standard format
To allow for interoperability of methods, datasets are converted from their original format to a common one.
Each dataset is split in `train`, `dev` and `test` folder each containing two files per text sharing a uniq id (usually its pmid for biomedical articles):
- `{id}_header.txt` contains the raw text. The first line is the title (in case of an article) while the second line contains the abstract.
- `{id}_data.txt` is a tabulation-separated `'\t'` file containing the data itself, starting with a header. \
Mentions normalized by multiple concepts are separated by a '|' sign.

Example: `23402_data.txt` 
```
start	end	mention	_class	norm
77	94	neonatal jaundice	SpecificDisease	D007567
137	155	lamellar cataracts	SpecificDisease	C535342|OMIM:116800
```

Data can be standardized anew from original by running the following command line:
```
$ python main.py --input {dataset} --original
```
Output will be found in the `tmp` folder.

## Adding a custom dataset
Adding your own customized dataset can be done in a few steps:
- Standardize your dataset. 
    If you are not using text containing a title, simply leave the first line of {id}_header empty.
    Make sure to attribute a uniq id to each file.
- Add your converted dataset in a folder within 'data/standardized' with a name of your choosing.
- Create a knowledge base of your data with concept separated from labels by '||'. Labels and synonym concepts are separated by a simple '|'. \
    Example:
    ```
    C566983|611252||Spastic Paraplegia 32, Autosomal Recessive|SPG32
    D054363||Solitary Fibrous Tumor|Benign Fibrous Mesothelioma
    ```
- Store your knowledge base in `data/knowledge_base/standardized/{NAME}.txt` with `{NAME}` matching your dataset folder name.
- Run main.py with the `--input` argument matching your dataset folder name.

## Utils
Contains multiple file format handlers, allowing to convert datasets/files to input formats of different entity normalization methods.

`standardize_data.py` : Allows conversion of datasets to a standardized format. Can be used independently of main.py.

**Usage**:
```
python loader.py \
    --input {DATASET_PATH} \ # Input directory containing dataset file(s).
    --output {OUTPUT_PATH} \  # Converted dataset output directory
    --dataset {DATASET} # Input dataset format. Supported: Bacteria Biotope 4 as [BB4] | NCBI Disease Corpus as [NCBI]
```

-----

`bb4_exclude.py` : Creates a Bacteria Biotope dataset subcategory containing only the specified entities.
Input must be in a standardized format.
Handles the following entities: `Phenotype`, `Habitat`, `Microorganism`.

**Usage**:
```
python bb4_exclude.py \
    --input {INPUT_PATH}\ # Input path of Bacteria Biotope 4 dataset.
    --output {OUTPUT_PATH} \ # Output directory.
    --separate {ENTITY} \ # Type of entities to whitelist from dataset. Either 'Microorganism', 'Phenotype' or 'Habitat'. Handles multiple arguments.
```
-----

`evaluation.py` : Evaluates predictions using different accuracy functions.

**Usage**: \
`--input` is the only required argument.
Other arguments are only required for a Bacteria Biotope 4 test set evaluation (see below).
```
python convert_BioSyn_pred_to_a2.py \
    --input {INPUT_PATH} \ # Input path containing prediction file.
    --output {OUTPUT_PATH} \ # Output path for Bacteria Biotope converted predictions.
    --entities {ENTITIES} \ # Subset of entity types predicted. Either "Microorganisms", "Phenotype" or "Habitat". Handles multiple arguments.
    --dataset {DATASET_PATH} \ # Original Bacteria Biotope 4 dataset containing unmodified .a1 files.
```
*Special case* :
Ground truth for normalizations of the Bacteria Biotope 4 test set aren't made publicly available, a dedicated evaluator can be found online.
As such, this script outputs a folder containing predictions formatted in a way that is interpretable by the [Bacteria Biotope 2019 online evaluation software](http://bibliome.jouy.inra.fr/demo/BioNLP-OST-2019-Evaluation/index.html).
Please compress the output folder as .gz before submitting.

-----

`biosyn.py` : Script acting as a pipeline to run the BioSyn method.
Folder environnement is set up inside the BioSyn directory then populated with the data.
The data is then processed, the model trained and inference subsequently made.
Lastly the folder environnement is cleaned up and produced files stored in the `results` folder.

`lightweight.py` : Script acting as a pipeline to run the Lightweight method.
Works in a similar way to the BioSyn pipeline.

## Additional informations

The `utils/mods` folder stores slightly modified versions of Lightweight and BioSyn scripts.
The modified BioSyn scripts allow certain informations to pass through the pipeline unhindered and do not change the way the code works.
However part of lightweight method's code (Mainly the context, coherence and mention-entity prior components of the code) are unavailable. As such I had to code those morsels following the paper's specifications. Divergence arising between the author's results and those of this implementation most likely come from this part of the code.

The `utils/old` folder stores prototypes of the current working scripts. While useless to most users, some functions could find some uses in very specific tasks (ex: converting a standardized dataset back to a ncbi-disease or Bacteria Biotope format).

## References
[1] Zhang Y, Chen Q, Yang Z, Lin H, Lu Z. BioWordVec, improving biomedical word embeddings with subword information and MeSH. Scientific Data. 2019. \
[2] Sung, M., Jeon, H., Lee, J., Kang, J. Biomedical Entity Representations with Synonym Marginalization. In Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics. 2020.