# for i in {1..10}; do
#     cd /home/atoffano/Downloads/models/save/models/on_dev/biosyn-biobert-bb4-habitat-$i
#     INPUT=./predictions_eval.json
#     python /home/atoffano/montages_reseau/home_maiage/menneb/entity-norm/utils/BioSyn_on_BB4/convert_BioSyn_pred_to_a2.py \
#         --input ${INPUT} \
#         --dataset /home/atoffano/Downloads/BB4/BioNLP-OST-2019_BB-norm_dev \
#         --entities Habitat
#     zip -r /home/atoffano/Downloads/biosyn-biobert-bb4-habitat-$i converted_pred/*
#     cd ..
# done
for i in {1..10}; do
    cd /home/atoffano/Downloads/Results/Lightweight/BB4-Phenotype/$i
    INPUT=./predict_result.txt
    python /home/atoffano/montages_reseau/home_maiage/menneb/entity-norm/utils/BioSyn/convert_BioSyn_pred_to_a2.py \
        --input ${INPUT} \
        --output /home/atoffano/Downloads/Results/Lightweight/BB4-Phenotype/$i \
        --dataset /home/atoffano/Downloads/BB4/BioNLP-OST-2019_BB-norm_test \
        --entities Phenotype
    cd converted_pred
    zip -r biosyn-biobert-bb4-phenotype-$i *
done
