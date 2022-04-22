# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/core/block_types.ipynb (unless otherwise specified).

__all__ = ['Component', 'SamplingComponent', 'SklearnComponent', 'PickleSaverComponent', 'NoSaverComponent',
           'OneClassSklearnComponent', 'PandasComponent']

# Cell
from functools import partialmethod
from typing import Optional, Union
import copy
import pickle
from pathlib import Path
import re

from sklearn.utils import Bunch
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pyarrow as pa
import joblib
from IPython.display import display

# block_types
from .data_conversion import (DataConverter, NoConverter, PandasConverter,
                                              StandardConverter, GenericConverter,
                                              data_converter_factory)
from .utils import (save_csv,  save_parquet,  save_multi_index_parquet,
                                    save_keras_model,  save_csv_gz, read_csv, read_csv_gz)
from .utils import DataIO, SklearnIO, PandasIO, NoSaverIO
from .utils import data_io_factory
from .utils import ModelPlotter, Profiler, Comparator
from .utils import camel_to_snake, snake_to_camel
from ..utils.utils import (set_logger, delete_logger, replace_attr_and_store,
                                     get_specific_dict_param, get_hierarchy_level)
import block_types.config.bt_defaults as dflt

# Cell
class Component ():
    """Base component class used in our Pipeline."""
    def __init__ (self,
                  estimator=None,
                  name: Optional[str] = None,
                  class_name: Optional[str] = None,
                  suffix: Optional[str] = None,
                  group: str = dflt.group,
                  root=None,
                  overwrite_field: bool = dflt.overwrite_field,
                  error_if_present: bool = dflt.error_if_present,
                  ignore:set = set(),
                  but: Union[str, list] = '',
                  data_converter: Optional[DataConverter] = None,
                  data_io: Optional[DataIO] = None,
                  model_plotter: Optional[ModelPlotter] = None,
                  profiler: Optional[Profiler] = None,
                  comparator: Optional[Comparator] = None,
                  apply = None,
                  direct_apply: bool = False,
                  direct_fit: bool = False,
                  direct_fit_apply: bool = False,
                  error_if_apply: bool = False,
                  error_if_fit: bool = False,
                  error_if_fit_apply: bool = False,
                  logger=None,
                  verbose: int = dflt.verbose,
                  name_logger:str = dflt.name_logger,
                  mode_logger:str = dflt.mode_logger,
                  **kwargs):

        """
        Initialize attributes and fields.

        Parameters
        ----------
        estimator : estimator (classifier or transformer) or None, optional
            Estimator being wrapped.
        name : Pipeline or None, optional
            Name of component. If not provided, it is inferred from the name of the
            estimator's class, or the name of the custom class defining the componet.
        data_converter : DataConverter or None, optional
            Converts incoming data to format expected by component, and convert
            outgoing result to format expected by caller.
        data_io : DataIO or None, optional
            Manages data serialization and deserialization.
        model_plotter : ModelPlotter or None, optional
            Helper object that allows to retrieve information to be shown about this
            component, as part of a Pipeline diagram.
        logger : logging.logger or None, optional
            Logger used to write messages
        verbose : int, optional
            Verbosity, 0: warning or critical, 1: info, 2: debug.
        """

        assert not isinstance(estimator, Component), 'estimator cannot be an instance of Component'

        # name of current component, for logging and plotting purposes
        self._determine_component_name (name, estimator, class_name=class_name, suffix=suffix, apply=apply)

        # obtain hierarchy_level
        self.hierarchy_level = get_hierarchy_level (base_class=Component)

        # store __init__ attrs into `self`
        but = ', '.join (but) if isinstance(but, list) else but
        but = (but + ', ') if len(but)>0 else but
        but = but + 'ignore, but, overwrite_field, error_if_present, path_results, path_models, apply'
        if isinstance (ignore, str): ignore = set(re.split(', *', ignore))
        ignore.update ({'name', 'class_name', 'suffix', 'apply', 'data_converter'})
        replace_attr_and_store (base_class=Component, but=but,
                                error_if_present=error_if_present, overwrite=overwrite_field,
                                ignore=ignore)

        if self.logger is None:
            self.logger = set_logger (self.name_logger, verbose=self.verbose, mode=self.mode_logger)

        # obtain class-specific kwargs
        kwargs = self.obtain_config_params (**kwargs)

        # object that manages loading / saving
        if self.data_io is None:
            self.data_io = DataIO (component=self, **kwargs)
        else:
            if 'data_io' in kwargs:
                del kwargs['data_io']
            self.data_io = data_io_factory (self.data_io, component=self, **kwargs)

        self.path_results = self.data_io.path_results
        self.path_models = self.data_io.path_models

        # data converter
        if self.data_converter is None:
            # TODO: have DataConverter store a reference to component, and use the logger from that reference.
            self.data_converter = GenericConverter (**kwargs)
        else:
            if 'data_converter' in kwargs:
                del kwargs['data_converter']
            self.data_converter = data_converter_factory (self.data_converter,
                                                          **kwargs)
        # plotting model component
        if self.model_plotter is None:
            self.model_plotter = ModelPlotter (component=self, **kwargs)
        else:
            self.model_plotter.set_component (self)

        # profiling computational cost
        if self.profiler is None:
            self.profiler = Profiler (self, **kwargs)

        # comparing results against other implementations of this component
        if self.comparator is None:
            self.comparator = Comparator (self, **kwargs)
        elif type(self.comparator) is type:
            self.comparator = self.comparator (self, **kwargs)

        # determine and assign apply and fit functions
        self.assign_apply_and_fit_functions (apply=apply)

    def __repr__ (self):
        return f'Component {self.class_name} (name={self.name})'

    def reset_logger (self):
        delete_logger (self.name_logger)

    def get_specific_data_io_parameters (self, tag, **kwargs):
        suffix = f'_{tag}'
        n = len(suffix)
        return {k[:-n]:kwargs[k]
                for k in kwargs if k.endswith (suffix) and k[:-n] in DataIO.specific_params}

    def obtain_config_params (self, tag=None, **kwargs):
        """Overwrites parameters in kwargs with those found in a dictionary of the same name
        as the component.

        Checks if there is a parameter whose name is the name of the class or the name given
        to this component. In that case, it overwrites the parameters in kwargs with those
        found in that dictionary. The parameters in kwargs can be used as *global* parameters
        for multiple components, while parameters specific of one component can be overwritten
        using a dictionary with the name of that component. See example below.
        """
        k = get_specific_dict_param (self, **kwargs)

        if k is not None:
            config = kwargs.copy()
            config.update (config[k])
        else:
            config = kwargs

        if tag is not None:
            if tag == '__name__': tag = self.name
            self.tag = tag
            config.update (self.get_specific_data_io_parameters (tag, **kwargs))

        config.update(verbose=self.verbose,
                      logger=self.logger)

        return config

    def _determine_component_name (self, name: str, estimator, class_name:Optional[str]=None,
                                   suffix:Optional[str]=None, apply=None) -> None:
        """
        Determines an appropriate name for the component if not provided by input.

        If not provided, it is inferred from the name of the estimator's class, or
        the name of the custom class defining the componet.
        """
        if class_name is not None:
            self.class_name = class_name
        else:
            self.class_name = self.__class__.__name__
            if self.class_name in __all__:
                if estimator is not None: self.class_name = estimator.__class__.__name__
                if apply is not None and hasattr (apply, '__name__'):
                    self.class_name = snake_to_camel (apply.__name__)

        if name is not None:
            self.name = name
        else:
            self.name = camel_to_snake (self.class_name)

        self.suffix = suffix
        if self.suffix is not None:
            self.name = f'{self.name}_{self.suffix}'

    def create_estimator (self, **kwargs):
        self.estimator = Bunch(**kwargs)

    def fit_like (self, *X, y=None, load=None, save=None, split=None,
                  func='_fit', validation_data=None, test_data=None,
                  sequential_fit_apply=False, fit_apply=False, converter_args={}, **kwargs):
        """
        Estimates the parameters of the component based on given data X and labels y.

        Uses the previously fitted parameters if they're found in disk and load
        is True.
        """
        if not fit_apply:
            self.profiler.start_timer ()
            profiler_method = 'fit'
        else:
            profiler_method = 'fit_apply'
        if self.error_if_fit and func=='_fit': raise RuntimeError (f'{self.name} should not call fit')
        if self.error_if_fit_apply and func=='_fit_apply':
            raise RuntimeError (f'{self.name} should not call fit_apply')
        X = self.data_converter.convert_single_tuple_for_fitting (X)
        X = X + (y, ) if y is not None else X

        if split is not None:
            self.original_split = self.data_io.split
            self.set_split (split)

        self.logger.info (f'fitting {self.name} (using {self.data_io.split} data)')

        previous_estimator = None
        if self.data_io.can_load_model (load):
            previous_estimator = self.data_io.load_estimator()

        already_computed = False
        if previous_estimator is not None:
            if func=='_fit':
                already_computed = True
            elif func=='_fit_apply':
                previous_result = None
                if self.data_io.can_load_result (load):
                    previous_result = self.data_io.load_result (split=split)
                already_computed = previous_result is not None
            else:
                raise ValueError (f'function {func} not valid')

        if not already_computed:
            X = copy.deepcopy (X) if self.data_converter.inplace else X
            if func=='_fit_apply':
                X = self.data_converter.convert_before_fit_apply (
                    *X, sequential_fit_apply=sequential_fit_apply, **converter_args)
                X = self.data_converter.convert_no_tuple (X)
            elif func=='_fit':
                X = self.data_converter.convert_before_fitting (*X)
            else:
                raise ValueError (f'function {func} not valid')
            additional_data= self._add_validation_and_test (validation_data, test_data)
            if func=='_fit':
                if len(kwargs) > 0: raise AttributeError (f'kwargs: {kwargs} not valid')
                self.profiler.start_no_overhead_timer ()
                self._fit (*X, **additional_data)
            elif func=='_fit_apply':
                assert self.fit_apply_func is not None, ('object must have _fit_apply method or one of '
                                                    'its aliases implemented when func="_fit_apply"')
                self.profiler.start_no_overhead_timer ()
                result = self.fit_apply_func (*X, **additional_data, **kwargs)
            else:
                raise ValueError (f'function {func} not valid')
            self.profiler.finish_no_overhead_timer (method=profiler_method, split=self.data_io.split)
            if func=='_fit':
                _ = self.data_converter.convert_after_fitting (*X)
            elif func=='_fit_apply':
                result = self.data_converter.convert_after_fit_apply (
                    result, sequential_fit_apply=sequential_fit_apply, **converter_args)
                if self.data_io.can_save_result (save, split):
                    self.data_io.save_result (result, split=split)
            else:
                raise ValueError (f'function {func} not valid')
            if self.data_io.can_save_model (save):
                self.data_io.save_estimator ()
        else:
            self.set_estimator (previous_estimator)
            self.logger.info (f'loaded pre-trained {self.name}')
            if func=='_fit_apply':
                result = previous_result
                self.logger.info (f'loaded pre-computed result')

        if not (fit_apply and func == '_fit'):
            self.profiler.finish_timer (method=profiler_method, split=self.data_io.split)

        if split is not None:
            self.set_split (self.original_split)

        if func=='_fit':
            return self
        else:
            return result

    fit = partialmethod (fit_like, func='_fit')

    def fit_apply (self, *X, y=None, load_model=None, save_model=None,
                   load_result=None, save_result=None, func='_fit',
                   validation_data=None, test_data=None, sequential_fit_apply=False,
                   **kwargs):

        self.profiler.start_timer ()
        if self.error_if_fit_apply: raise RuntimeError (f'{self.name} should not call fit_apply')

        X = self.data_converter.convert_single_tuple_for_fitting (X)
        X = X + (y, ) if y is not None else X

        if self.fit_apply_func is not None:
            return self.fit_like (*X,
                                  load=load_model, save=save_model,
                                  func='_fit_apply', validation_data=validation_data,
                                  test_data=test_data, sequential_fit_apply=sequential_fit_apply,
                                  fit_apply=True, **kwargs)
        else:
            if not self.direct_fit:
                kwargs_fit = dict(load=load_model, save=save_model,
                                  validation_data=validation_data,
                                  test_data=test_data,
                                  sequential_fit_apply=sequential_fit_apply,
                                  fit_apply=True)
            else:
                kwargs_fit = dict()
            if not self.direct_apply:
                kwargs_apply = dict (load=load_result, save=save_result, fit_apply=True,
                                     sequential_fit_apply=sequential_fit_apply, **kwargs)
            else:
                kwargs_apply = kwargs
            return self.fit (*X, **kwargs_fit).apply (*X, **kwargs_apply)

    def _add_validation_and_test (self, validation_data, test_data):
        additional_data = {}
        def add_data (data, split_name):
            if data is not None:
                if isinstance(data, tuple):
                    if len(data) > 0:
                        newX = data[0]
                    else:
                        self.logger.warning (f'empty {split_name}')
                        newX = None
                    if len(data) == 2:
                        newy = data[1]
                    elif len(data)==1:
                        newy = None
                    elif len(data)>2:
                        raise ValueError (f'{split_name} must have at most 2 elements')
                else:
                    newX = data
                    newy = None
                newX, newy = self.data_converter.convert_before_fitting (newX, newy)
                if newy is not None:
                    additional_data[split_name] = (newX, newy)
                else:
                    additional_data[split_name] = newX

        add_data (validation_data, 'validation_data')
        add_data (test_data, 'test_data')

        return additional_data

    # aliases
    fit_transform = fit_apply
    fit_predict = fit_apply

    def __call__ (self, *X, load=None, save=None, fit_apply=False, sequential_fit_apply=False, **kwargs):
        """
        Transforms the data X and returns the transformed data.

        Uses the previously transformed data if it's found in disk and load
        is True.
        """
        if not fit_apply: self.profiler.start_timer ()
        if self.direct_apply: return self.result_func (*X, **kwargs)
        if self.error_if_apply: raise RuntimeError (f'{self.name} should not call apply')
        assert self.result_func is not None, 'apply function not implemented'
        result = self._compute_result (X, self.result_func, load=load, save=save, fit_apply=fit_apply,
                                       sequential_fit_apply=sequential_fit_apply, **kwargs)
        return result

    def _assign_fit_func (self):
        self.fit_func = None
        self.estimator_fit_func = None
        if callable(getattr(self, '_fit', None)):
            self.fit_func = self._fit
        elif self.estimator is not None and callable(getattr(self.estimator, 'fit', None)):
            self.fit_func = self.estimator.fit
            self.estimator_fit_func = 'fit'

    def _assign_result_func (self):
        implemented = []
        self.result_func = None
        self.estimator_result_func = None
        if callable(getattr(self, '_apply', None)):
            self.result_func = self._apply
            implemented += [self.result_func]
        if callable(getattr(self, '_transform', None)):
            self.result_func = self._transform
            implemented += [self.result_func]
        if callable(getattr(self, '_predict', None)):
            self.result_func = self._predict
            implemented += [self.result_func]
        if len(implemented)==0:
            if self.estimator is not None and callable(getattr(self.estimator, 'transform', None)):
                self.result_func = self.estimator.transform
                self.estimator_result_func = 'transform'
                implemented += [self.result_func]
            if self.estimator is not None and callable(getattr(self.estimator, 'predict', None)):
                self.result_func = self.estimator.predict
                self.estimator_result_func = 'predict'
                implemented += [self.result_func]
        if len(implemented) > 1:
            raise AttributeError (f'{self.class_name} must have only one of _transform, _apply, '
                                  f'or _predict methods implemented => found: {implemented}')

    def _assign_fit_apply_func (self):
        implemented = []
        self.fit_apply_func = None
        self.estimator_fit_apply_func = None
        if callable(getattr(self, '_fit_apply', None)):
            self.fit_apply_func = self._fit_apply
            implemented += [self.fit_apply_func]
        if callable(getattr(self, '_fit_transform', None)):
            self.fit_apply_func = self._fit_transform
            implemented += [self.fit_apply_func]
        if callable(getattr(self, '_fit_predict', None)):
            self.fit_apply_func = self._fit_predict
            implemented += [self.fit_apply_func]
        if len(implemented)==0:
            if self.estimator is not None and callable(getattr(self.estimator, 'fit_transform', None)):
                self.fit_apply_func = self.estimator.fit_transform
                self.estimator_fit_apply_func = 'fit_transform'
                implemented += [self.fit_apply_func]
            if self.estimator is not None and callable(getattr(self.estimator, 'fit_predict', None)):
                self.fit_apply_func = self.estimator.fit_predict
                self.estimator_fit_apply_func = 'fit_predict'
                implemented += [self.fit_apply_func]
        if len(implemented) > 1:
            raise AttributeError (f'{self.class_name} must have only one of fit_transform, fit_apply, '
                                  f'or fit_predict methods implemented => found: {implemented}')

    def assign_apply_and_fit_functions (self, apply=None):
        """Determine and assign apply and fit functions."""
        if apply is not None: self._apply = apply
        self._assign_result_func ()
        self._assign_fit_apply_func ()
        self._assign_fit_func ()
        self.is_model = True
        if self.fit_func is None:
            self._fit = self._fit_
            if self.fit_apply_func is None:
                self.is_model = False
        else:
            self._fit = self.fit_func
        if self.direct_apply:
            self.set_apply (self.result_func)
        if not self.is_model:
            self.fit = self._fit_
            # self.set_fit_apply (self.apply)
        else:
            if self.direct_fit:
                self.fit = self.fit_func
            if self.direct_fit_apply:
                self.set_fit_apply (self.fit_apply_func)

    # aliases for transform method
    apply = __call__
    transform = __call__
    predict = partialmethod (__call__, converter_args=dict(new_columns=['prediction']))

    def _compute_result (self, X, result_func, load=None, save=None, split=None,
                         converter_args={}, fit_apply=False,
                         sequential_fit_apply=False, **kwargs):

        profiler_method = 'fit_apply' if fit_apply else 'apply'
        if split is not None:
            self.original_split = self.data_io.split
            self.set_split (split)

        self.logger.debug (f'applying {self.name} (on {self.data_io.split} data)')

        previous_result = None
        if self.data_io.can_load_result (load):
            previous_result = self.data_io.load_result (split=split)
        if previous_result is None:
            X = self.data_converter.convert_single_tuple_for_transforming (X)
            X = self.data_converter.convert_before_transforming (
                *X, fit_apply=fit_apply, sequential_fit_apply=sequential_fit_apply, **converter_args)
            X = self.data_converter.convert_no_tuple (X)
            X = self.data_converter.convert_single_tuple_for_result_func (X)
            self.profiler.start_no_overhead_timer ()
            result = result_func (*X, **kwargs)
            self.profiler.finish_no_overhead_timer (profiler_method, self.data_io.split)
            result = self.data_converter.convert_after_transforming (
                result, fit_apply=fit_apply, sequential_fit_apply=sequential_fit_apply, **converter_args)
            if self.data_io.can_save_result (save, split):
                self.data_io.save_result (result, split=split)
        else:
            result = previous_result
            self.logger.info (f'loaded pre-computed result')

        self.profiler.finish_timer (profiler_method, self.data_io.split)
        if split is not None:
            self.set_split (self.original_split)

        return result

    def _fit_ (self, *X, **kwargs):
        return self

    def show_result_statistics (self, result=None, split=None) -> None:
        """
        Show statistics of transformed data.

        Parameters
        ----------
        result: DataFrame or other data structure or None, optional
            Transformed data whose statistics we show. If not provided, it is loaded
            from disk.
        training_data_flag: bool, optional
            If True, transformed training data is loaded, otherwise transformed test
            data is loaded.
        """
        if result is None:
            df = self.load_result(split=split)
        else:
            df = result

        if df is not None:
            display (self.name)
            if callable(getattr(df, 'describe', None)):
                display (df.describe())
            elif isinstance(df, np.ndarray) or isinstance(df, list):
                df = pd.DataFrame (df)
                display (df.describe())

    def remove_non_pickable_fields (self):
        pass

    # ********************************
    # exposing some data_io and data_converters methods
    # ********************************
    def load_estimator (self):
        estimator = self.data_io.load_estimator ()
        if estimator is not None:
            self.set_estimator (estimator)

    def load_result (self, split=None, path_results=None, result_file_name=None):
        return self.data_io.load_result (split=split, path_results=path_results,
                                         result_file_name=result_file_name)

    def assert_equal (self, item1, item2=None, split=None, raise_error=True, **kwargs):
        return self.comparator.assert_equal (item1, item2=item2, split=split,
                                             raise_error=raise_error, **kwargs)

    # ********************************
    # setters
    # ********************************
    def set_split (self, split):
        self.data_io.set_split (split)

    def set_save_splits (self, save_splits):
        self.data_io.set_save_splits (save_splits)

    def set_save_model (self, save_model):
        self.data_io.set_save_model (save_model)

    def set_load_model (self, load_model):
        self.data_io.set_load_model (load_model)

    def set_save_result (self, save_result):
        self.data_io.set_save_result (save_result)

    def set_load_result (self, load_result):
        self.data_io.set_load_result (load_result)

    def set_data_io (self, data_io, copy=False):
        self.data_io = copy.copy(data_io) if copy else data_io
        self.data_io.setup (self)

    def set_name (self, name):
        self.name = name
        self.data_io.set_file_names (name)

    def set_estimator (self, estimator):
        self.estimator = estimator
        if self.estimator_result_func is not None:
            self.result_func = getattr (self.estimator, self.estimator_result_func, None)
            assert callable (self.result_func)
        if self.estimator_fit_apply_func is not None:
            self.fit_apply_func = getattr (self.estimator, self.estimator_fit_apply_func, None)
            assert callable (self.fit_apply_func)
        if self.estimator_fit_func is not None:
            self.fit_func = getattr (self.estimator, self.estimator_fit_func, None)
            assert callable (self.fit_func)
            self._fit = self.fit_func
            assert self.is_model

    def set_apply (self, result_func):
        self.apply = result_func
        self.__call__ = result_func
        self.transform = result_func
        self.predict = result_func

    def set_fit_apply (self, fit_apply_func):
        self.fit_apply = fit_apply_func
        self.fit_transform = fit_apply_func
        self.fit_predict = fit_apply_func

# Cell
class SamplingComponent (Component):
    """
    Component that makes use of labels in transform method.

    When calling the transform method, one of the columns of the received data
    is assumed to contain the ground-truth labels. This allows the transform
    method to modify the number of observations, changing the number of rows in
    the data and in the labels. See `PandasConverter` class in
    `block_types.core.data_conversion`.
    """
    def __init__ (self, estimator=None, transform_uses_labels=True, **kwargs):

        # the SamplingComponent over-rides the following parameters:
        super().__init__ (estimator=estimator, transform_uses_labels=transform_uses_labels,
                          **kwargs)

# Cell
class SklearnComponent (Component):
    """
    Component that saves estimator parameters in pickle format.

    Convenience subclass used when the results can be saved in
    pickle format. See `SklearnIO` class in `core.utils`.
    """
    def __init__ (self, estimator=None, data_io='SklearnIO', transform_uses_labels=False,
                  **kwargs):

        super().__init__ (estimator=estimator, data_io=data_io, transform_uses_labels=False,
                          **kwargs)

# alias
PickleSaverComponent = SklearnComponent

# Cell
class NoSaverComponent (Component):
    """Component that does not save any data."""
    def __init__ (self, estimator=None, data_io='NoSaverIO', **kwargs):

        super().__init__ (estimator=estimator, data_io=data_io, **kwargs)

# Cell
class OneClassSklearnComponent (SklearnComponent):
    """Component that uses only normal data (labelled with 0) for fitting parameters."""
    def __init__ (self, estimator=None, **kwargs):
        super().__init__ (estimator=estimator, **kwargs)

    def _fit (self, X, y=None):
        assert y is not None, 'y must be provided in OneClassSklearnComponent class'
        X = X[y==0]

        assert self.estimator is not None, 'estimator must be provided in OneClassSklearnComponent class'
        self.estimator.fit (X, y)

# Cell
class PandasComponent (Component):
    """
    Component that preserves the DataFrame format for incoming data and results.

    This component also writes results in parquet format, by default.
    See `PandasConverter` in `core.data_conversion` for details on the data
    conversion performed.
    """
    def __init__ (self, estimator=None, data_converter='PandasConverter', data_io='PandasIO',
                  **kwargs):
        super().__init__ (estimator=estimator, data_converter=data_converter, data_io=data_io,
                          **kwargs)