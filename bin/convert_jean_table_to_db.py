#!/usr/bin/env python
"""Take metadata information from jean and adds to database."""
import pandas as pd
from pymongo import MongoClient
import numpy as np

def parse_meig_dat(fname):
    header = pd.MultiIndex.from_tuples([
        ('magic', 'id'),
        ('magic', 'srr'),
        ('magic', 'srp'),
        ('magic', 'project description'),
        ('magic', 'reference'),
        ('magic', 'authors'),
        ('magic', 'biosample'),
        ('magic', 'sample summary'),
        ('magic', 'RNA aim: total, polyA, nascent, small RNA, 3\', 5\''),
        ('magic', 'Experiment detail'),
        ('magic', 'Targeted experiment'),
        ('magic', 'Targeted experiment details'),
        ('magic', 'Genomic DNA'),
        ('mieg', 'Biological class, control'),
        ('mieg', 'Control'),
        ('mieg', 'Treatment'),
        ('mieg', 'Treatment details'),
        ('mieg', 'Knockdown'),
        ('mieg', 'Knockdown details'),
        ('mieg', 'Overexpression'),
        ('mieg', 'Overexpression details'),
        ('mieg', 'Marker gene'),
        ('mieg', 'Driver gene or promoter'),
        ('nlm', 'Sex'),
        ('mieg', 'Sex'),
        ('chen', 'Sex'),
        ('oliver', 'Sex'),
        ('nlm', 'Developmental stage'),
        ('mieg', 'Developmental stage'),
        ('mieg', 'Developmental stage details'),
        ('chen', 'Development stage'),
        ('oliver', 'Development stage'),
        ('oliver', 'Age stage'),
        ('nlm', 'cell type and anatomy'),
        ('chen', 'Tissue'),
        ('oliver', 'Tissue'),
        ('mieg', 'Tissue'),
        ('mieg', 'Tissue details'),
        ('mieg', 'Tissue description'),
        ('mieg', 'System type'),
        ('mieg', 'System'),
        ('mieg', 'System description'),
        ('nlm', 'Strain, treatment or note'),
        ('chen', 'Genotype'),
        ('oliver', 'Background genotype'),
        ('oliver', 'Treatment perturbation'),
        ('oliver', 'Treatment conditions'),
        ('oliver', 'Sample focus'),
        ('chen', 'Cell type'),
        ('oliver', 'Cell type'),
        ('mieg', 'Cell line'),
        ('mieg', 'Cell line details'),
        ('nlm', 'Cell line'),
        ('chen', 'Sample type'),
        ('oliver', 'Sample type'),
        ('oliver', 'Tissue position'),
        ('oliver', 'Notes and flags'),
        ('magic', 'Problem in SRA consistency or download'),
        ('magic', 'Sample is duplciated'),
        ])

    df = pd.read_csv(fname, sep='\t', encoding="ISO-8859-1", skiprows=1, header=None, names=header)

    def set_runs(x):
        """TM have provided 'srr' when a library was ran on more
        than one lane. This is set to NaN if there was only one run. I want to go
        ahead and fill this in."""
        header = ('magic', 'srr')
        if x.isnull()[header]:
            x[header] = x[('magic', 'id')]
        return x

    return df.apply(set_runs, axis=1)


def get_level(x, dat):
    vals = []
    for key, value in dat.items():
        if key[0] == x:
            if not isinstance(value, str) and np.isnan(value):
                continue
            vals.append({
                'name': key[1],
                'value': value
            })
    return vals

def undo(biometa, record):
    """Undo the changes."""
    for record in df.to_dict('record'):
        pk = record[('magic', 'biosample')]
        biometa.find_one_and_update(
            {'_id': pk},
            {
                '$unset': {
                    'magic': '',
                    'mieg': '',
                    'chen': '',
                    'oliver': '',
                    'nlm': '',
                }
            }
        )

if __name__ == '__main__':
    # Import Jean's summary
    fname = '../../ncbi_remap/data/jean/RunsDroso_4annot_9549_libraries.txt'
    df = parse_meig_dat(fname)

    # Connect to database
    client = MongoClient(host='localhost', port=27022)
    db = client['test']
    biometa = db['biometa']

    # Add jean's annotation summary to database
    for record in df.to_dict('record'):
        pk = record[('magic', 'biosample')]
        biometa.find_one_and_update(
            {'_id': pk},
            {
                '$addToSet': {
                    'magic': {'$each': get_level('magic', record)},
                    'mieg': {'$each': get_level('mieg', record)},
                    'chen': {'$each': get_level('chen', record)},
                    'oliver': {'$each': get_level('oliver', record)},
                    'nlm': {'$each': get_level('nlm', record)},
                }
            }
            )
