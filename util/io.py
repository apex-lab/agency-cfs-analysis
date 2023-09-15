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

def load_osf_binding_dataset():
    '''
    Downloads dataset reported in https://doi.org/10.31234/osf.io/4z2rj
    and returns all action binding trials as a dataframe.
    '''
    # Import these in-function so they're not requirements for main analysis,
    # only for the power analysis before data collection.
    import tempfile
    from bids import BIDSLayout
    from zipfile import ZipFile
    from osfclient.utils import makedirs
    from osfclient import OSF
    from tqdm import tqdm
    # download dataset from OSF
    osf = OSF()
    project = osf.project('753C2')
    store = next(project.storages) # osfstorage
    with tempfile.TemporaryDirectory() as tmpdir:
        with tqdm(unit = 'files') as pbar:
            prefix = os.path.join(tmpdir, store.name)
            for file_ in store.files:
                path = file_.path
                if path.startswith('/'):
                    path = path[1:]
                path = os.path.join(prefix, path)
                directory, _ = os.path.split(path)
                makedirs(directory, exist_ok = True)
                with open(path, "wb") as f:
                    file_.write_to(f)
                pbar.update()
        # unpack the .zip archive
        zip_dir = os.path.join(tmpdir, 'osfstorage', 'data')
        zip_f = os.path.join(zip_dir, 'data_bids_anon.zip')
        with ZipFile(zip_f, 'r') as zip_archive:
            zip_archive.extractall(zip_dir)
        # parse the BIDS directory structure
        bids_root = os.path.join(zip_dir, 'data_bids_anon')
        layout = BIDSLayout(bids_root, validate = False)
        # get clock task filenames and sort by subject number
        sub = lambda f: int(re.findall(r'sub-(\w+)_', f)[0])
        fpaths = layout.get(return_type = 'file', task = 'libet')
        fpaths.sort(key = sub)
        # and load the data into memory before temp directory is deleted
        dfs = [pd.read_csv(f, sep = '\t') for f in fpaths]
    # now consolidate data from all subjects into one dataframe
    cond_dfs = []
    for i, df in enumerate(dfs):
        df['subject'] = i # add subject index
        conds = df.trial.unique()
        conds.sort()
        for cond in conds: # exclude 5 practice trials
            cond_df = df[df.trial == cond].iloc[5:]
            cond_dfs.append(cond_df)
    df = pd.concat(cond_dfs)
    df = df[df.trial.str.contains('key')] # we just want action binding
    df['operant'] = df.trial.str.contains('operant').astype(int)
    df = df[['subject', 'operant', 'overest_ms']]
    return df
