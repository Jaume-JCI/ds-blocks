import shutil
import glob
import os

exclude = ['test_data']
d = glob.glob ('test_*')
#d = [x for x in d if x not in exclude]
print (f'Removing folders: \n{d}')
print ('Proceed? (y/n)')
#proceed = input (' > ')
proceed='y'
if proceed == 'y':
    for folder in d:
        shutil.rmtree (folder)

    #d = glob.glob ('test_*')
    #assert d==exclude
