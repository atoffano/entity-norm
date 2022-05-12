# Entity-Norm
***

Comparative analysis of neural methods for entity normalization in the biological field.

This repository is made to store all results and scripts obtained by adapting different neural methods for entity normalization in the biological field.

Results sheet can be found here : https://docs.google.com/spreadsheets/d/1dDVcLoVeu9MloluEPtpPtgt2v-_XlFCQ35QN0NUJbpg/edit?usp=sharing

File format handlers can be found in the utils directory.

# Scripts
Directory containing all scripts used for preprocessing datasets, training and evaluating models. 

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
