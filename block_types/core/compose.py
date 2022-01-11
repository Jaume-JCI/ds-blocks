# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/core/compose.ipynb (unless otherwise specified).

__all__ = ['MultiComponent', 'Pipeline', 'make_pipeline', 'pipeline_factory', 'PandasPipeline', 'ColumnSelector',
           'Concat', 'ColumnTransformer', 'Identity', 'make_column_transformer_pipelines', 'make_column_transformer',
           'MultiSplitComponent']

# Cell
import warnings
import pandas as pd
import warnings
from sklearn.utils import Bunch

try:
    from graphviz import *
    imported_graphviz = True
except:
    imported_graphviz = False

from .block_types import (Component,
                                          PandasComponent,
                                          SamplingComponent,
                                          NoSaverComponent)
from .data_conversion import PandasConverter
from .utils import PandasIO
from ..utils.utils import get_logging_level
import block_types.config.bt_defaults as dflt

# Cell
class MultiComponent (SamplingComponent):
    """
    Component containing a list of components inside.

    The list must contain at least one component.

    See `Pipeline` class.
    """
    def __init__ (self,
                  separate_labels=False,
                  warning_if_nick_name_exists=False,
                  **kwargs):
        """Assigns attributes and calls parent constructor.

        Parameters
        ----------
        separate_labels: bool, optional
            whether or not the fit method receives the labels in a separate `y` vector
            or in the same input `X`, as an additional variable. See description of
            Pipeline class for more details.
        """
        if 'estimator' in kwargs:
            self.logger.warning ('estimator passed as key-word argument in MultiComponent')

        if not hasattr (self, 'components'):
            self.components = []
        if not hasattr (self, 'finalized_component_list'):
            self.finalized_component_list = False

        # we need to call super().__init__() *after* having creating the `components` field,
        # since the constructor of Component calls a method that is overriden in Pipeline,
        # and this method makes use of the mentioned `components` field
        super().__init__ (separate_labels = separate_labels,
                          **kwargs)

        self.set_split ('whole')


    def register_components (self, *components):
        """
        Registering component in `self.components` list.

        Every time that a new component is set as an attribute of the pipeline,
        this component is added to the list `self.components`. Same
        mechanism as the one used by pytorch's `nn.Module`
        """
        if not hasattr(self, 'components'):
            self.components = []
            self.finalized_component_list = False
        if not self.finalized_component_list:
            self.components += components

    def __setattr__(self, k, v):
        """
        See register_components
        """
        super().__setattr__(k, v)

        if isinstance(v, Component):
            self.register_components(v)
            if not hasattr(self, v.name):
                super().__setattr__(v.name, v)
            if not self.finalized_component_list:
                if hasattr(v, 'nick_name') and self.warning_if_nick_name_exists:
                    self.logger.warning (f'{v} already has a nick_name: {v.nick_name}')
                    warnings.warn (f'{v} already has a nick_name: {v.nick_name}')
                v.nick_name = k

    def add_component (self, component):
        if not hasattr(self, 'finalized_component_list'):
            self.finalized_component_list = False
        finalized_component_list = self.finalized_component_list
        self.finalized_component_list = False
        self.register_components(component)
        self.finalized_component_list = finalized_component_list

        if hasattr(component, 'nick_name') and self.warning_if_nick_name_exists:
            self.logger.warning (f'{component} already has a nick_name: {component.nick_name}')
            warnings.warn (f'{component} already has a nick_name: {component.nick_name}')
        component.nick_name = component.name
        if not hasattr(self, component.name):
            super().__setattr__ (component.name, component)

    def set_components (self, *components):
        self.components = components
        self.finalized_component_list = True
        for component in components:
            if hasattr(component, 'nick_name') and self.warning_if_nick_name_exists:
                self.logger.warning (f'{component} already has a nick_name: {component.nick_name}')
                warnings.warn (f'{component} already has a nick_name: {component.nick_name}')
            component.nick_name = component.name
            if not hasattr(self, component.name):
                super().__setattr__ (component.name, component)

    def clear_descendants (self):
        self.cls = Bunch ()
        self.obj = Bunch ()
        self.full_obj = Bunch ()
        self.full_cls = Bunch ()
        for component in self.components:
            if isinstance(component, MultiComponent):
                component.clear_descendants ()

    def gather_descendants (self, root='', nick_name=True):
        if not hasattr (self, 'cls'):
            self.cls = Bunch ()
            self.obj = Bunch ()
            self.full_obj = Bunch ()
            self.full_cls = Bunch ()

        if hasattr(self, 'nick_name'):
            name = self.nick_name if nick_name else self.name
        else:
            name = self.name
        self.hierarchy_path = f'{root}{name}'
        for component in self.components:
            self._insert_descendant (self.cls, component, component.class_name)
            self._insert_descendant (self.obj, component, component.name)

            name = component.nick_name if nick_name else component.name
            component_hierarchy_path = f'{self.hierarchy_path}.{name}'
            self._insert_descendant (self.full_cls, component_hierarchy_path, component.class_name)
            self._insert_descendant (self.full_obj, component_hierarchy_path, component.name)
            if isinstance(component, MultiComponent):
                component.gather_descendants (root=f'{self.hierarchy_path}.',
                                              nick_name=nick_name)
                for name in component.cls:
                    self._insert_descendant (self.cls, component.cls[name], name)
                    self._insert_descendant (self.full_cls, component.full_cls[name], name)
                for name in component.obj:
                    self._insert_descendant (self.obj, component.obj[name], name)
                    self._insert_descendant (self.full_obj, component.full_obj[name], name)

    def _insert_descendant (self, cmp_dict, component, name):
        if name in cmp_dict:
            if not isinstance(cmp_dict[name], list):
                cmp_dict[name] = [cmp_dict[name]]
            if isinstance(component, list):
                cmp_dict[name].extend(component)
            else:
                cmp_dict[name].append(component)
        else:
            if isinstance(component, list):
                cmp_dict[name] = component.copy()
            else:
                cmp_dict[name] = component

    def gather_times (self):
        dfs = [self.profiler.retrieve_times ()]
        for component in self.components:
            if isinstance(component, MultiComponent):
                dfs.append(component.gather_times ())
            else:
                dfs.append(component.profiler.retrieve_times (is_leaf=True))
        dfs = self.profiler.combine_times (dfs)
        return dfs

    def construct_diagram (self, split=None, include_url=False, port=4000, project='block_types'):
        """
        Construct diagram of the pipeline components, data flow and dimensionality.

        By default, we use test data to show the number of observations
        in the output of each component. This can be changed passing
        `split='train'`
        """
        split = self.get_split (split)

        if include_url:
            base_url = f'http://localhost:{port}/{project}'
        else:
            URL = ''

        node_name = 'data'
        output = 'train / test'

        f = Digraph('G', filename='fsm2.svg')
        f.attr('node', shape='circle')

        f.node(node_name)

        f.attr('node', shape='box')
        for component in self.components:
            last_node_name = node_name
            last_output = output
            node_name = component.model_plotter.get_node_name()
            if include_url:
                URL = f'{base_url}/{component.model_plotter.get_module_path()}.html#{node_name}'
            f.node(node_name, URL=URL)
            f.edge(last_node_name, node_name, label=last_output)
            output = component.model_plotter.get_edge_name(split=split)

        last_node_name = node_name
        node_name = 'output'
        f.attr('node', shape='circle')
        f.edge(last_node_name, node_name, label=output)

        return f

    def show_result_statistics (self, split=None):
        """
        Show statistics about results obtained by each component.

        By default, this is shown on test data, although this can change setting
        `split='train'`
        """
        split = self.get_split (split)

        for component in self.components:
            component.show_result_statistics(split=split)

    def show_summary (self, split=None):
        """
        Show list of pipeline components, data flow and dimensionality.

        By default, we use test data to show the number of observations
        in the output of each component. This can be changed passing
        `split='train'`
        """
        split = self.get_split (split)

        node_name = 'data'
        output = 'train / test'

        for i, component in enumerate(self.components):
            node_name = component.model_plotter.get_node_name()
            output = component.model_plotter.get_edge_name(split=split)
            print (f'{"-"*100}')
            print (f'{i}: {node_name} => {output}')


    def get_split (self, split=None):
        if split is None:
            if self.data_io.split is not None:
                split = self.data_io.split
            else:
                split = 'whole'

        return split

    def assert_all_equal (self, path_reference_results, raise_error=False, recursive=True,
                          max_recursion=None, current_recursion=0, verbose=None, **kwargs):
        """Compare results stored in current run against reference results stored in given path."""
        if verbose is not None:
            self.logger.setLevel(get_logging_level (verbose))
        is_equal = True
        non_equal_components = []
        end_recursion = max_recursion is not None and current_recursion > max_recursion
        if end_recursion:
            self.logger.setLevel(get_logging_level (self.verbose))
            return True
        for component in self.components:
            if isinstance(component, MultiComponent) and recursive and not end_recursion:
                this_equal = component.assert_all_equal (path_reference_results,
                                                         raise_error=raise_error,
                                                         recursive=recursive,
                                                         max_recursion=max_recursion,
                                                         current_recursion=current_recursion+1,
                                                         verbose=verbose,
                                                         **kwargs)
            else:
                this_equal = component.assert_equal (path_reference_results,
                                                     raise_error=raise_error,
                                                     verbose=verbose,
                                                     **kwargs)
            if not this_equal:
                non_equal_components.append(component.name)
            is_equal = this_equal and is_equal

        if not is_equal:
            self.logger.warning (f'Results are different in components {non_equal_components}')
        else:
            self.logger.info ('both pipelines give the same results')

        self.logger.setLevel(get_logging_level (self.verbose))

        return is_equal

    def load_estimator (self):
        for component in self.components:
            component.load_estimator ()

    # *************************
    # setters
    # *************************
    def set_split (self, split):
        super().set_split (split)
        for component in self.components:
            component.set_split (split)

    def set_save_splits (self, save_splits):
        super().set_save_splits (save_splits)
        for component in self.components:
            component.set_save_splits (save_splits)

    def set_load_model (self, load_model):
        super().set_load_model (load_model)
        for component in self.components:
            component.set_load_model (load_model)

    def set_save_model (self, save_model):
        super().set_save_model (save_model)
        for component in self.components:
            component.set_save_model (save_model)

    def set_save_result (self, save_result):
        super().set_save_result (save_result)
        for component in self.components:
            component.set_save_result (save_result)

    def set_load_result (self, load_result):
        super().set_load_result (load_result)
        for component in self.components:
            component.set_load_result (load_result)

# Cell
class Pipeline (MultiComponent):
    """
    Pipeline composed of a list of components that run sequentially.

    During training, the components of the list are trained one after the other,
    where one component is fed the result of transforming the data with the list
    of components located before in the pipeline.

    The `Pipeline` class is a subclass of `SamplingComponent`, which itself is a
    subclass of `Component`. This provides the functionality of `Component`
    to any implemented pipeline, such as logging the messages, loading / saving the
    results, and convert the data format so that it can work as part of other
    pipelines with potentially other data formats.

    Being a subclass of `SamplingComponent`, the `transform` method
    receives an input data  `X` that contains both data and labels.

    Furthermore, the Pipeline constructor sets `separate_labels=False` by default,
    which means that the `fit` method also receives an input data `X` that contains
    not only data but also labels. This is necessary because some of the components in
    the pipeline might be of class `SamplingComponent`, and such components
    need the input data `X` to contain labels when calling `transform` (and note that
    this method is called when calling `fit` on a pipeline, since we do `fit_transform`
    on all the components except for the last one)
    """
    def __init__ (self, **kwargs):
        """Assigns attributes and calls parent constructor.

        Parameters
        ----------
        separate_labels: bool, optional
            whether or not the fit method receives the labels in a separate `y` vector
            or in the same input `X`, as an additional variable. See description of
            Pipeline class for more details.
        """

        super().__init__ (**kwargs)

    def _fit (self, X, y=None):
        """
        Fit components of the pipeline, given data X and labels y.

        By default, y will be None, and the labels are part of `X`, as a variable.
        """
        X = self._fit_apply_except_last (X, y)
        self.components[-1].fit (X, y)

    def _fit_apply (self, X, y=None, **kwargs):
        X = self._fit_apply_except_last (X, y, **kwargs)
        return self.components[-1].fit_apply (X, y, **kwargs)

    def _fit_apply_except_last (self, X, y, **kwargs):
        for component in self.components[:-1]:
            X = component.fit_apply (X, y, **kwargs)
        return X

    def _apply (self, X):
        """Transform data with components of pipeline, and predict labels with last component.

        In the current implementation, we consider prediction a form of mapping,
        and therefore a special type of transformation."""
        for component in self.components:
            X = component.transform (X)

        return X

# Cell
def make_pipeline(*components, cls=Pipeline, **kwargs):
    """Create `Pipeline` object of class `cls`, given `components` list."""
    pipeline = cls (**kwargs)
    pipeline.set_components(*components)
    return pipeline

# Cell
def pipeline_factory (pipeline_class, **kwargs):
    """Creates a pipeline object given its class `pipeline_class`

    Parameters
    ----------
    pipeline_class : class or str
        Name of the pipeline class used for creating the object.
        This can be either of type string or class.
    """
    if type(pipeline_class) is str:
        Pipeline = eval(pipeline_class)
    elif type(pipeline_class) is type:
        Pipeline = pipeline_class
    else:
        raise ValueError (f'pipeline_class needs to be either string or class, we got {pipeline_class}')

    return Pipeline (**kwargs)

# Cell
class PandasPipeline (Pipeline):
    """
    Pipeline that saves results in parquet format, and preserves DataFrame format.

    See `Pipeline` class for an explanation of using `separate_labels=False`
    """
    def __init__ (self,
                  data_converter=None,
                  data_io=None,
                  separate_labels=False,
                  **kwargs):
        if data_converter is None:
            data_converter = PandasConverter (separate_labels=separate_labels,
                                              **kwargs)
        if data_io is None:
            data_io = PandasIO (**kwargs)
        super().__init__ (self,
                          data_converter=data_converter,
                          data_io=data_io,
                          **kwargs)

# Cell
class ColumnSelector (NoSaverComponent):
    def __init__ (self,
                  columns=[],
                  remainder=False,
                  verbose=dflt.verbose,
                  force_verbose=False,
                  logger=None,
                  **kwargs):
        verbose = 0 if not force_verbose else verbose
        if verbose==0:
            logger=None
        super().__init__ (verbose=verbose,
                          logger=logger,
                          **kwargs)

    def _apply (self, df):
        if self.remainder:
            return df[[c for c in df.columns if c not in self.columns]]
        else:
            return df[self.columns]

# Cell
class Concat (NoSaverComponent):
    def __init__ (self,
                  verbose=dflt.verbose,
                  force_verbose=False,
                  logger=None,
                  **kwargs):
        verbose = 0 if not force_verbose else verbose
        if verbose==0:
            logger=None
        super().__init__ (verbose=verbose,
                          logger=logger,
                          **kwargs)

    def _apply (self, *dfs):
        return pd.concat(list(dfs), axis=1)

# Cell
class _BaseColumnTransformer (MultiComponent):
    def __init__ (self, name=None, class_name=None, **kwargs):
        super().__init__ (name=name, class_name=class_name, **kwargs)
        self.concat = Concat (**kwargs)
        del self.concat.nick_name

    def set_components (self, *components):
        components = list(components)
        components.append (self.concat)
        super().set_components (*components)

    def _fit (self, df, y=None):
        assert len(self.components) > 0
        assert self.components[-1] is self.concat
        for component in self.components[:-1]:
            component.fit (df)
        return self

    def _apply (self, df):
        dfs = []
        assert len(self.components) > 0
        assert self.components[-1] is self.concat
        for component in self.components[:-1]:
            dfs.append (component.transform (df))
        df_result = self.concat.transform (*dfs)
        return df_result

class ColumnTransformer (_BaseColumnTransformer):
    def __init__ (self, *transformers, remainder = 'drop', **kwargs):
        super().__init__ (**kwargs)
        components = make_column_transformer_pipelines (*transformers, remainder=remainder, **kwargs)
        super().set_components(*components)

# Cell
class Identity (NoSaverComponent):
    def __init__ (self,
                  verbose=dflt.verbose,
                  force_verbose=False,
                  logger=None,
                  **kwargs):
        verbose = 0 if not force_verbose else verbose
        if verbose==0:
            logger=None
        super().__init__ (verbose=verbose,
                          logger=logger,
                          **kwargs)

    def _apply (self, X):
        return X

# Cell
def _append_pipeline (pipelines, name, transformer, columns, remainder= False, **kwargs):
    drop = False
    if isinstance(transformer, str):
        if transformer == 'passthrough':
            transformer = Identity (**kwargs)
        elif transformer == 'drop':
            drop = True
        else:
            raise ValueError (f'name {transformer} not recognized')

    if not drop:
        config=kwargs.copy()
        config.update({name:dict(data_io='NoSaverIO')})
        pipeline = make_pipeline(ColumnSelector(columns, remainder=remainder, **kwargs),
                                 transformer,
                                 name=name,
                                 **config)
        pipelines.append (pipeline)

def _get_transformer_name (transformer, columns):
    columns_name = ''.join([x[0] for x in columns])
    if len(columns_name) > 5:
        columns_name = columns_name[:5]
    if isinstance(transformer,str):
        if transformer == 'passthrough':
            transformer_name = 'pass'
        elif transformer == 'drop':
            transformer_name = 'drop'
        else:
            raise ValueError (f'name {transformer} not recognized')
    elif hasattr(transformer, 'name'):
        transformer_name = transformer.name
    else:
        transformer_name = transformer.__class__.__name__
    name = f'{transformer_name}_{columns_name}'
    return name

def make_column_transformer_pipelines (*transformers, remainder='drop', **kwargs):
    pipelines = []
    all_columns = []
    for name, transformer, columns in transformers:
        _append_pipeline (pipelines, name, transformer, columns, **kwargs)
        all_columns.extend(columns)

    all_columns = list(set(all_columns))
    name = _get_transformer_name (remainder, ['r','e','m'])
    _append_pipeline (pipelines, name, remainder, all_columns, remainder=True, **kwargs)

    return pipelines

def make_column_transformer (*transformers, remainder='drop', name=None, class_name=None, **kwargs):
    transformers_with_name = []
    for transformer, columns in transformers:
        transformer_name = _get_transformer_name (transformer, columns)
        transformers_with_name.append ((transformer_name, transformer, columns))

    pipelines = make_column_transformer_pipelines (*transformers_with_name,
                                                   remainder=remainder,
                                                   **kwargs)
    column_transformer = _BaseColumnTransformer (name=name, class_name=class_name, **kwargs)
    column_transformer.set_components(*pipelines)
    return column_transformer


# Cell
class MultiSplitComponent (MultiComponent):
    def __init__ (self,
                  component=None,
                  name=None,
                  class_name=None,
                  fit_to = 'training',
                  fit_additional = [],
                  apply_to = ['training', 'validation', 'test'],
                  raise_error_if_split_doesnot_exist=False,
                  raise_warning_if_split_doesnot_exist=True,
                  **kwargs):
        if class_name is None:
            if hasattr(component, 'class_name'):
                class_name = f'{component.class_name}MultiSplit'
            else:
                class_name = f'{component.__class__.__name__}MultiSplit'

        if name is None:
            if hasattr(component, 'name'):
                name = f'{component.name}_multi_split'
            else:
                name = f'{component.__class__.__name__}_multi_split'

        super().__init__ (name=name, class_name=class_name, **kwargs)

    def _fit (self, X, y=None):
        if not isinstance(X, dict):
            X = {self.fit_to: X}
        component = self.components[0]
        additional_data = {}
        for split in self.fit_additional:
            if split not in ['validation', 'test']:
                raise ValueError (f'split {split} not valid')
            if split in X.keys():
                additional_data[f'{split}_data'] = X[split]
            else:
                self._issue_error_or_warning (split, X)

        component.fit(X[self.fit_to], y=y, split='training', **additional_data)

    def _issue_error_or_warning (self, split, X):
        message = f'split {split} not found in X keys ({X.keys()})'
        if self.raise_error_if_split_doesnot_exist:
            raise RuntimeError (message)
        elif self.raise_warning_if_split_doesnot_exist:
            warnings.warn (message)

    def _apply (self, X, apply_to = None, output_not_dict=False, split=None, **kwargs):
        apply_to = self.apply_to if apply_to is None else apply_to
        apply_to = apply_to if isinstance(apply_to, list) else [apply_to]
        if not isinstance(X, dict):
            key = apply_to[0] if len(apply_to)==1 else split if split is not None else 'test'
            X = {key: X}
            input_not_dict = True
        else:
            input_not_dict = False

        component = self.components[0]
        result = {}
        for split in apply_to:
            if split in X.keys():
                result[split] = component.apply (X[split], split=split, **kwargs)
            else:
                self._issue_error_or_warning (split, X)

        if input_not_dict:
            result = result[key]
        elif output_not_dict and len(result)==1:
            result = list(result.items())[0][1]
        return result
