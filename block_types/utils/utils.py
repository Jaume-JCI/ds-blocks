# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/utils/utils.ipynb (unless otherwise specified).

__all__ = ['make_reproducible', 'get_logging_level', 'delete_logger', 'set_logger', 'set_empty_logger', 'set_verbosity',
           'remove_previous_results', 'set_tf_loglevel', 'argnames', 'get_specific_dict_param',
           'obtain_class_specific_attrs', 'get_hierarchy_level', 'replace_attr_and_store']

# Cell
import sys
import os
import random as python_random
import logging
import shutil
from pathlib import Path
import re
import inspect
import numpy as np

# block-types
import block_types.config.bt_defaults as dflt

# Cell
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
def get_logging_level (verbose):
    return logging.DEBUG if verbose == 2 else logging.INFO if verbose == 1 else logging.WARNING

# Cell
def delete_logger (name, path_results='log', filename='logs.txt'):
    if filename is not None and path_results is not None:
        path_to_log_file = f'{path_results}/{filename}'
        if os.path.exists (path_to_log_file):
            os.remove (path_to_log_file)

# Cell
import pdb
def set_logger (name, path_results='log', stdout=True,
                mode='a', just_message = False, filename='logs.txt',
                logging_level=logging.DEBUG, verbose=None, verbose_out=None,
                print_path=False):
    """Set logger."""
    logger = logging.getLogger(name)
    if verbose is not None:
        logging_level = get_logging_level (verbose)
    if verbose_out is not None:
        logging_level_out = get_logging_level (verbose_out)
    else:
        logging_level_out = logging_level
    logger.setLevel(logging_level)

    for hdlr in logger.handlers[:]:  # remove all old handlers
        logger.removeHandler(hdlr)
    # Create handlers
    if stdout:
        c_handler = logging.StreamHandler()
        c_handler.setLevel(logging_level_out)
        c_format = logging.Formatter('%(message)s')
        c_handler.setFormatter(c_format)
        logger.addHandler(c_handler)
    else:
        logger.removeHandler(sys.stderr)

    if filename is not None and path_results is not None:
        os.makedirs(path_results, exist_ok=True)
        path_to_log_file = f'{path_results}/{filename}'
        #pdb.set_trace()
        if print_path: print (f'log written in {os.path.abspath(path_to_log_file)}')
        f_handler = logging.FileHandler (path_to_log_file, mode = mode)
        f_handler.setLevel(logging_level)
        if just_message:
            f_format = logging.Formatter('%(asctime)s - %(message)s')
        else:
            f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s {%(filename)s:%(funcName)s:%(lineno)d} - %(message)s')
        f_handler.setFormatter(f_format)
        logger.addHandler(f_handler)
    #logger.propagate = 0
    logger.propagate = False

    return logger

# Cell
def set_empty_logger ():
    return set_logger ('no_logging', stdout=False, filename=None, verbose=0)

# Cell
def set_verbosity (name=None, logger=None, logging_level=logging.DEBUG, verbose=None, verbose_out=None):
    """Set logger."""
    if logger is None:
        assert name is not None, 'either logger or name must be not None'
        logger = logging.getLogger(name)
    if verbose is not None:
        logging_level = get_logging_level (verbose)
    if verbose_out is not None:
        logging_level_out = get_logging_level (verbose_out)
    else:
        logging_level_out = logging_level
    logger.setLevel(logging_level)

    for hdlr in logger.handlers[:]:  # remove all old handlers
        hdlr.setLevel(logging_level)

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

    try:
        import tensorflow as tf
    except:
        print ('tensorflow needs to be installed in order to call set_tf_loglevel()')

    tf.get_logger().setLevel(level)

# Cell
def argnames(f, frame=False):
    "Names of arguments to function or frame `f`"
    code = getattr(f, 'f_code' if frame else '__code__')
    return code.co_varnames[:code.co_argcount+code.co_kwonlyargcount]

# Cell
def _store_attr(self, overwrite=False, error_if_present=False, ignore=set(), **attrs):
    stored = getattr(self, '__stored_args__', None)
    for n,v in attrs.items():
        if hasattr(self, n) and not overwrite:
            if (error_if_present and getattr(self, n) is not v and n not in ignore
                and not callable(getattr(self, n))):
                raise RuntimeError (f'field {n} already present in object from {self.__class__.__name__}')
            continue
        setattr(self, n, v)
        if stored is not None: stored[n] = v

# Cell
def get_specific_dict_param (self, **kwargs):
    if (hasattr(self, 'name') and
        kwargs.get(self.name) is not None and
        isinstance(kwargs[self.name], dict)):
        k = self.name
    elif (hasattr(self, 'class_name') and
        kwargs.get(self.class_name) is not None and
        isinstance(kwargs[self.class_name], dict)):
        k = self.class_name
    elif (hasattr(self, 'group') and
        kwargs.get(self.group) is not None and
        isinstance(kwargs[self.group], dict)):
        k = self.group
    elif (hasattr(self, 'hierarchy_level') and
        kwargs.get('levels') is not None and
        isinstance(kwargs['levels'], dict) and
        'until' in kwargs['levels'] and
        self.hierarchy_level <= kwargs['levels']['until']):
        k = 'levels'
    else:
        k = None

    return k

def obtain_class_specific_attrs (self, **kwargs):
    """Overwrites parameters in kwargs with those found in a dictionary of the same name
    given to this component.

    Checks if there is a parameter whose name is the name of the class or the name given
    to this component. In that case, it overwrites the parameters in kwargs with those
    found in that dictionary. The parameters in kwargs can be used as *global* parameters
    for multiple components, while parameters specific of one component can be set using
    a dictionary with the name of that component. See example below.
    """
    k = get_specific_dict_param (self, **kwargs)

    if k is not None:
        config = kwargs[k]
    else:
        config = {}

    return config

# Cell
def get_hierarchy_level (base_class=object):
    stack = inspect.stack()
    hierarchy_level=0
    last_type = None
    for frame_number in range(1, len(stack)):
        fr = sys._getframe(frame_number)
        fr_stack = stack[frame_number]
        if fr is not fr_stack[0]:
            raise RuntimeError ('fr is not fr_stack[0]')

        args = argnames(fr, True)
        if len(args) > 0:
            self = fr.f_locals[args[0]]
            if last_type is None:
                last_type = type(self)
            if ((fr_stack.function == '__init__') and
                isinstance(self, base_class) and
                (type(self) != last_type) ):
                hierarchy_level += 1
                last_type = type(self)
    return hierarchy_level

# Cell
def replace_attr_and_store (names=None, but='', store_args=None,
                            recursive=True, base_class=object,
                            replace_generic_attr=True, overwrite=False,
                            error_if_present=False, ignore=set(), overwrite_name=True,
                            self=None, include_first=False, **attrs):
    """
    Replaces generic attributes and stores them into attrs in `self`.

    If kwargs contains an attribute called the same way as the class of
    self, all the keys in that dictionary are considered class-specific
    attributes whose value overwrites any attribute in kwargs of the same
    name.

    The function is called recursively in the hierarchy of parent classes,
    from the leaf to the root class, until it reaches an ascendant that
    is not an instance of `base_class`.

    Most of the implementation is taken from fastcore library, `store_attrs`
    function.
    """
    frame_number=1
    stack = inspect.stack()
    original_type = None
    input_attrs = attrs
    while True:
        fr = sys._getframe(frame_number)
        fr_stack = stack[frame_number]
        if fr is not fr_stack[0]:
            raise RuntimeError ('fr is not fr_stack[0]')

        args = argnames(fr, True)
        if recursive:
            if len(args) > 0:
                self = fr.f_locals[args[0]]
                if not isinstance(self, base_class):
                    break
                if fr_stack.function != '__init__':
                    break
                if original_type is None:
                    original_type = type(self)

                if type(self) != original_type:
                    break
            else:
                break
        else:
            if self is not None:
                if include_first:
                    args = [self] + list(args)
            elif len(args) > 0:
                self = fr.f_locals[args[0]]
            else:
                raise RuntimeError ('self not found')

        if store_args is None: store_args = not hasattr(self,'__slots__')
        if store_args and not hasattr(self, '__stored_args__'): self.__stored_args__ = {}
        if names and isinstance(names,str): names = re.split(', *', names)
        #pdb.set_trace()
        ns = names if names is not None else getattr(self, '__slots__', args[1:])
        added = {n:fr.f_locals[n] for n in ns}
        attrs = {**input_attrs, **added}
        if replace_generic_attr and 'kwargs' in fr.f_locals:
            class_specific_attrs = obtain_class_specific_attrs (self, **fr.f_locals['kwargs'])
            attrs.update(class_specific_attrs)
        else:
            class_specific_attrs={}
        if isinstance(but,str): but = re.split(', *', but)
        attrs = {k:v for k,v in attrs.items() if k not in but}
        _store_attr(self, overwrite=overwrite, error_if_present=error_if_present,
                    ignore=ignore, **attrs)
        if overwrite_name and ('name' in class_specific_attrs
                               or 'class_name' in class_specific_attrs):
            new_attrs = {k:class_specific_attrs[k] for k in ['name', 'class_name']
                         if k in class_specific_attrs}
            _store_attr(self, overwrite=True, error_if_present=error_if_present,
                        ignore=ignore, **new_attrs)

        if not recursive:
            break

        frame_number += 1
