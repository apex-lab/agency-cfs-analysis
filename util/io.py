import pandas as pd
import os
import re

class Layout:

    def __init__(self, data_dir):
        '''
        Arguments
        ------------
        data_dir : str
            Relative or absolute path to directory containing the data.
            Assumes directory is organized as output by the experiment
            script in https://github.com/apex-lab/agency-cfs.
        '''
        self.dir = data_dir

    def get_subjects(self):
        '''
        Returns
        ---------
        subs : list[str]
            The subject IDs for which subdirectories exist, in sorted order.
        '''
        isdir = lambda fpath: os.path.isdir(os.path.join(self.dir, fpath))
        subdirs = [fpath for fpath in os.listdir(self.dir) if isdir(fpath)]
        subdirs = [d for d in subdirs if 'sub-' in d]
        subs = [re.findall('sub-(\w+)', d)[0] for d in subdirs]
        subs.sort(key = int)
        return subs

    def get_filepath(self, sub, task):
        '''
        Arguments
        ----------
        sub : str
        task : str

        Returns
        ----------
        fpath : str
        '''
        sub_root = os.path.join(self.dir, 'sub-%s'%sub, 'beh')
        fname = 'sub-%s_task-%s_beh.tsv'%(sub, task)
        fpath = os.path.join(sub_root, fname)
        return fpath

    def load(self, sub, task):
        '''
        Arguments
        ----------
        sub : str
        task : str

        Returns
        ---------
        df : pd.DataFrame
        '''
        fpath = self.get_filepath(sub, task)
        return pd.read_csv(fpath, sep = '\t')

    def get_task_filepaths(self, task, subs = None):
        '''
        Arguments
        -----------
        task : str
        subs : list[str]
            You can specify subjects manually if you want,
            e.g. if you've excluded some subjects.

        Returns
        ------------
        fpaths : list[str]
            List of filepaths containing data for specified task.
        '''
        if subs is not None:
            subs = self.get_subjects()
        fpaths = []
        for sub in subs:
            f = self.get_filepath(sub, task)
            if os.path.exists(f):
                fpaths.append(f)
        return fpaths

    def load_clock_data(self, sub):
        '''
        Loads one subject's data from both 'masked' and 'unmasked' task files
        as a single dataframe.

        Arguments
        ----------
        sub : str

        Returns
        ----------
        df : pd.DataFrame
        '''
        df1 = self.load(sub, 'masked')
        df2 = self.load(sub, 'unmasked')
        df = pd.concat([df1, df2])
        return df
