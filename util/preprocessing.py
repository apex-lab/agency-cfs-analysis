from collections import OrderedDict
from tfHuber import mean as _mean
import pandas as pd
import numpy as np

def get_condition_labels(df, sep = ' '):
    '''
    Creates a pd.Series with condition labels like 'unmasked_operant'
    from boolean columns in clock task data.
    '''
    masked = df.masked.copy()
    masked = masked.replace({False: 'unmasked', True: 'masked'})
    operant = df.operant.copy()
    operant = operant.replace({False: 'baseline', True: 'operant'})
    condition = masked + sep + operant
    return condition

def _calc_per_condition(df, func, catch = False):
    '''
    applies fo given function to each condition and returns results

    Arguments
    ----------
    catch : bool, default: False
        Whether to use catch trials (True) or ordinary trials (False).
    '''
    df = df[(~df.practice)] # always exclude practice trials
    if catch:
        df = df[df.catch]
    else:
        df = df[~df.catch]
    label = get_condition_labels(df)
    conds = pd.unique(label)
    conds.sort() # make sure always evaluated in same order
    res = OrderedDict()
    for cond in conds:
        res[cond] = func(df[label == cond])
    return res

def calc_detection_counts(df, catch = False):
    '''
    Calculates number of trials in each masked condition where subject
    reported being aware of seeing a circle.

    Arguments
    ----------
    df : pd.DataFrame
        Dataframe containing task data from Libet clock task conditions,
        e.g. as loaded with `layout.load_clock_data(sub_id)`.

    Returns
    ----------
    counts : Array of shape (n_condition, 2)
        A 2x2 contingency table where counts[:, 0] is the number of
        reported circles seen in each condition, and
        counts[;, 1] is n_trials - counts[:, 0].
    '''
    get_counts = lambda df: df.aware.mean()
    def get_counts(df):
        return (df.aware.sum(), (~df.aware).sum())
    df = df[df.masked]
    counts =  _calc_per_condition(df, get_counts, catch)
    counts = np.array(counts)
    return counts.astype(int)

huber_mean = lambda x: _mean(np.array(x.tolist()))[0]

def calc_overest_means(df):
    '''
    Calculates Huber mean (i.e. more outlier robust than sample mean)
    of each condition, excluding practice trials, catch trials, and trials
    in which subject reported seeing a circle.

    Arguments
    ----------
    df : pd.DataFrame
        Dataframe containing task data from Libet clock task conditions,
        e.g. as loaded with `layout.load_clock_data(sub_id)`.

    Returns
    ----------
    means : dict
        A dictionary containing Huber means for each condition.
    '''
    df = df[(~df.aware) | (~df.masked)]
    get_means = lambda df: huber_mean(df.overest_t)
    means = _calc_per_condition(df, get_means)
    return means
