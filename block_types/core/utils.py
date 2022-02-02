# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/core/utils.ipynb (unless otherwise specified).

__all__ = ['save_csv', 'save_parquet', 'save_multi_index_parquet', 'save_keras_model', 'save_csv_gz', 'read_csv',
           'read_csv_gz', 'load_keras_model', 'estimator2io', 'result2io', 'DataIO', 'PandasIO', 'PickleIO',
           'SklearnIO', 'NoSaverIO', 'data_io_factory', 'ModelPlotter', 'Profiler', 'Comparator', 'camel_to_snake']

# Cell
from pathlib import Path
import re
from functools import partialmethod
import time
import pickle
from IPython.display import display
from sklearn.base import BaseEstimator, ClassifierMixin, TransformerMixin
from sklearn.utils import Bunch
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pyarrow as pa
import joblib
import copy

try:
    from graphviz import *
    imported_graphviz = True
except:
    imported_graphviz = False

# block_types
from .data_conversion import PandasConverter
from ..config import bt_defaults as dflt
from ..utils.utils import set_logger, get_logging_level

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
estimator2io = dict(
    keras=dict(fitting_load_func=load_keras_model,
               fitting_save_func=save_keras_model,
               fitting_file_extension=''),
    pickle=dict(fitting_load_func=joblib.load,
                 fitting_save_func=joblib.dump,
                 fitting_file_extension='.pk'),
    default=dict(fitting_load_func=joblib.load,
                 fitting_save_func=joblib.dump,
                 fitting_file_extension='.pk'))

result2io = dict(
    pandas=dict(result_load_func=pd.read_parquet,
                result_save_func=save_multi_index_parquet,
                result_file_extension='.parquet'),
    pickle=dict(result_load_func=joblib.load,
                 result_save_func=joblib.dump,
                 result_file_extension='.pk'),
    default=dict(result_load_func=joblib.load,
                 result_save_func=joblib.dump,
                 result_file_extension='.pk')
)

# Cell
class DataIO ():
    def __init__ (self,
                  component=None,
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
        result_file_name : str or None, optional
            Name of the file used for storing the transformed data.
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
        save_splits : dict, optional
            Dictionary mapping split names to booleans. Usual split names are 'test', 'validation', 'training'
            For each split name, if True the transformed data is saved for that split.
        save : bool, optional
            If False, neither transformed data nor estimated parameters are saved,
            regardless of the other arguments.
        load: bool, optional
            If False, neither transformed data nor estimated parameters are loaded,
            regardless of the other arguments.
        """

        self.component = component
        if component is not None:
            config = self.component.obtain_config_params (**kwargs)
            self._init (**config)
            self.setup (component)
        else:
            self._init (**kwargs)
            self._initial_kwargs = kwargs

    def _init (self,
               path_models=None,
               fitting_file_name=None,
               fitting_file_extension=None,
               fitting_load_func=None,
               fitting_save_func=None,
               estimator_io='pickle',
               load_model=True,
               save_model=True,

               path_results=dflt.path_results,
               result_file_extension=None,
               result_file_name=None,
               result_load_func=None,
               result_save_func=None,
               result_io='pickle',
               save_splits=dflt.save_splits,
               load_result=True,
               save_result=True,

               load=True,
               save=True,
               split='whole',
               **kwargs):

        self.path_models = path_models
        self.path_results = path_results

        # saving / loading estimator parameters
        self.fitting_file_name = fitting_file_name
        self.fitting_file_extension = fitting_file_extension
        self.fitting_load_func = fitting_load_func
        self.fitting_save_func = fitting_save_func
        self.estimator_io = estimator_io

        # saving / loading transformed data
        self.result_file_extension = result_file_extension
        self.result_load_func = result_load_func
        self.result_save_func = result_save_func
        self.result_io = result_io

        # saving / loading transformed training data
        self.set_save_splits (save_splits)

        # saving / loading transformed test data
        self.result_file_name = result_file_name

        # whether the transformation has been applied to training data (i.e., to be saved in training path)
        # or to test data (i.e,. to be saved in test path)
        self.split = split

        # global saving and loading
        self.set_save (save)
        self.set_load (load)
        self.set_save_model (save_model)
        self.set_load_model (load_model)
        self.set_save_result (save_result)
        self.set_load_result (load_result)

        self.path_model_file = None

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

        if hasattr(self, '_initial_kwargs'):
            config = self.component.obtain_config_params (**self._initial_kwargs)
            self._init (**config)
            del self._initial_kwargs

        if self.fitting_file_extension is None:
            self.fitting_file_extension = estimator2io[self.estimator_io]['fitting_file_extension']
        if self.fitting_load_func is None:
            self.fitting_load_func = estimator2io[self.estimator_io]['fitting_load_func']
        if self.fitting_save_func is None:
            self.fitting_save_func = estimator2io[self.estimator_io]['fitting_save_func']

        if self.result_file_extension is None:
            self.result_file_extension = result2io[self.result_io]['result_file_extension']
        if self.result_load_func is None:
            self.result_load_func = result2io[self.result_io]['result_load_func']
        if self.result_save_func is None:
            self.result_save_func = result2io[self.result_io]['result_save_func']

        # configuration for saving / loading fitted estimator
        if self.fitting_file_name is None:
            self.fitting_file_name = f'{self.component.name}_estimator{self.fitting_file_extension}'

        # configuration for saving / loading result of transforming training data
        if self.result_file_name is None:
            self.result_file_name = f'{self.component.name}_result{self.result_file_extension}'

        if self.path_results is not None:
            self.path_results = Path(self.path_results).resolve()

        if self.path_models is None:
            self.path_models = self.path_results
        else:
            self.path_models = Path(self.path_models).resolve()

        if self.path_models is not None:
            self.path_model_file = self.path_models / 'models' / self.fitting_file_name
        else:
            self.path_model_file = None

    def load_estimator (self):
        """Load estimator parameters."""
        estimator = self._load (path=self.path_model_file,
                                load_func=self.fitting_load_func)
        return estimator

    def save_estimator (self):
        """Save estimator parameters."""
        if self.component.estimator is not None:
            self._save (self.path_model_file, self.fitting_save_func, self.component.estimator)

    def load_result (self, split=None, path_results=None, result_file_name=None):
        """
        Load transformed data.

        Transformed training data is loaded if self.training_data_flag=True,
        otherwise transformed test data is loaded.
        """
        split = self.split if split is None else split
        path_results = self.path_results if path_results is None else Path(path_results).resolve()
        result_file_name = self.result_file_name if result_file_name is None else result_file_name
        if path_results is not None:
            path_result_file = path_results / split / result_file_name
        else:
            path_result_file = None
        return self._load (path_result_file, self.result_load_func)

    def save_result (self, result, split=None, path_results=None, result_file_name=None):
        """
        Save transformed data.

        Transformed training data is saved if self.training_data_flag=True,
        otherwise transformed test data is saved.
        """
        split = self.split if split is None else split
        path_results = self.path_results if path_results is None else Path(path_results).resolve()
        result_file_name = self.result_file_name if result_file_name is None else result_file_name
        if path_results is not None:
            path_result_file = path_results / split / result_file_name
        else:
            path_result_file = None
        self._save (path_result_file, self.result_save_func,
                    result)

    def can_load_model (self, load=None):
        return load if load is not None else (self.load_flag and self.load_model_flag)

    def can_load_result (self, load=None):
        return load if load is not None else (self.load_flag and self.load_result_flag)

    def can_save_model (self, save=None):
        return save if save is not None else (self.save_flag and self.save_model_flag)

    def can_save_result (self, save=None, split=None):
        split = self.split if split is None else split
        return save if save is not None else (self.save_flag and
                                              self.save_result_flag and
                                              self.save_splits.get(split, True))

    def _load (self, path, load_func):
        if (path is not None) and path.exists():
            self.component.logger.info (f'loading from {path}')
            return load_func (path)
        else:
            return None

    def _save (self, path, save_func, item):
        if (path is not None) and (save_func is not None):
            self.component.logger.info (f'saving to {path}')
            # create parent directory if it does not exist
            path.parent.mkdir(parents=True, exist_ok=True)
            # save data using save_func
            try:
                save_func (item, path)
            except Exception as e:
                self.component.logger.warning (f'could not write to {path}, exception: {e}')

    # ********************************
    # setters
    # ********************************
    def set_split (self, split):
        self.split = split

    def set_save_splits (self, save_splits):
        self.save_splits = save_splits

    def set_path_results (self, path_results):
        self.path_results = path_results
        if self.path_results is not None:
            self.path_results = Path(self.path_results).resolve()
            if self.path_models is None:
                self.set_path_models (path_results)
        self.component.path_results = self.path_results
        self.component.path_models = self.path_models

    def set_path_models (self, path_models):
        self.path_models = path_models
        if self.path_models is not None:
            self.path_models = Path(self.path_models).resolve()
        else:
            self.path_models = path_results
        if self.path_models is not None and self.fitting_file_name is not None:
            self.path_model_file = self.path_models / 'models' / self.fitting_file_name
        else:
            self.path_model_file = None
        self.component.path_results = self.path_results
        self.component.path_models = self.path_models


    # global saving and loading
    def set_save (self, save):
        self.save_flag = save
        if not save:
            self.set_save_model (False)
            self.set_save_result (False)

    def set_load (self, load):
        self.load_flag = load
        if not load:
            self.set_load_model (False)
            self.set_load_result (False)

    def set_save_model (self, save):
        self.save_model_flag = save if self.save_flag else False

    def set_load_model (self, load):
        self.load_model_flag = load if self.load_flag else False

    def set_save_result (self, save):
        self.save_result_flag = save if self.save_flag else False

    def set_load_result (self, load):
        self.load_result_flag = load if self.load_flag else False

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
                  **kwargs):

        super().__init__ (result_file_extension=result_file_extension,
                          result_load_func=result_load_func,
                          result_save_func=result_save_func,
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
                  **kwargs):

        super().__init__ (fitting_file_extension=fitting_file_extension,
                          fitting_load_func=fitting_load_func,
                          fitting_save_func=fitting_save_func,

                          result_file_extension=result_file_extension,
                          result_load_func=result_load_func,
                          result_save_func=result_save_func,
                          **kwargs)

SklearnIO = PickleIO

# Cell
class NoSaverIO (DataIO):
    """DataIO that does not load or save anything."""
    def __init__ (self,
                  load=False,
                  save=False,
                  force_load=False,
                  force_save=False,
                  **kwargs):
        super().__init__ (load=force_load if force_load else False,
                          save=force_save if force_save else False,
                          **kwargs)

# Cell
def data_io_factory (data_io, component=None, **kwargs):
    if type(data_io) is str:
        cls = eval(data_io)
    elif type(data_io) is type:
        cls = data_io
    elif isinstance (data_io, DataIO):
        data_io = copy.copy(data_io)
        data_io.setup (component=component)
        return data_io
    else:
        raise ValueError (f'invalid converter {data_io}, must be str, '
                           'class or object instance of DataIO')
    data_io = cls(component=component, **kwargs)
    return data_io

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
        self.result_shape = {}

    def set_component (self, component=None):
        self.component = component

    def get_node_name (self):
        return self.diagram_node_name

    def get_edge_name (self, split=None, load_data=True):
        split = self.component.data_io.split if split is None else split
        result_shape = self.result_shape[split] if split in self.result_shape else None
        if result_shape is None:
            if load_data:
                df = self.component.data_io.load_result(split=split)
                if (df is not None) and hasattr(df, 'shape'):
                    result_shape = self.result_shape[split] = df.shape

        if result_shape is None:
            return self.diagram_edge_name
        else:
            return f'{self.diagram_edge_name} {result_shape}'

    def get_module_path (self):
        return self.diagram_module_path

# Cell
class Profiler ():
    def __init__ (self, component, do_profiling=True, **kwargs):
        self.component = component
        self.name = component.name
        if hasattr(component, 'hierarchy_level'):
            self.hierarchy_level = component.hierarchy_level
        else:
            self.hierarchy_level = 0
        self.do_profiling=do_profiling
        self.times = Bunch(sum=pd.DataFrame (),
                          max=pd.DataFrame (),
                          min=pd.DataFrame (),
                          number=pd.DataFrame ())
        keys = list(self.times.keys()).copy()
        for k in keys:
            self.times[f'novh_{k}']=pd.DataFrame ()

    def start_timer (self):
        self.time = time.time()

    def start_no_overhead_timer (self):
        self.no_overhead_time = time.time()

    def finish_timer (self, method, split):
        self._finish_timer (method, split, suffix='', measured_time=self.time)

    def finish_no_overhead_timer (self, method, split):
        self._finish_timer (method, split, suffix='novh_', measured_time=self.no_overhead_time)

    def _finish_timer (self, method, split, suffix='', measured_time=None):
        if method.startswith('_'):
            method = method[1:]
        total_time = time.time() - measured_time
        df=self.times[f'{suffix}sum']
        if method in df.index and split in df.columns:
            df.loc[method, split] += total_time
            self.times[f'{suffix}number'].loc[method, split] += 1
            self.times[f'{suffix}max'].loc[method, split] = max(self.times[f'{suffix}max'].loc[method, split], total_time)
            self.times[f'{suffix}min'].loc[method, split] = min(self.times[f'{suffix}min'].loc[method, split], total_time)
        else:
            df.loc[method, split] = total_time
            self.times[f'{suffix}number'].loc[method, split] = 1
            self.times[f'{suffix}max'].loc[method, split] = total_time
            self.times[f'{suffix}min'].loc[method, split] = total_time

    def _compute_avg (self, df_sum, df_number):
        df_avg = df_sum.copy()
        columns = [c for c in df_avg.columns if c != ('leaf', '')]
        df_avg[columns] = df_avg[columns] / df_number[columns]
        return df_avg

    def retrieve_times (self, is_leaf=False):
        retrieved_times = Bunch()
        for k in self.times:
            df = self.times[k]
            columns = pd.MultiIndex.from_product([list(df.columns),list(df.index)])
            index = pd.MultiIndex.from_product([[self.hierarchy_level], [self.name]])
            df = pd.DataFrame (index=index,
                               columns = columns, data=df.values.reshape(1,-1))
            df['leaf']=is_leaf
            retrieved_times[k] = df

        retrieved_times['avg']= self._compute_avg (retrieved_times['sum'],
                                                   retrieved_times['number'])
        retrieved_times['novh_avg']= self._compute_avg (retrieved_times['novh_sum'],
                                                        retrieved_times['novh_number'])
        return retrieved_times

    def combine_times (self, df_list):
        df_dict = Bunch()
        for k in df_list[0].keys():
            df_dict[k] = pd.concat([x[k] for x in df_list])
            df_dict[k] = df_dict[k].sort_index()
        df_novh_avg = df_dict['novh_avg']
        df_dict['no_overhead_total'] = df_novh_avg[df_novh_avg.leaf].sum(axis=0)

        df_avg = self.retrieve_times ()['avg']
        df_dict['overhead_total'] = df_avg -  df_dict['no_overhead_total']
        df_dict['no_overhead_total'] = df_dict['no_overhead_total'].to_frame().T
        return df_dict

# Cell
class Comparator ():
    def __init__ (self, component=None, data_io=None, name='comparator', **kwargs):
        if component is not None:
            self.component = component
            self.logger = component.logger
            self.name = component.name
            self.data_io = component.data_io
        else:
            self.component = None
            self.logger = set_logger ('comparator', filename=None)
            self.name = name
            if data_io is not None:
                self.data_io = data_io_factory (data_io)

    def compare_objects (self, left, right, message='', **kwargs):
        if left != right:
            return message + f'{left}!={right}'
        else:
            return ''

    def compare (self, left, right, message='', rtol=1e-07, atol=0, **kwargs):
        if not type(left)==type(right):
            return f'{message}{type(left)}!={type(right)}'
        if isinstance(left, tuple) or isinstance(left, list):
            try:
                left = np.array(left, dtype=float)
                right = np.array(right, dtype=float)
            except:
                for i, (x, y) in enumerate(zip(left, right)):
                    result = self.compare (x, y, message + f'[{i}] ', rtol=rtol, atol=atol, **kwargs)
                    if len(result) > 0:
                        return result
                return ''
        elif isinstance (left, dict):
            if sorted(left.keys()) != sorted(right.keys()):
                return f'{message}{sorted(left.keys())}!={sorted(right.keys())}'
            for k in left:
                result = self.compare (left[k], right[k], message + f'[{k}] ', rtol=rtol, atol=atol,
                                       **kwargs)
                if len(result) > 0:
                    return result
            return ''

        if isinstance (left, np.ndarray):
            try:
                np.testing.assert_allclose (left, right, rtol=rtol, atol=atol)
                return ''
            except AssertionError as e:
                return message + str(e)
        elif isinstance (left, pd.DataFrame):
            try:
                pd.testing.assert_frame_equal (left, right)
                return ''
            except AssertionError as e:
                return message + str(e)
        elif isinstance (left, str):
            if left != right:
                return message + f'{left}!={right}'
            else:
                return ''
        elif np.isscalar (left) and np.isreal (left):
            if np.isclose (left, right, rtol=rtol, atol=atol):
                return ''
            else:
                return message + f'{left} not close to {right}'
        else:
            return self.compare_objects (left, right, message=message, rtol=1e-07, atol=0, **kwargs)
        return ''

    def assert_equal (self, item1, item2=None, split=None, raise_error=True, verbose=None,
                      **kwargs):
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
        if verbose is not None:
            self.logger.setLevel(get_logging_level (verbose))
        self.logger.info (f'comparing results for {self.name}')
        if item2 is None:
            item2 = item1
            self.logger.info (f'loading our results...')
            item1 = self.data_io.load_result (split=split)
        elif type(item1) is str:
            self.logger.info (f'loading others results...')
            item1 = self.data_io.load_result (split=split, path_results=item1)
        if type(item2) is str:
            item2 = self.data_io.load_result (split=split, path_results=item2)
        difference = self.compare (item1, item2, **kwargs)
        if len(difference) == 0:
            self.logger.info (f'Results are equal.\n')
            if not raise_error:
                if verbose is not None:
                    self.logger.setLevel(get_logging_level (self.component.verbose))
                return True
        else:
            if raise_error:
                raise AssertionError (f'Component {self.name} => results are different: {difference}')
            else:
                self.logger.warning (f'Component {self.name} => results are different: {difference}')
                if verbose is not None:
                    self.logger.setLevel(get_logging_level (self.component.verbose))
                return False

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