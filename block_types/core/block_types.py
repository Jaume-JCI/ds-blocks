# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/core.block_types.ipynb (unless otherwise specified).

__all__ = ['Component', 'SamplingComponent', 'SklearnComponent', 'PickleSaverComponent', 'NoSaverComponent',
           'OneClassSklearnComponent', 'PandasComponent']

# Cell
from sklearn.base import BaseEstimator, ClassifierMixin, TransformerMixin
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pyarrow as pa
import joblib
import pickle
from pathlib import Path
from IPython.display import display
from typing import Optional
import copy

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
from ..config import defaults as dflt
from ..utils.utils import set_logger

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

        # logger used to display messages
        if logger is None:
            self.logger = set_logger ('block_types', verbose=verbose)
        else:
            self.logger = logger

        # name of current component, for logging and plotting purposes
        self._determine_component_name (name, estimator)

        # object that manages loading / saving
        if data_io is None:
            self.data_io = DataIO (component=self, **kwargs)
        else:
            self.data_io = copy.copy(data_io)
            self.data_io.setup (self)

        # estimator (ML model)
        self.estimator = estimator

        # data converter
        if data_converter is None:
            self.data_converter = NoConverter ()
        else:
            self.data_converter = data_converter

        # plotting model component
        if model_plotter is None:
            self.model_plotter = ModelPlotter (component=self, **kwargs)
        else:
            self.model_plotter = model_plotter
            self.model_plotter.set_component (self)

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

    def fit (self, X, y=None, load=True, save=True):
        """
        Estimates the parameters of the component based on given data X and labels y.

        Uses the previously fitted parameters if they're found in disk and overwrite
        is False.
        """
        self.logger.info (f'fitting {self.name}')

        previous_estimator = None
        if load and not self.data_io.overwrite:
            previous_estimator = self.data_io.load_estimator()

        if previous_estimator is None:
            X, y = self.data_converter.convert_before_fitting (X, y)
            self._fit (X, y)
            self.data_converter.convert_after_fitting (X)
            if save:
                self.data_io.save_estimator ()
        else:
            self.estimator = previous_estimator
            self.logger.info (f'loaded pre-trained {self.name}')
        return self

    def transform (self, *X, load=True, save=True):
        """
        Transforms the data X and returns the transformed data.

        Uses the previously transformed data if it's found in disk and overwrite
        is False.
        """
        if callable(getattr(self, '_apply', None)):
            result_func = self._apply
        elif callable(getattr(self, '_transform', None)):
            result_func = self._transform
        else:
            AttributeError (f'{self.class_name} must have either _transform or _apply methods')
        self.logger.info (f'applying {self.name} transform')
        result= self._compute_result (X, result_func, load=load, save=save)
        return result

    def predict (self, *X, load=True, save=True):
        """
        Predicts binary labels and returns result.

        Uses previously stored predictions if found in disk and overwrite is False.
        """
        self.logger.info (f'applying {self.name} inference')
        return self._compute_result (X, self._predict, new_columns=['prediction'], load=load, save=save)

    # aliases for transform method
    __call__ = transform
    apply = transform

    def _compute_result (self, X, result_func, load=True, save=True, **kwargs):
        if len(X) == 1:
            X = X[0]
        previous_result = None
        if load and not self.data_io.overwrite:
            previous_result = self.data_io.load_result()
        if previous_result is None:
            X = self.data_converter.convert_before_transforming (X, **kwargs)
            if type(X) is tuple:
                result = result_func (*X)
            else:
                result = result_func (X)
            result = self.data_converter.convert_after_transforming (result, **kwargs)
            if save:
                self.data_io.save_result (result)
        else:
            result = previous_result
            self.logger.info (f'loaded pre-computed result')
        return result


    def _fit (self, X, y=None):
        if self.estimator is not None:
            self.estimator.fit (X, y)

    def _transform (self, X):
        if self.estimator is not None:
            return self.estimator.transform (X)
        else:
            raise NotImplementedError ('estimator is None _transform method probably needs to be implemented in subclass')

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
    # setters
    # ********************************
    def set_training_data_flag (self, training_data_flag):
        self.data_io.set_training_data_flag (training_data_flag)

    def set_save_result_flag_test (self, save_result_flag_test):
        self.data_io.set_save_result_flag_test (save_result_flag_test)

    def set_save_result_flag_training (self, save_result_flag_training):
        self.data_io.set_save_result_flag_training (save_result_flag_training)

    def set_save_result_flag (self, save_result_flag):
        self.data_io.set_save_result_flag (save_result_flag)

    def set_overwrite (self, overwrite):
        self.data_io.set_overwrite (overwrite)

    def set_save_fitting (self, save_fitting):
        self.data_io.set_save_fitting (save_fitting)

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