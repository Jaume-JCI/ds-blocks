# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/core.block_types.ipynb (unless otherwise specified).

__all__ = ['Component', 'SamplingComponent', 'SklearnComponent', 'PickleSaverComponent', 'NoSaverComponent',
           'OneClassSklearnComponent', 'PandasComponent']

# Cell
from functools import partialmethod
from typing import Optional
import copy
import pickle
from pathlib import Path

from sklearn.base import BaseEstimator, ClassifierMixin, TransformerMixin
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pyarrow as pa
import joblib
from IPython.display import display

try:
    from graphviz import *
    imported_graphviz = True
except:
    imported_graphviz = False

# block_types
from .data_conversion import DataConverter, NoConverter, PandasConverter
from .utils import save_csv, save_parquet, save_multi_index_parquet, save_keras_model, save_csv_gz, read_csv, read_csv_gz
from .utils import DataIO, SklearnIO, PandasIO, NoSaverIO, ModelPlotter
from .utils import camel_to_snake
from ..utils.utils import set_logger, replace_attr_and_store, get_specific_dict_param

# Cell

class Component (ClassifierMixin, TransformerMixin, BaseEstimator):
    """Base component class used in our Pipeline."""
    def __init__ (self,
                  estimator=None,
                  name: Optional[str] = None,
                  data_converter: Optional[DataConverter] = None,
                  data_io: Optional[DataIO] = None,
                  model_plotter: Optional[ModelPlotter] = None,
                  logger=None,
                  verbose: int = 0,
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

        # name of current component, for logging and plotting purposes
        self._determine_component_name (name, estimator)

        # store __init__ attrs into `self`
        replace_attr_and_store (base_class=Component, but='name')

        if self.logger is None:
            self.logger = set_logger ('block_types', verbose=verbose)

        # object that manages loading / saving
        if self.data_io is None:
            self.data_io = DataIO (component=self, **kwargs)
        else:
            self.data_io = copy.copy(self.data_io)
            self.data_io.setup (self)

        # data converter
        if self.data_converter is None:
            # TODO: have DataConverter store a reference to component, and use the logger from that reference.
            self.data_converter = NoConverter (logger=self.logger,
                                               verbose=self.verbose,
                                               **kwargs)

        # plotting model component
        if self.model_plotter is None:
            self.model_plotter = ModelPlotter (component=self, **kwargs)
        else:
            self.model_plotter.set_component (self)

    def obtain_config_params (self, **kwargs):
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

        return config

    def _determine_component_name (self, name: Optional[str], estimator) -> None:
        """
        Determines an appropriate name for the component if not provided by input.

        If not provided, it is inferred from the name of the estimator's class, or
        the name of the custom class defining the componet.
        """
        self.class_name = self.__class__.__name__
        if (self.class_name in __all__) and (estimator is not None):
            self.class_name = estimator.__class__.__name__

        if name is not None:
            self.name = name
        else:
            self.name = camel_to_snake (self.class_name)

    def fit_like (self, X, y=None, load=None, save=None, split=None,
                  func='_fit', validation_data=None, test_data=None, **kwargs):
        """
        Estimates the parameters of the component based on given data X and labels y.

        Uses the previously fitted parameters if they're found in disk and load
        is True.
        """
        if split is not None:
            self.original_split = self.data_io.split
            self.set_split (split)

        self.logger.info (f'fitting {self.name} (using {self.data_io.split} data)')

        previous_estimator = None
        if self.data_io.can_load_model (load):
            previous_estimator = self.data_io.load_estimator()

        if previous_estimator is None:
            X, y = self.data_converter.convert_before_fitting (X, y)
            additional_data= self._add_validation_and_test (validation_data, test_data)
            if func=='_fit':
                if len(kwargs) > 0:
                    raise AttributeError (f'kwargs: {kwargs} not valid')
                self._fit (X, y, **additional_data)
            elif func=='_fit_apply':
                fit_apply_func = self._determine_fit_apply_func ()
                assert fit_apply_func is not None, ('object must have _fit_apply method or one of '
                                                    'its aliases implemented when func="_fit_apply"')
                result = fit_apply_func (X, y=y, **additional_data, **kwargs)
            else:
                raise ValueError (f'function {func} not valid')
            self.data_converter.convert_after_fitting (X)
            if self.data_io.can_save_model (save):
                self.data_io.save_estimator ()
        else:
            self.estimator = previous_estimator
            self.logger.info (f'loaded pre-trained {self.name}')

        if split is not None:
            self.set_split (self.original_split)

        if func=='_fit':
            return self
        else:
            return result

    fit = partialmethod (fit_like, func='_fit')

    def fit_apply (self, X, y=None, load_model=None, save_model=None,
                   load_result=None, save_result=None, func='_fit',
                   validation_data=None, test_data=None, **kwargs):

        if self._determine_fit_apply_func () is not None:
            return self.fit_like (X, y=y,
                                  load=load_model, save=save_model,
                                  func='_fit_apply', validation_data=validation_data,
                                  test_data=test_data, **kwargs)
        else:
            return self.fit (X, y=y,
                             load=load_model, save=save_model,
                             validation_data=validation_data,
                             test_data=test_data).apply (X, load=load_result,
                                                         save=save_result, **kwargs)

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

    def apply (self, *X, load=None, save=None, **kwargs):
        """
        Transforms the data X and returns the transformed data.

        Uses the previously transformed data if it's found in disk and load
        is True.
        """

        result_func = self._determine_result_func ()
        result = self._compute_result (X, result_func, load=load, save=save, **kwargs)
        return result

    def _determine_result_func (self):
        implemented = []
        if callable(getattr(self, '_apply', None)):
            result_func = self._apply
            implemented += [result_func]
        if callable(getattr(self, '_transform', None)):
            result_func = self._transform
            implemented += [result_func]
        if callable(getattr(self, '_predict', None)):
            result_func = self._predict
            implemented += [result_func]
        if len(implemented)==0:
            if self.estimator is not None and callable(getattr(self.estimator, 'transform', None)):
                result_func = self.estimator.transform
                implemented += [result_func]
            if self.estimator is not None and callable(getattr(self.estimator, 'predict', None)):
                result_func = self.estimator.predict
                implemented += [result_func]
        if len (implemented) == 0:
            raise AttributeError (f'{self.class_name} must have one of _transform, _apply, or _predict methods implemented\n'
                                  f'Otherwise, self.estimator must have either predict or transform methods')
        if len(implemented) > 1:
            raise AttributeError (f'{self.class_name} must have only one of _transform, _apply, '
                                  f'or _predict methods implemented => found: {implemented}')
        return result_func

    def _determine_fit_apply_func (self):
        implemented = []
        result_func = None
        if callable(getattr(self, '_fit_apply', None)):
            result_func = self._fit_apply
            implemented += [result_func]
        if callable(getattr(self, '_fit_transform', None)):
            result_func = self._fit_transform
            implemented += [result_func]
        if callable(getattr(self, '_fit_predict', None)):
            result_func = self._fit_predict
            implemented += [result_func]
        if len(implemented)==0:
            if self.estimator is not None and callable(getattr(self.estimator, 'fit_transform', None)):
                result_func = self.estimator.fit_transform
                implemented += [result_func]
            if self.estimator is not None and callable(getattr(self.estimator, 'fit_predict', None)):
                result_func = self.estimator.fit_predict
                implemented += [result_func]
        if len(implemented) > 1:
            raise AttributeError (f'{self.class_name} must have only one of fit_transform, fit_apply, '
                                  f'or fit_predict methods implemented => found: {implemented}')
        return result_func

    # aliases for transform method
    __call__ = apply
    transform = apply
    predict = partialmethod (apply, converter_args=dict(new_columns=['prediction']))

    def _compute_result (self, X, result_func, load=None, save=None, split=None,
                         converter_args={}, **kwargs):

        if split is not None:
            self.original_split = self.data_io.split
            self.set_split (split)

        self.logger.info (f'applying {self.name} (on {self.data_io.split} data)')

        if len(X) == 1:
            X = X[0]
        previous_result = None
        if self.data_io.can_load_result (load):
            previous_result = self.data_io.load_result (split=split)
        if previous_result is None:
            X = self.data_converter.convert_before_transforming (X, **converter_args)
            if type(X) is tuple:
                result = result_func (*X, **kwargs)
            else:
                result = result_func (X, **kwargs)
            result = self.data_converter.convert_after_transforming (result, **converter_args)
            if self.data_io.can_save_result (save, split):
                self.data_io.save_result (result, split=split)
        else:
            result = previous_result
            self.logger.info (f'loaded pre-computed result')

        if split is not None:
            self.set_split (self.original_split)

        return result


    def _fit (self, X, y=None):
        if self.estimator is not None:
            self.estimator.fit (X, y)

    def show_result_statistics (self, result=None, training_data_flag=False) -> None:
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
            self.set_training_data_flag (training_data_flag)
            df = self.data_io.load_result()
        else:
            df = result

        if df is not None:
            display (self.name)
            if callable(getattr(df, 'describe', None)):
                display (df.describe())

    def assert_equal (self, path_reference_results: str, assert_equal_func=pd.testing.assert_frame_equal, **kwargs):
        """
        Check whether the transformed data is the same as the reference data stored in given path.

        Parameters
        ----------
        path_reference_results: str
            Path where reference results are stored. The path does not include the
            file name, since this is stored as a field of data_io.
        assert_equal_func: function, optional
            Function used to check whether the values are the same. By defaut,
            `pd.testing.assert_frame_equal` is used, which assumes the data type is
            DataFrame.

        """
        type_result = 'training' if self.data_io.training_data_flag else 'test'
        self.logger.info (f'comparing {type_result} results for {self.class_name}')

        self.logger.info (f'loading...')
        current_results = self.data_io.load_result ()
        if self.data_io.training_data_flag:
            path_to_reference_file = Path(path_reference_results) / self.data_io.result_file_name_training
        else:
            path_to_reference_file = Path(path_reference_results) / self.data_io.result_file_name_test
        reference_results = self.data_io._load (path_to_reference_file, self.data_io.result_load_func)
        self.logger.info (f'comparing...')
        assert_equal_func (current_results, reference_results, **kwargs)
        self.logger.info (f'equal results\n')

    # ********************************
    # exposing some data_io and data_converters methods
    # ********************************
    def load_estimator (self):
        estimator = self.data_io.load_estimator ()
        if estimator is not None:
            self.estimator = estimator

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

# ******************************************
# Subclasses of Component.
# Most of these are basically the same as GenericComponent, the only difference being that some parameters
# are over-riden when constructing the object, to force a specific behavior
# ******************************************

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
    def __init__ (self,
                  estimator=None,
                  transform_uses_labels=True,
                  **kwargs):

        # the SamplingComponent over-rides the following parameters:
        super().__init__ (estimator=estimator,
                          transform_uses_labels=transform_uses_labels,
                          **kwargs)

# Cell
class SklearnComponent (Component):
    """
    Component that saves estimator parameters in pickle format.

    Convenience subclass used when the results can be saved in
    pickle format. See `SklearnIO` class in `core.utils`.
    """
    def __init__ (self,
                  estimator=None,
                  data_io=None,
                  transform_uses_labels=False,
                  **kwargs):

        if data_io is None:
            data_io = SklearnIO (**kwargs)

        super().__init__ (estimator=estimator,
                          data_io = data_io,
                          transform_uses_labels=False,
                          **kwargs)

# alias
PickleSaverComponent = SklearnComponent

# Cell
class NoSaverComponent (Component):
    """Component that does not save any data."""
    def __init__ (self,
                  estimator=None,
                  data_io=None,
                  **kwargs):

        if data_io is None:
            data_io = NoSaverIO (**kwargs)

        super().__init__ (estimator=estimator,
                          data_io=data_io,
                          **kwargs)

# Cell
class OneClassSklearnComponent (SklearnComponent):
    """Component that uses only normal data (labelled with 0) for fitting parameters."""
    def __init__ (self,
                  estimator=None,
                  **kwargs):
        super().__init__ (estimator=estimator,
                          **kwargs)

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
    def __init__ (self,
                  estimator=None,
                  data_converter=None,
                  data_io=None,
                  **kwargs):

        if data_converter is None:
            data_converter = PandasConverter (**kwargs)
        if data_io is None:
            data_io = PandasIO (**kwargs)

        super().__init__ (estimator=estimator,
                          data_converter=data_converter,
                          data_io=data_io,
                          **kwargs)