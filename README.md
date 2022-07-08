# Entity-Norm

Comparative analysis of neural methods for entity normalization in the biological field.

This repository is made to store and make accessible all scripts and resulting data made to adapt different neural methods for entity normalization in the biological field.

Results sheet can be found here : https://docs.google.com/spreadsheets/d/1dDVcLoVeu9MloluEPtpPtgt2v-_XlFCQ35QN0NUJbpg/edit?usp=sharing

Individual file format handlers can be found in the utils directory and used independently as needed.
For convenience of use interactions can be made through the main.py script.

# Requirements
With the goal to make reproducing results as easy as possible, conda environements for both methods are directly available for installation through a .yaml configuration file.
```
conda env create -f lightweight_env.yaml
conda env create -f biosyn_env.yaml
```
An installation using pip is also available for both environnements. Please use a unique virtual environnement per method if you plan to use both, as package conflicts may emerge.
```
pip install biosyn_requirements.txt
pip install lightweight_requirements.txt
```

Additionnaly, Lightweight authors represent each word by a 200-dimensional word embedding computed on PubMed and MIMIC-III corpus, which can be downloaded [here](https://github.com/ncbi-nlp/BioSentVec) or directly [here](https://ftp.ncbi.nlm.nih.gov/pub/lu/Suppl/BioSentVec/BioWordVec_PubMed_MIMICIII_d200.vec.bin) and placed in `Biomedical-Entity-Linking/input/` if you plan to use this method.

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
