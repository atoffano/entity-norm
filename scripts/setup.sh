cd ..
    
# BioSyn
git clone https://github.com/dmis-lab/BioSyn.git
rm BioSyn/eval.py BioSyn/utils.py
cp utils/mods/BioSyn/* ./BioSyn

# Lightweight
git clone https://github.com/tigerchen52/Biomedical-Entity-Linking.git
rm Biomedical-Entity-Linking/source/data_utils.py
rm Biomedical-Entity-Linking/source/train.py
rm Biomedical-Entity-Linking/source/generate_candidate.py
rm Biomedical-Entity-Linking/source/load_data.py
cp utils/mods/Lightweight/input/* Biomedical-Entity-Linking/input
cp utils/mods/Lightweight/source/* Biomedical-Entity-Linking/source
