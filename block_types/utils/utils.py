# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/utils.utils.ipynb (unless otherwise specified).

__all__ = ['make_reproducible', 'set_logger', 'remove_previous_results', 'set_tf_loglevel']

# Cell
import os
import numpy as np
import random as python_random
import logging
import shutil
from pathlib import Path

# block-types
import block_types.config.defaults as dflt

def make_reproducible ():
    """
    Make results obtained from neural network model reproducible.

    This function should be run at the very beginning. The result
    of calling this is that the pipeline produces the exact same
    results as previous runs.
    """
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    os.environ['PYTHONHASHSEED'] = '0'

    # The below is necessary for starting Numpy generated random numbers
    # in a well-defined initial state.
    np.random.seed(123)

    # The below is necessary for starting core Python generated random numbers
    # in a well-defined state.
    python_random.seed(123)

    # The below set_seed() will make random number generation
    # in the TensorFlow backend have a well-defined initial state.
    # For further details, see:
    # https://www.tensorflow.org/api_docs/python/tf/random/set_seed
    try:
        import tensorflow as tf
        tf.random.set_seed(1234)
    except:
        print ('tensorflow needs to be installed in order to run make_reproducible()')

# Cell
def set_logger (name, path_results='log', stdout=True,
                mode='w', just_message = False, filename='logs.txt',
                logging_level=logging.DEBUG, verbose=None):
    """Set logger."""
    logger = logging.getLogger(name)
    if verbose is not None:
        logging_level = logging.DEBUG if verbose == 2 else logging.INFO if verbose == 1 else logging.WARNING
    logger.setLevel(logging_level)

    for hdlr in logger.handlers[:]:  # remove all old handlers
        logger.removeHandler(hdlr)

    #if not logger.hasHandlers():

    # Create handlers
    if stdout:
        c_handler = logging.StreamHandler()
        c_handler.setLevel(logging_level)
        c_format = logging.Formatter('%(message)s')
        c_handler.setFormatter(c_format)
        logger.addHandler(c_handler)

    os.makedirs(path_results, exist_ok=True)
    f_handler = logging.FileHandler('%s/%s' %(path_results, filename), mode = mode)
    f_handler.setLevel(logging_level)
    if just_message:
        f_format = logging.Formatter('%(asctime)s - %(message)s')
    else:
        f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s {%(filename)s:%(funcName)s:%(lineno)d} - %(message)s')
    f_handler.setFormatter(f_format)
    logger.addHandler(f_handler)
    logger.propagate = 0

    return logger

# Cell
def remove_previous_results (path_results=dflt.path_results):
    """Remove folder containing previous results, if exists."""
    if Path(path_results).exists():
        shutil.rmtree(path_results)

# Cell
def set_tf_loglevel(level):
    if level >= logging.FATAL:
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
    if level >= logging.ERROR:
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
    if level >= logging.WARNING:
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1'
    else:
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '0'
    logging.getLogger('tensorflow').setLevel(level)

    tf.get_logger().setLevel(level)