# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/datasets.datasets.ipynb (unless otherwise specified).

__all__ = ['DataSet']

# Cell
from pathlib import Path
import abc
import pandas as pd
import numpy as np

# block_types API
from ..config import bt_defaults as dflt
from ..utils.utils import set_logger

# Cell
class DataSet (metaclass=abc.ABCMeta):
    """Abstract DataSet class."""
    def __init__ (self, logger = None, verbose=dflt.verbose, **kwargs):
        """
        Initialize common attributes and fields, in particular the logger.

        Parameters
        ----------
        logger : logging.Logger or None, optional
            Logger used to write messages
        verbose : int, optional
            Verbosity, 0: warning or critical, 1: info, 2: debug.
        """
        if logger is None:
            self.logger = set_logger ('block_types', verbose=verbose)
        else:
            self.logger = logger
    @abc.abstractmethod
    def load ():
        pass