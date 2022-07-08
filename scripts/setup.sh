#!/bin/bash
cd "${0%/*}"
cd ..
# BioSyn
git clone https://github.com/dmis-lab/BioSyn.git
echo Modding BioSyn..
rm BioSyn/data_loader.py BioSyn/utils.py
cp utils/mods/BioSyn/utils.py ./BioSyn
cp utils/mods/BioSyn/data_loader.py ./BioSyn/src/biosyn

echo Installing package BioSyn
cd BioSyn
python setup.py develop
cd ..
echo BioSyn init done!

# Lightweight
git clone https://github.com/tigerchen52/Biomedical-Entity-Linking.git
echo Modding LightWeight..
rm Biomedical-Entity-Linking/source/data_utils.py
rm Biomedical-Entity-Linking/source/train.py
rm Biomedical-Entity-Linking/source/generate_candidate.py
rm Biomedical-Entity-Linking/source/load_data.py
cp -r utils/mods/Lightweight/input/* Biomedical-Entity-Linking/input
chmod -R +x Biomedical-Entity-Linking/source/input/Ab3P/identify_abbr
cp -r utils/mods/Lightweight/source/* Biomedical-Entity-Linking/source
echo Lightweight init done!
