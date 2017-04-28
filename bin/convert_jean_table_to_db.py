#!/usr/bin/env python
"""Take metadata information from Jean's summary and adds to database."""

import pandas as pd
from pymongo import MongoClient
import numpy as np
import re
import logging

logger = logging.getLogger()

def parse_meig_dat(fname):
    """Parse the Mieg file specifying my own headers.

    The Mieg headers were a little awkward, so I decided to clean these up a
    little. I tried to keep them similar so that they would be easily
    translated back.
    """
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


def split_srr(df):
    """Splits ('magic', 'srr') column into separate rows.

    I am thinking it will be more useful to split SRRs up into their own
    record. When added to the database I am using set logic based on values so
    I would get a list of SRRs that is easy to pull out.
    """
    rows = []
    for i, sr in df.iterrows():
        srr = sr[('magic', 'srr')]
        if ';' in srr:
            srrs = [x.strip() for x in sr[('magic', 'srr')].split('\\;')]
            for run in srrs:
                sr[('magic', 'srr')] = run
                rows.append(sr)
        else:
            rows.append(sr)
    return pd.concat(rows, axis=1, ignore_index=True).T


def get_level(x, dat):
    """Quick helper to pull out records from a dict based that is keyed with a
    tuple.

    The keys are of the form {(index1, index2): value}. I want to pull out
    everthing corresponding to index1 and return [{index2: value},].

    """
    pattern = re.compile(r'[ \\\(\)\?]+')
    vals = []
    for keys, value in dat.items():
        if keys[0] == x:
            if not isinstance(value, str) and np.isnan(value): continue

            if x != 'magic':
                key = re.sub(pattern, '_', keys[1]).strip('_').lower()
                value = re.sub(pattern, '_', value).strip('_').lower()
            else:
                key = keys[1]
                value = value

            if value == 'none': continue

            vals.append({
                'name': key,
                'value': value
            })

    return vals


def undo(biometa, df):
    """Undo the changes.

    Since I am playing with the database want a way to easily undo the changes
    if I need to.

    """
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


def add_to_db(biometa, df):
    # Add jean's annotation summary to database
    logger.info('Adding records to database')
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


if __name__ == '__main__':
    # Import Jean's summary
    logger.info('Importing data')
    fname = '../../ncbi_remap/data/jean/RunsDroso_4annot_9549_libraries.txt'
    df = parse_meig_dat(fname)

    # split up srrs in Jean's table
    dfSplit = split_srr(df)

    # Connect to database
    logger.info('Connecting to database')
    client = MongoClient(host='localhost', port=27022)
    db = client['sra']
    biometa = db['biometa']

    # Add to database
    add_to_db(biometa, dfSplit)
#     undo(biometa, dfSplit)

