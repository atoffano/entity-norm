#!/bin/sh
#SBATCH --mem=64g
#SBATCH --nodes=1
#SBATCH --partition=all
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:3
#SBATCH --output=/mnt/beegfs/home/toffano/entity-norm/BioSyn/log.out
#SBATCH --error=/mnt/beegfs/home/toffano/entity-norm/BioSyn/log.out
#SBATCH --job-name=biosyn

cd /mnt/beegfs/home/toffano/entity-norm/BioSyn/preprocess
DATA_DIR=../datasets
DATASET=bb4
RAW_DATA=${DATA_DIR}/raw/${DATASET}/BB4_Phenotype_to_NCBI
ENTITY=Phenotype
DICT=bb4_dict.txt
AB3P_PATH=../Ab3P/identify_abbr
iter=10

for ((i = 1 ; i <= $iter ; i++)); do
    echo PREPROCESSING --------------------------------------------------------------
    echo ----------------------------------------------------------------------------
    echo ;
    echo Parsing RAW dataset to generate mentions and concepts ----------------------
    python ./ncbi_disease_preprocess.py \
        --input_file ${RAW_DATA}/NCBItrainset_corpus.txt \
        --output_dir ${DATA_DIR}/${DATASET}/train

    python ./ncbi_disease_preprocess.py \
        --input_file ${RAW_DATA}/NCBIdevelopset_corpus.txt \
        --output_dir ${DATA_DIR}/${DATASET}/dev

    python ./ncbi_disease_preprocess.py \
        --input_file ${RAW_DATA}/NCBItestset_corpus.txt \
        --output_dir ${DATA_DIR}/${DATASET}/test

    echo ;
    echo Preprocessing TRAINset and its dictionary ----------------------------------
    python ./dictionary_preprocess.py \
        --input_dictionary_path ./resources/${DICT} \
        --output_dictionary_path ${DATA_DIR}/${DATASET}/train_dictionary.txt \
        --lowercase \
        --remove_punctuation

    python ./query_preprocess.py \
        --input_dir ${DATA_DIR}/${DATASET}/train/ \
        --output_dir ${DATA_DIR}/${DATASET}/processed_train/ \
        --dictionary_path ${DATA_DIR}/${DATASET}/train_dictionary.txt \
        --ab3p_path ${AB3P_PATH} \
        --typo_path ./resources/ncbi-spell-check.txt \
        --remove_cuiless \
        --lowercase true \
        --remove_punctuation true

    echo ;
    echo Preprocessing DEVset and its dictionary ----------------------------------
    # preprocess devset and its dictionary
    python dictionary_preprocess.py \
        --input_dictionary_path ./resources/${DICT} \
        --additional_data_dir ${DATA_DIR}/${DATASET}/processed_train/ \
        --output_dictionary_path ${DATA_DIR}/${DATASET}/dev_dictionary.txt \
        --lowercase \
        --remove_punctuation

    python ./query_preprocess.py \
        --input_dir ${DATA_DIR}/${DATASET}/dev/ \
        --output_dir ${DATA_DIR}/${DATASET}/processed_dev/ \
        --dictionary_path ${DATA_DIR}/${DATASET}/dev_dictionary.txt \
        --ab3p_path ${AB3P_PATH} \
        --typo_path ./resources/ncbi-spell-check.txt \
        --remove_cuiless \
        --lowercase true \
        --remove_punctuation true

    # echo ;
    echo Preprocessing TESTset and its dictionary ----------------------------------
    # preprocess testset and its dictionary
    python dictionary_preprocess.py \
        --input_dictionary_path ./resources/${DICT} \
        --additional_data_dir ${DATA_DIR}/${DATASET}/processed_dev/ \
        --output_dictionary_path ${DATA_DIR}/${DATASET}/test_dictionary.txt \
        --lowercase \
        --remove_punctuation

    python ./query_preprocess.py \
        --input_dir ${DATA_DIR}/${DATASET}/test/ \
        --output_dir ${DATA_DIR}/${DATASET}/processed_test/ \
        --dictionary_path ${DATA_DIR}/${DATASET}/test_dictionary.txt \
        --ab3p_path ${AB3P_PATH} \
        --typo_path ./resources/ncbi-spell-check.txt \
        --lowercase true \
        --remove_punctuation true

    echo Constructing TRAINDEV ----------------------------------------------------
    mkdir -p ${DATA_DIR}/${DATASET}/processed_traindev/
    cp -a ${DATA_DIR}/${DATASET}/processed_dev/. ${DATA_DIR}/${DATASET}/processed_traindev/
    cp -a ${DATA_DIR}/${DATASET}/processed_train/. ${DATA_DIR}/${DATASET}/processed_traindev/

    echo ;
    echo TRAINING Model biosyn-biobert-${DATASET}-$i---------------------------------------
    echo ----------------------------------------------------------------------------------
    MODEL_NAME_OR_PATH=dmis-lab/biobert-base-cased-v1.1
    OUTPUT_DIR=../tmp/biosyn-biobert-${DATASET}-$i
    python ../train.py \
        --model_name_or_path ${MODEL_NAME_OR_PATH} \
        --train_dictionary_path ${DATA_DIR}/${DATASET}/train_dictionary.txt \
        --train_dir ${DATA_DIR}/${DATASET}/processed_traindev \
        --output_dir ${OUTPUT_DIR} \
        --use_cuda \
        --topk 20 \
        --seed $i \
        --epoch 10 \
        --train_batch_size 16\
        --learning_rate 1e-5 \
        --max_length 25

    echo ;
    echo EVALUATING Model biosyn-biobert-${DATASET}-$i on devset-------------------------------
    echo --------------------------------------------------------------------------------------
    MODEL_NAME_OR_PATH=../tmp/biosyn-biobert-${DATASET}-$i
    python ../eval.py \
            --model_name_or_path ${MODEL_NAME_OR_PATH} \
            --dictionary_path ${DATA_DIR}/${DATASET}/test_dictionary.txt \
            --data_dir ${DATA_DIR}/${DATASET}/processed_test \
            --output_dir ${OUTPUT_DIR} \
            --use_cuda \
            --topk 20 \
            --max_length 25 \
            --save_predictions

    echo \
    echo CLEANUP ------------------------------------------------------------------------------
    mkdir -p /mnt/beegfs/home/toffano/entity-norm/BioSyn/models/biosyn-biobert-bb4-${ENTITY}-$i
    mv ${DATA_DIR}/${DATASET}/* /mnt/beegfs/home/toffano/entity-norm/BioSyn/models/biosyn-biobert-bb4-${ENTITY}-$i
    mv ../tmp/biosyn-biobert-bb4-$i/* /mnt/beegfs/home/toffano/entity-norm/BioSyn/models/biosyn-biobert-bb4-${ENTITY}-$i

    echo ;
    echo ITERATION $i DONE -----------------------------------------------------------
    echo -----------------------------------------------------------------------------
    echo ;
done
echo done