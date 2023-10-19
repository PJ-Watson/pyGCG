import collections
from pathlib import Path

import customtkinter as ctk
import numpy as np


def fpe(filepath):
    return Path(filepath).expanduser().resolve()


def flatten_dict(input_dict, parent_key=False, separator="_"):
    items = []
    for key, value in input_dict.items():
        new_key = str(parent_key) + separator + key if parent_key else key
        if isinstance(value, collections.abc.MutableMapping):
            items.extend(flatten_dict(value, new_key, separator).items())
        elif isinstance(value, list):
            for k, v in enumerate(value):
                items.extend(flatten_dict({str(k): v}, new_key).items())
        else:
            items.append((new_key.upper(), value))
    return dict(items)


# https://github.com/matplotlib/matplotlib/issues/4556
def update_errorbar(errobj, x, y, xerr=None, yerr=None):
    ln, caps, bars = errobj

    if len(bars) == 2:
        assert (
            xerr is not None and yerr is not None
        ), "Your errorbar object has 2 dimension of error bars defined. You must provide xerr and yerr."
        barsx, barsy = bars  # bars always exist (?)
        try:  # caps are optional
            errx_top, errx_bot, erry_top, erry_bot = caps
        except ValueError:  # in case there is no caps
            pass

    elif len(bars) == 1:
        assert (xerr is None and yerr is not None) or (
            xerr is not None and yerr is None
        ), "Your errorbar object has 1 dimension of error bars defined. You must provide xerr or yerr."

        if xerr is not None:
            (barsx,) = bars  # bars always exist (?)
            try:
                errx_top, errx_bot = caps
            except ValueError:  # in case there is no caps
                pass
        else:
            (barsy,) = bars  # bars always exist (?)
            try:
                erry_top, erry_bot = caps
            except ValueError:  # in case there is no caps
                pass

    ln.set_data(x, y)

    try:
        errx_top.set_xdata(x + xerr)
        errx_bot.set_xdata(x - xerr)
        errx_top.set_ydata(y)
        errx_bot.set_ydata(y)
    except NameError:
        pass
    try:
        barsx.set_segments(
            [np.array([[xt, y], [xb, y]]) for xt, xb, y in zip(x + xerr, x - xerr, y)]
        )
    except NameError:
        pass

    try:
        erry_top.set_xdata(x)
        erry_bot.set_xdata(x)
        erry_top.set_ydata(y + yerr)
        erry_bot.set_ydata(y - yerr)
    except NameError:
        pass
    try:
        barsy.set_segments(
            [np.array([[x, yt], [x, yb]]) for x, yt, yb in zip(x, y + yerr, y - yerr)]
        )
    except NameError:
        pass


def error_bar_visibility(errobj, visible=True):
    ln, caps, bars = errobj

    ln.set_visible(visible)

    if len(bars) == 2:
        barsx, barsy = bars  # bars always exist (?)
        barsx.set_visible(visible)
        barsy.set_visible(visible)
        try:  # caps are optional
            errx_top, errx_bot, erry_top, erry_bot = caps
            errx_top.set_visible(visible)
            errx_bot.set_visible(visible)
            erry_top.set_visible(visible)
            erry_bot.set_visible(visible)
        except ValueError:  # in case there is no caps
            pass

    elif len(bars) == 1:
        (bars1d,) = bars  # bars always exist (?)
        bars1d.set_visible(visible)
        try:
            err_top, err_bot = caps
            err_top.set_visible(visible)
            err_bot.set_visible(visible)
        except ValueError:  # in case there is no caps
            pass


# From https://stackoverflow.com/questions/4140437/
class ValidateFloatVar(ctk.StringVar):
    """StringVar subclass that only allows valid float values to be put in it."""

    def __init__(self, master=None, value=None, name=None):
        ctk.StringVar.__init__(self, master, value, name)
        self._old_value = self.get()
        self.trace("w", self._validate)

    def _validate(self, *_):
        new_value = self.get()
        try:
            new_value == "" or float(new_value)
            self._old_value = new_value
        except ValueError:
            ctk.StringVar.set(self, self._old_value)
