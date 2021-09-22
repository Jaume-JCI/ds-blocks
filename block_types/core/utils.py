# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/core.utils.ipynb (unless otherwise specified).

__all__ = ['save_csv', 'save_parquet', 'save_multi_index_parquet', 'save_keras_model', 'save_csv_gz', 'read_csv',
           'read_csv_gz', 'load_keras_model', 'DataIO', 'PandasIO', 'PickleIO', 'SklearnIO', 'NoSaverIO',
           'ModelPlotter', 'camel_to_snake']

# Cell
from pathlib import Path
import re
from functools import partialmethod
from sklearn.base import BaseEstimator, ClassifierMixin, TransformerMixin
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pyarrow as pa
import joblib
import pickle
from IPython.display import display

try:
    from graphviz import *
    imported_graphviz = True
except:
    imported_graphviz = False

# block_types
from .data_conversion import PandasConverter
from ..config import defaults as dflt
from ..utils.utils import set_logger

# Cell
def save_csv (df, path, **kwargs):
    """
    Save DataFrame `df` to csv file indicated in `path`.

    Convenience function that uses the same signature
    as joblib.dump, which is needed by `DataIO`.
    """
    df.to_csv (path, **kwargs)

# Cell
def save_parquet (df, path, **kwargs):
    """
    Save DataFrame `df` to parquet file indicated in `path`.

    Convenience function that uses the same signature
    as joblib.dump, which is needed by `DataIO`.
    """
    df.to_parquet (path, **kwargs)

# Cell
def save_multi_index_parquet (df, path, **kwargs):
    """
    Save DataFrame `df` to multi-index parquet file indicated in `path`.

    Convenience function that uses the same signature
    as joblib.dump, which is needed by `DataIO`.
    """
    table = pa.Table.from_pandas(df)
    pq.write_table(table, path)

# Cell
def save_keras_model (model, path, **kwargs):
    """
    Save keras `model` to file indicated in `path`.

    Convenience function that uses the same signature
    as joblib.dump, which is needed by `DataIO`.
    """
    model.save (path, **kwargs)

# Cell
def save_csv_gz (df, path, **kwargs):
    """
    Save DataFrame `df` to csv.gz file indicated in `path`.

    Convenience function that uses the same signature
    as joblib.dump, which is needed by `DataIO`.
    """
    df.to_csv (path, compression='gzip', **kwargs)

# Cell
def read_csv (path, **kwargs):
    """
    Read DataFrame from csv file indicated in `path`.

    Convenience function that uses the same signature
    as joblib.load, which is needed by `DataIO`.
    """
    return pd.read_csv (path, index_col=0, parse_dates=True, **kwargs)

# Cell
def read_csv_gz (path, **kwargs):
    """
    Read DataFrame from csv.gz file indicated in `path`.

    Convenience function that uses the same signature
    as joblib.load, which is needed by `DataIO`.
    """
    return pd.read_csv (path, index_col=0, parse_dates=True, compression='gzip', **kwargs)

# Cell
def load_keras_model (path, **kwargs):
    import tensorflow.keras as keras
    return keras.models.load_model(path)

# Cell
class DataIO ():
    def __init__ (self,
                  component=None,
                  path_results=dflt.path_results,
                  fitting_file_name = None,
                  fitting_file_extension='',
                  fitting_load_func=None,
                  fitting_save_func=None,
                  save_fitting=True,

                  result_file_extension='',
                  result_file_name_training=None,
                  result_file_name_test=None,
                  result_load_func=None,
                  result_save_func=None,
                  save_training_result=True,
                  save_test_result=True,
                  save_result=True,
                  save=True,
                  load=True,
                  overwrite=dflt.overwrite,
                  **kwargs):
        """
        Initialize common attributes and fields.

        Parameters
        ----------
        component : Component or None, optional
            reference to component that uses the DataIO object.
            By storing this reference, the DataIO class behaves very much
            like a callback object that keeps the state and internal parameters
            of the caller for greater flexibility.
            This reference is currently used mainly for accessing the estimator
            that is part of the component, since sometimes this estimator is
            initialized after the component's construction. The reference is
            also used for getting access to the name and class of the
            Component,  for determining the names of the files where
            results are saved.
        path_results : str or Path or None, optional
            Path to results folder where estimator's parameters and transformed
            data are stored.
        fitting_file_name : str or None, optional
            Name of the file used for storing the estimator's parameters.
            If not provided, the name of the component is used. This name
            is usually the name of the class of the component converted to
            snake case.
        fitting_file_extension : str or None, optional
            Extension of the file where the estimator's parameters are
            saved. By default, no extension is used.
        fitting_load_func : function or None, optional
            Function used for loading the stored parameters of the estimator.
            If None is given, the parameters are not loaded. This function
            must have the following signature:
            estimator_parameters = fitting_load_func (path_to_file)
        fitting_save_func : function or None, optional
            Function used for saving the stored parameters of the estimator.
            If None is given, the parameters are not saved. This function
            must have the following signature:
            fitting_save_func (estimator_parameters, path_to_file)
        result_file_extension : str or None, optional
            Extension of the file where the transformed data is saved.
            By default, no extension is used.
        result_file_name_training : str or None, optional
            Name of the file used for storing the transformed training data.
            If not provided, it constructed based on the name of the component.
        result_file_name_test : str or None, optional
            Name of the file used for storing the transformed test data.
            If not provided, it constructed based on the name of the component.
        result_load_func : function or None, optional
            Function used for loading the transformed data. By default, this
            function is `pd.read_parquet`. The provided function must have the
            following signature:
            transformed_data = result_load_func (path_to_file)
        result_save_func : function, optional
            Function used for saving the transformed data. By default, the
            function used is `save_multi_index_parquet` (see above). The
            provided function must have the following signature:
            result_save_func (transformed_data, path_to_file)
        save_training_result : bool, optional
            If True, the transformed training data is saved.
        save_test_result : bool, optional
            If True, the transformed test data is saved.
        save : bool, optional
            If False, neither transformed data nor estimated parameters are saved,
            regardless of the other arguments.
        load: bool, optional
            If False, neither transformed data nor estimated parameters are loaded,
            regardless of the other arguments.
        overwrite : bool, optional
            If True, any existing file with the same name is overwritten.
        """

        self.path_results = path_results

        # saving / loading estimator parameters
        self.fitting_file_name = fitting_file_name
        self.fitting_file_extension = fitting_file_extension
        self.fitting_load_func = fitting_load_func
        self.fitting_save_func = fitting_save_func
        self.set_save_fitting (save_fitting)

        # saving / loading transformed data
        self.result_file_extension = result_file_extension
        self.result_load_func = result_load_func
        self.result_save_func = result_save_func

        # saving / loading transformed training data
        self.result_file_name_training = result_file_name_training
        self.set_save_result_flag_training (save_training_result)

        # saving / loading transformed test data
        self.result_file_name_test = result_file_name_test
        self.set_save_result_flag_test (save_test_result)

        # whether the transformation has been applied to training data (i.e., to be saved in training path)
        # or to test data (i.e,. to be saved in test path)
        self.training_data_flag = False

        # whether existing files should be overwritten or not
        self.set_overwrite (overwrite)

        # global saving and loading
        self.set_save (save)
        self.set_load (load)

        self.path_result_file_training = None
        self.path_model_file = None
        self.path_result_file_test = None

        if component is not None:
            self.setup (component)
        else:
            self.component = None

    def setup (self, component=None):
        """
        Initialize remaining fields given `component` from which data is saved/loaded.

        We use the name of `component` for inferring the name of the files
        where the data is saved / loaded. The reason why we need to do this in a
        separate setup method is because the component might be unknown when
        constructing the DataIO object in the subclasses below (see for instance
        SklearnIO subclass)
        """

        self.component = component

        # configuration for saving / loading fitted estimator
        if self.fitting_file_name is None:
            self.fitting_file_name = f'{self.component.name}_estimator{self.fitting_file_extension}'

        # configuration for saving / loading result of transforming training data
        if self.result_file_name_training is None:
            self.result_file_name_training = f'{self.component.name}_result_training{self.result_file_extension}'

        # configuration for saving / loading result of transforming test data
        if self.result_file_name_test is None:
            self.result_file_name_test = f'{self.component.name}_result_test{self.result_file_extension}'

        if self.path_results is not None:
            self.path_results = Path(self.path_results).resolve()
            self.path_result_file_training = self.path_results / self.result_file_name_training
            self.path_model_file = self.path_results / self.fitting_file_name
            self.path_result_file_test = self.path_results / self.result_file_name_test
        else:
            self.path_result_file_training = None
            self.path_model_file = None
            self.path_result_file_test = None

    def load_estimator (self):
        """Load estimator parameters."""
        estimator = self._load (path=self.path_model_file, load_func=self.fitting_load_func)
        return estimator

    def save_estimator (self):
        """Save estimator parameters."""
        estimator = self.component.estimator if (self.component.estimator is not None) else self.component
        self._save (self.path_model_file, self.fitting_save_func, estimator, self.save_fitting)

    def load_result (self):
        """
        Load transformed data.

        Transformed training data is loaded if self.training_data_flag=True,
        otherwise transformed test data is loaded.
        """
        if self.training_data_flag:
            return self.load_training_result ()
        else:
            return self.load_test_result ()

    def load_training_result (self):
        """Load transformed training data."""
        return self._load (self.path_result_file_training, self.result_load_func)

    def load_test_result (self):
        """Load transformed test data."""
        return self._load (self.path_result_file_test, self.result_load_func)

    def save_result (self, result):
        """
        Save transformed data.

        Transformed training data is saved if self.training_data_flag=True,
        otherwise transformed test data is saved.
        """
        if self.training_data_flag:
            self.save_training_result (result)
        else:
            self.save_test_result (result)

    def save_training_result (self, result):
        """Save transformed training data."""
        return self._save (self.path_result_file_training, self.result_save_func, result, self.save_result_flag_training)

    def save_test_result (self, result):
        """Save transformed test data."""
        return self._save (self.path_result_file_test, self.result_save_func, result, self.save_result_flag_test)

    def _load (self, path, load_func):
        if (path is not None) and path.exists() and self.load:
            self.component.logger.info (f'loading from {path}')
            return load_func (path)
        else:
            return None

    def _save (self, path, save_func, item, save_flag):
        if (path is not None) and (save_func is not None) and save_flag and self.save:
            self.component.logger.debug (f'saving to {path}')
            # create parent directory if it does not exist
            self.path_results.mkdir(parents=True, exist_ok=True)
            # save data using save_func
            try:
                save_func (item, path)
            except Exception as e:
                self.component.logger.warning (f'could not write to {path}, exception: {e}')

    # ********************************
    # setters
    # ********************************
    def set_training_data_flag (self, training_data_flag):
        self.training_data_flag = training_data_flag

    def set_save_result_flag_test (self, save_result_flag_test):
        self.save_result_flag_test = save_result_flag_test

    def set_save_result_flag_training (self, save_result_flag_training):
        self.save_result_flag_training = save_result_flag_training

    def set_save_result_flag (self, save_result_flag):
        if self.training_data_flag:
            self.save_result_flag_training = save_result_flag
        else:
            self.save_result_flag_test = save_result_flag

    def set_overwrite (self, overwrite):
        self.overwrite = overwrite

    def set_save_fitting (self, save_fitting):
        self.save_fitting = save_fitting

    def set_path_results (self, path_results):
        self.path_results = path_results
        self.path_result_file_training, self.path_model_file, self.path_result_file_test = None, None, None
        if self.path_results is not None:
            self.path_results = Path(self.path_results).resolve()
            if self.result_file_name_training is not None:
                self.path_result_file_training = self.path_results / self.result_file_name_training
            if self.fitting_file_name is not None:
                self.path_model_file = self.path_results / self.fitting_file_name
            if self.result_file_name_test is not None:
                self.path_result_file_test = self.path_results / self.result_file_name_test

    # global saving and loading
    def set_save (self, save):
        self.save = save

    def set_load (self, load):
        self.load = load

# Cell
class PandasIO (DataIO):
    """
    Saves results in parquet format by default.

    Results are supposed to be in Pandas DataFrame format.
    """
    def __init__ (self,
                  result_file_extension='.parquet',
                  result_load_func=pd.read_parquet,
                  result_save_func=save_multi_index_parquet,
                  save_training_result=True,
                  save_test_result=True,
                  **kwargs):

        super().__init__ (result_file_extension=result_file_extension,
                          result_load_func=result_load_func,
                          result_save_func=result_save_func,
                          save_training_result=save_training_result,
                          save_test_result=save_test_result,
                          **kwargs)

# Cell
class PickleIO (DataIO):
    """
    DataIO that uses pickle format for saving / loading the estimator.

    It does not restrict the format for saving / loading the result of
    the transformation.
    """

    def __init__ (self,
                  fitting_file_extension='.pk',
                  fitting_load_func=joblib.load,
                  fitting_save_func=joblib.dump,

                  result_file_extension='.pk',
                  result_load_func=joblib.load,
                  result_save_func=joblib.dump,
                  save_training_result=True,
                  save_test_result=True,
                  **kwargs):

        super().__init__ (fitting_file_extension=fitting_file_extension,
                          fitting_load_func=fitting_load_func,
                          fitting_save_func=fitting_save_func,

                          result_file_extension=result_file_extension,
                          result_load_func=result_load_func,
                          result_save_func=result_save_func,
                          save_training_result=save_training_result,
                          save_test_result=save_test_result,
                          **kwargs)

SklearnIO = PickleIO

# Cell
class NoSaverIO (DataIO):
    """DataIO that does not load or save anything."""
    def __init__ (self,
                  fitting_load_func=None,
                  fitting_save_func=None,
                  save_fitting=False,
                  result_load_func=None,
                  result_save_func=None,
                  save_training_result=False,
                  save_test_result=False,
                  **kwargs):

        super().__init__ (fitting_load_func=fitting_load_func,
                          fitting_save_func=fitting_save_func,
                          save_fitting=save_fitting,
                          result_load_func=result_load_func,
                          result_save_func=result_save_func,
                          save_training_result=save_training_result,
                          save_test_result=save_test_result,
                          **kwargs)

# Cell
class ModelPlotter ():
    """Helper class that provides information about the component used for plotting the pipeline diagram."""
    def __init__ (self,
                  component=None,
                  # diagram options
                  diagram_node_name = None,
                  diagram_edge_name = '',
                  diagram_module_path = '',
                  **kwargs):

        self.set_component (component)

        # diagram options
        if diagram_node_name is None:
            diagram_node_name = self.component.class_name
        self.diagram_node_name = diagram_node_name
        self.diagram_edge_name = diagram_edge_name
        self.diagram_module_path = diagram_module_path
        self.training_result_shape = None
        self.test_result_shape = None

    def set_component (self, component=None):
        self.component = component

    def get_node_name (self):
        return self.diagram_node_name

    def get_edge_name (self, training_data_flag=False, load_data=True):
        result_shape = self.training_result_shape if training_data_flag else self.test_result_shape
        if result_shape is None:
            if load_data:
                self.component.data_io.set_training_data_flag (training_data_flag)
                df = self.component.data_io.load_result()
                if (df is not None) and hasattr(df, 'shape'):
                    if training_data_flag:
                        self.training_result_shape = result_shape = df.shape
                    else:
                        self.test_result_shape = result_shape = df.shape

        if result_shape is None:
            return self.diagram_edge_name
        else:
            return f'{self.diagram_edge_name} {result_shape}'

    def get_module_path (self):
        return self.diagram_module_path

# Cell
def camel_to_snake (name):
    """
    Convert CamelCase to snake_case.

    Used for converting classes names to file names where
    the corresponding computation is stored:
        https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()