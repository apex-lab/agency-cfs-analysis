import pandas as pd
import numpy as np

class DataSimulator:

    def __init__(self, n_trials = 40, effect_size_ms = 28.,
                    sd_pop = 76., sd_sub = 92.):
        '''
        A helper class to simulate null data in which the intentional binding
        effect is only present when the subject is aware of the
        operant stimulus.

        However, if you specify that subject should be aware of operant on all
        trials, it will produce data as if the effect size is equal for
        masked and unmasked conditions. So in that case, you could use it to
        simulate non-null data.

        Default parameter values are computed from the n = 190 subject dataset
        reported in https://doi.org/10.31234/osf.io/4z2rj

        Arguments
        --------
        n_trials : int
            Number of trials per block.
        effect_size_ms : float
            The population mean of the subject-level difference between
            operant and baseline condition, given in milliseconds.
        sd_pop : float
            Standard deviation of the subject-level paired differences
            between operant and baseline condition.
        sd_sub : float
            Standard deviation of the trial-by-trial overestimates
            within one subject.
        '''
        self.n_trials = n_trials
        self.effect_size_ms = effect_size_ms
        self.sd_pop = sd_pop
        self.sd_sub = sd_sub

    def _format_df(self, ts):
        '''
        adds some metadata so we can use same functions as main analysis code
        when we analyze simulated data
        '''
        df = pd.DataFrame({'overest_t': ts})
        df['aware'] = False # not actual awareness, whether they report it
        df['catch'] = False
        df['practice'] = False
        return df

    def simulate_masked(self, effect_size, p_aware = 0., seed = None):

        rng = np.random.default_rng(seed)

        # simulate baseline trials
        est_baseline = rng.normal(0, self.sd_sub, self.n_trials)
        baseline = self._format_df(est_baseline)
        baseline['operant'] = False

        # simulate operant condition
        est_unaware = rng.normal(0, self.sd_sub, self.n_trials)
        est_aware = rng.normal(effect_size, self.sd_sub, self.n_trials)
        aware = rng.uniform(size = self.n_trials) < p_aware
        est_operant = np.choose(aware, [est_unaware, est_aware])
        operant = self._format_df(est_operant)
        operant['operant'] = True

        df = pd.concat([baseline, operant])
        df['masked'] = True
        return df

    def simulate_subject(self, p_aware = 0., seed = None):
        '''
        simulates all four clock conditions for one subject

        Arguments
        -----------
        p_aware : float
            Probability that operant stimulus will "break through" masking
            on the masked trials. If you set this to 1., then effect size
            in the masked conditions is the same as in the unmasked conditions,
            so that's like simulating non-null data.
        seed : int

        Returns
        -----------
        df : pd.DataFrame
            A dataframe similar to that returned by
            util.io.Layout.load_clock_data when loading real subject data.
        '''
        rng = np.random.default_rng(seed)
        effect_size =  rng.normal(self.effect_size_ms, self.sd_pop)
        masked_conds = self.simulate_masked(effect_size, p_aware, rng)
        unmasked_conds = self.simulate_masked(effect_size, 1., rng)
        unmasked_conds['masked'] = False
        df = pd.concat([masked_conds, unmasked_conds])
        return df
