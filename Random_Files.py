import shutil, random, os
dirpath = 'bioRxiv_Articles3'
destDirectory = '/home/dhunt/py-venv/2021-SULI-Text-Mining1/SULI-Text-Mining-Project/Random Fe Articles'

filenames = random.sample(os.listdir(dirpath), 100)
for fname in filenames:
    srcpath = os.path.join(dirpath, fname)
    shutil.copy(srcpath, destDirectory)