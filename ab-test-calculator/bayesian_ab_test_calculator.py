# credit to https://towardsdatascience.com/bayesian-a-b-testing-with-python-the-easy-guide-d638f89e0b8a
from math import lgamma
from typing import Tuple
import numpy as np
import pandas as pd
from scipy.stats import beta

# Fill in here the losses and wins for each group (ctrl - A/test - B), in case you want to run it locally
LOSSES_CTRL, WINS_CTRL = 8000, 2000
LOSSES_TEST, WINS_TEST = 7927, 2073


class BayesianABTestCalculator:
    @staticmethod
    def _h(a, b, c, d) -> float:
        """
        Helper function for computing an integral. See link at the top of the file.
        :param a: int
        :param b: int
        :param c: int
        :param d: int
        :return: float.
        """
        num = lgamma(a + c) + lgamma(b + d) + lgamma(a + b) + lgamma(c + d)
        den = lgamma(a) + lgamma(b) + lgamma(c) + lgamma(d) + lgamma(a + b + c + d)
        return np.exp(num - den)

    @staticmethod
    def _g0(a: int, b: int, c: int) -> float:
        """
        Helper function for computing an integral. See link at the top of the file.
        :param a: int
        :param b: int
        :param c: int
        :return: float.
        """
        return np.exp(lgamma(a + b) + lgamma(a + c) - (lgamma(a + b + c) + lgamma(a)))

    @staticmethod
    def _hiter(a, b, c, d):
        """
        Helper generator for computing an integral. See link at the top of the file.
        :param a: int
        :param b: int
        :param c: int
        :param d: int
        :return: float.
        """
        while d > 1:
            d -= 1
            yield BayesianABTestCalculator._h(a, b, c, d) / d

    @staticmethod
    def _g(a, b, c, d) -> float:
        """
        Helper function for computing an integral. See link at the top of the file.
        :param a: int
        :param b: int
        :param c: int
        :param d: int
        :return: float.
        """
        return BayesianABTestCalculator._g0(a, b, c) + sum(
            BayesianABTestCalculator._hiter(a, b, c, d)
        )

    @staticmethod
    def calc_prob_between(beta_test, beta_control) -> float:
        """
        Returns the probability that the tests' mean is higher that the controls', based on their beta value.
        For more details, see the link at the top of the file.
        :param beta_test: float. the beta value of the test.
        :param beta_control: float. the beta value of the test.
        :return: float. a probability as described.
        """
        return BayesianABTestCalculator._g(
            beta_test.args[0],
            beta_test.args[1],
            beta_control.args[0],
            beta_control.args[1],
        )

    @staticmethod
    def run_test(losses_ctrl: int, wins_ctrl: int, losses_test: int, wins_test: int) -> Tuple[pd.DataFrame, str]:
        """
        :param losses_ctrl: number of losses for the control group.
        :param wins_ctrl: number of wins for the control group.
        :param losses_test: number of losses for the test group.
        :param wins_test: number of wins for the test group.
        :return: None. Prints the bottom line of the A/B test.
        """
        # This is the known data: wins & losses for the Control and Test set
        ctrl_winrate = wins_ctrl / (max(wins_ctrl + losses_ctrl, 1))
        test_winrate = wins_test / (max(wins_test + losses_test, 1))

        # here we create the Beta functions for the two sets
        a_C, b_C = wins_ctrl + 1, losses_ctrl + 1
        beta_C = beta(a_C, b_C)
        a_T, b_T = wins_test + 1, losses_test + 1
        beta_T = beta(a_T, b_T)

        # calculating the lift
        lift = (beta_T.mean() - beta_C.mean()) / beta_C.mean()

        # calculating the probability for Test to be better than Control
        prob = BayesianABTestCalculator.calc_prob_between(beta_T, beta_C)
        df = pd.DataFrame(
                [
                    [
                        losses_ctrl,
                        wins_ctrl,
                        str(np.around(100 * ctrl_winrate, 2)) + "%",
                    ],
                    [
                        losses_test,
                        wins_test,
                        str(np.around(100 * test_winrate, 2)) + "%",
                    ],
                ],
                columns=["#lost", "#won", "winrate"], index=["A", "B"])

        txt = f"B lift with respect to A is {lift * 100:2.2f}%.  \n"
        better_group = "A" if ctrl_winrate > test_winrate else "B"
        txt += f"{better_group} achieved better results by {abs(np.around(100 * (ctrl_winrate - test_winrate), 2))}%.  \n"
        txt += f"{better_group} is better with {prob * 100:2.1f}% probability."
        return df, txt
