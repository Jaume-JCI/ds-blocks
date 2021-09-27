# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/core.compose.ipynb (unless otherwise specified).

__all__ = ['Pipeline', 'make_pipeline', 'pipeline_factory', 'PandasPipeline', 'ColumnSelector', 'Concat',
           'ColumnTransformer', 'Identity', 'make_column_transformer_pipelines', 'make_column_transformer']

# Cell
import pandas as pd

from .block_types import Component, PandasComponent, SamplingComponent
from .data_conversion import PandasConverter
from .utils import PandasIO

# Cell
class Pipeline (SamplingComponent):
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
    def __init__ (self, separate_labels = False, **kwargs):
        """Assigns attributes and calls parent constructor.

        Parameters
        ----------
        separate_labels: bool, optional
            whether or not the fit method receives the labels in a separate `y` vector
            or in the same input `X`, as an additional variable. See description of
            Pipeline class for more details.
        """
        if not hasattr (self, 'components'):
            self.components = []
        if not hasattr (self, 'finalized_component_list'):
            self.finalized_component_list = False

        # we need to call super().__init__() *after* having creating the `components` field,
        # since the constructor of Component calls a method that is overriden in Pipeline,
        # and this method makes use of the mentioned `components` field
        super().__init__ (separate_labels = separate_labels,
                          **kwargs)

        self.set_training_data_flag(False)


    def register_components (self, *ms):
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
            self.components += ms

    def __setattr__(self, k, v):
        """
        See register_components
        """
        super().__setattr__(k, v)

        if isinstance(v, Component):
            self.register_components(v)

    def add_component (self, component):
        if not hasattr(self, 'finalized_component_list'):
            self.finalized_component_list = False
        finalized_component_list = self.finalized_component_list
        self.finalized_component_list = False
        self.register_components(component)
        self.finalized_component_list = finalized_component_list

    def set_components (self, *components):
        self.components = components
        self.finalized_component_list = True

    def _fit (self, X, y=None):
        """
        Fit components of the pipeline, given data X and labels y.

        By default, y will be None, and the labels are part of `X`, as a variable.
        """
        self._fit_transform_except_last (X, y)
        self.components[-1].fit (X, y)

    def _fit_transform (self, X, y=None, **kwargs):
        self._fit_transform_except_last (X, y, **kwargs)
        return self.components[-1].fit_transform (X, y, **kwargs)

    def _fit_transform_except_last (self, X, y, **kwargs):
        self.set_training_data_flag (True)
        for component in self.components[:-1]:
            X = component.fit_transform (X, y, **kwargs)

    def _transform (self, X):
        """Transform data with components of pipeline, and predict labels with last component.

        In the current implementation, we consider prediction a form of mapping,
        and therefore a special type of transformation."""
        self.set_training_data_flag (False)
        for component in self.components:
            X = component.transform (X)

        return X

    def construct_diagram (self, training_data_flag=None, include_url=False, port=4000, project='block_types'):
        """
        Construct diagram of the pipeline components, data flow and dimensionality.

        By default, we use test data to show the number of observations
        in the output of each component. This can be changed passing
        `training_data_flag=True`
        """
        training_data_flag = self.get_training_data_flag (training_data_flag)

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
            output = component.model_plotter.get_edge_name(training_data_flag=training_data_flag)

        last_node_name = node_name
        node_name = 'output'
        f.attr('node', shape='circle')
        f.edge(last_node_name, node_name, label=output)

        return f

    def show_result_statistics (self, training_data_flag=None):
        """
        Show statistics about results obtained by each component.

        By default, this is shown on test data, although this can change setting
        `training_data_flag=True`
        """
        training_data_flag = self.get_training_data_flag (training_data_flag)

        for component in self.components:
            component.show_result_statistics(training_data_flag=training_data_flag)

    def show_summary (self, training_data_flag=None):
        """
        Show list of pipeline components, data flow and dimensionality.

        By default, we use test data to show the number of observations
        in the output of each component. This can be changed passing
        `training_data_flag=True`
        """
        training_data_flag = self.get_training_data_flag (training_data_flag)

        node_name = 'data'
        output = 'train / test'

        for i, component in enumerate(self.components):
            node_name = component.model_plotter.get_node_name()
            output = component.model_plotter.get_edge_name(training_data_flag=training_data_flag)
            print (f'{"-"*100}')
            print (f'{i}: {node_name} => {output}')


    def get_training_data_flag (self, training_data_flag=None):
        if training_data_flag is None:
            if self.data_io.training_data_flag is not None:
                training_data_flag = self.data_io.training_data_flag
            else:
                training_data_flag = False

        return training_data_flag

    def assert_equal (self, path_reference_results, assert_equal_func=pd.testing.assert_frame_equal, **kwargs):
        """Compare results stored in current run against reference results stored in given path."""

        for component in self.components:
            component.assert_equal (path_reference_results, assert_equal_func=assert_equal_func, **kwargs)
        self.logger.info ('both pipelines give the same results')
        print ('both pipelines give the same results')

    def load_estimator (self):
        for component in self.components:
            component.load_estimator ()

    # *************************
    # setters
    # *************************
    def set_training_data_flag (self, training_data_flag):
        super().set_training_data_flag (training_data_flag)
        for component in self.components:
            component.set_training_data_flag (training_data_flag)

    def set_save_result_flag_test (self, save_result_flag_test):
        super().set_save_result_flag_test (save_result_flag_test)
        for component in self.components:
            component.set_save_result_flag_test (save_result_flag_test)

    def set_save_result_flag_training (self, save_result_flag_training):
        super().set_save_result_flag_training (save_result_flag_training)
        for component in self.components:
            component.set_save_result_flag_training (save_result_flag_training)

    def set_save_result_flag (self, save_result_flag):
        super().set_save_result_flag (save_result_flag)
        for component in self.components:
            component.set_save_result_flag (save_result_flag)

    def set_overwrite (self, overwrite):
        super().set_overwrite (overwrite)
        for component in self.components:
            component.set_overwrite (overwrite)

    def set_save_fitting (self, save_fitting):
        super().set_save_fitting (save_fitting)
        for component in self.components:
            component.set_save_fitting (save_fitting)

# Cell
def make_pipeline(*components, cls=Pipeline, **kwargs):
    """Create `Pipeline` object of class `cls`, given `components` list."""
    pipeline = cls (**kwargs)
    pipeline.components = list(components)
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
class ColumnSelector (Component):
    def __init__ (self,
                  columns=[],
                  **kwargs):
        super().__init__ (**kwargs)
        self.columns = columns

    def _transform (self, df):
        return df[self.columns]

# Cell
class Concat (Component):
    def __init__ (self,
                  **kwargs):
        super().__init__ (**kwargs)

    def _apply (self, *dfs):
        return pd.concat(list(dfs), axis=1)

# Cell
class _BaseColumnTransformer (Pipeline):
    def __init__ (self, **kwargs):
        super().__init__ (**kwargs)
        self.concat = Concat (**kwargs)

    def _fit (self, df, y=None):
        for component in self.components:
            component.fit (df)
        return self

    def _transform (self, df):
        dfs = []
        for component in self.components:
            dfs.append (component.transform (df))
        df_result = self.concat.transform (*dfs)
        return df_result

class ColumnTransformer (_BaseColumnTransformer):
    def __init__ (self, *transformers, **kwargs):
        self.components = make_column_transformer_pipelines (*transformers, **kwargs)
        super().__init__ (**kwargs)

# Cell
class Identity (Component):
    def __init__ (self, **kwargs):
        super ().__init__ (**kwargs)

    def _transform (self, X):
        return X

def make_column_transformer_pipelines (*transformers, **kwargs):
    pipelines = []
    for name, transformer, columns in transformers:
        if (type(transformer) is str) and transformer == 'passthrough':
            transformer = Identity (**kwargs)
        pipeline = make_pipeline(ColumnSelector(columns, **kwargs),
                                 transformer,
                                 name = name,
                                 **kwargs)
        pipelines.append (pipeline)

    return pipelines


def make_column_transformer (*transformers, **kwargs):
    transformers_with_name = []
    for transformer, columns in transformers:
        columns_name = ''.join([x[0] for x in columns])
        if len(columns_name) > 5:
            columns_name = columns_name[:5]
        if (type(transformer) is str) and transformer == 'passthrough':
            transformer_name = 'pass'
        elif hasattr(transformer, 'name'):
            transformer_name = transformer.name
        else:
            transformer_name = transformer.__class__.__name__
        name = f'{transformer_name}_{columns_name}'
        transformers_with_name.append ((name, transformer, columns))

    pipelines = make_column_transformer_pipelines (*transformers_with_name, **kwargs)
    column_transformer = _BaseColumnTransformer ()
    column_transformer.components = pipelines
    return column_transformer


# Cell
