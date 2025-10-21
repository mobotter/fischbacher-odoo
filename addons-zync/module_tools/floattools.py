from odoo.tools import float_round
from decimal import Decimal


def float_is_same(f1, f2, precision_rounding=None, tolerance=None, total_percentage_tolerance=None):
    """
    :param tolerance: float, if the difference between f1 and f2 is less than tolerance, return True
    :param total_percentage_tolerance: float, if the difference between f1 and f2 is less than total_percentage_tolerance

    """
    f = list(map(Decimal, [f1, f2]))
    if precision_rounding:
        digits = len(str(1/precision_rounding).split(".")[0]) - 1
        f = list(map(lambda x: round(x, digits), f))
    s = [str(f1), str(f2)]

    def get_len(s):
        if "." not in s:
            s += ".0"
        return len(str(s).split(".")[1])

    def round_to_len(f):
        return float_round(float(f), precision_digits=minlen)

    lens = list(map(get_len, s))
    minlen = min(lens)
    f = list(map(round_to_len, f))
    if f[0] == f[1]:
        return True
    if tolerance:
        diff = abs(f[0] - f[1])
        if diff <= tolerance:
            return True
    if total_percentage_tolerance and f[0]:
        diff = abs(f[0] - f[1])
        percentage = abs(diff / f[0] * 100)
        if percentage <= total_percentage_tolerance:
            return True
    return False
