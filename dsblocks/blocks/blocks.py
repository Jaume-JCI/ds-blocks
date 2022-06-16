# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/blocks/blocks.ipynb (unless otherwise specified).

__all__ = ['Splitter', 'DoubleKFoldBase', 'SingleKFold', 'FixedDoubleKFold', 'SkSplitGenerator', 'Evaluator',
           'PandasEvaluator']

# Cell
import abc
import sklearn
import numpy as np

from ..core.components import Component
from ..config import bt_defaults as dflt

# Cell
class Splitter (Component):
    def __init__ (self, training='train', validation='validation', test='test',
                  split_col='split', **kwargs):
        super().__init__ (**kwargs)

    def _apply (self, df):
        result = dict(training=df[df[self.split_col]==self.training],
                        validation=df[df[self.split_col]==self.validation],
                        test=df[df[self.split_col]==self.test])
        return {k:result[k] for k in result if not result[k].empty}

# Cell
class DoubleKFoldBase (metaclass=abc.ABCMeta):
    def __init__ (self, cv, split_col='split', label_col='label', group_col=None, **kwargs):
        self.cv = cv
        self.n_splits = self.cv.get_n_splits ()
        self.split_col = split_col
        self.label_col = label_col
        self.group_col = group_col

    def get_n_splits (self):
        return self.n_splits

    @abc.abstractmethod
    def split (self, df, y=None, groups=None):
        pass

# Cell
class SingleKFold (DoubleKFoldBase):
    def __init__ (self, cv, **kwargs):
        super().__init__ (cv, **kwargs)
    def split (self, df, y=None, groups=None):
        groups = (groups if groups is not None
                  else df[self.group_col] if self.group_col is not None
                  else None)
        y = y if y is not None else df[self.label_col]
        self.generator = self.cv.split (df, y, groups=groups)
        empty_array = np.array([])
        for i in range(self.n_splits):
            training, validation = next (self.generator)
            yield training, validation, empty_array

# Cell
class FixedDoubleKFold (DoubleKFoldBase):
    def __init__ (self, cv, input_test_label='test', **kwargs):
        super().__init__ (cv, **kwargs)
        self.input_test_label = input_test_label

    def split (self, df, y=None, groups=None):
        test = np.where(df[self.split_col]==self.input_test_label)[0]
        training_cond = df[self.split_col] != self.input_test_label
        training = np.where (training_cond)[0]

        groups = (groups[training] if groups is not None
                  else df.loc[training_cond, self.group_col] if self.group_col is not None
                  else None)
        y = (y[training] if y is not None else df.loc[training_cond, self.label_col])

        self.generator = self.cv.split (df[training_cond], y, groups=groups)

        for i in range(self.n_splits):
            training_training, training_validation = next (self.generator)
            validation_final, training_final = training[training_validation], training[training_training]
            yield training_final, validation_final, test

# Cell
class SkSplitGenerator (Component):
    def __init__ (self, split_generator, group_col=None, label_col=None, split_col=None,
                  use_splitter=False, training_label='training', validation_label='validation',
                  test_label='test', type_split='single', input_test_label='test', **kwargs):
        super ().__init__ (**kwargs)
        self.splitter = Splitter () if use_splitter else None
        self.generator = None
        if type_split == 'single':
            self.split_generator = SingleKFold (split_generator, split_col=split_col, label_col=label_col,
                                                group_col=group_col)
            self.validation_label = self.test_label
        elif type_split == 'fixed':
            self.split_generator = FixedDoubleKFold (split_generator, input_test_label=input_test_label,
                                                     split_col=split_col, label_col=label_col,
                                                     group_col=group_col)
        else:
            raise NotImplementedError (f'type_split {type_split} not recognized')

    def _fit_apply (self, X, y=None, **kwargs):
        if self.generator is None: self.generator = self.split_generator.split (X, y=y, **kwargs)
        training, validation, test = next (self.generator)
        X = self._create_split (X, training, validation, test)
        return X

    def _apply (self, X, **kwargs):
        training, validation, test = np.array([]), np.array([]), np.arange (X.shape[0])
        X = self._create_split (X, training, validation, test)
        return X

    def _create_split (self, X, training, validation, test):
        if self.split_col is not None:
            X[self.split_col] = None
            X[self.split_col].iloc[training] = self.training_label
            X[self.split_col].iloc[validation] = self.validation_label
            X[self.split_col].iloc[test] = self.test_label
        else:
            X = (X, (training, validation, test))

        if self.use_splitter:
            X = self.splitter (X)
        return X

    def reset (self):
        self.generator = None

# Cell
class Evaluator (Component, metaclass=abc.ABCMeta):
    def __init__ (self, classification_metrics='accuracy_score', regression_metrics=[], custom_metrics=[],
                  **kwargs):
        classification_metrics = self._get_metrics (classification_metrics)
        regression_metrics = self._get_metrics (regression_metrics)
        super().__init__ (**kwargs)
        self.apply_to_separate_splits = True

    def _get_metrics (self, metrics):
        metrics = [metrics] if isinstance (metrics, str) else metrics
        for i, metric in enumerate(metrics):
            metrics[i] = getattr(sklearn.metrics, metrics[i]) if isinstance(metrics[i], str) else metrics[i]
        return metrics

    @abc.abstractmethod
    def _apply (self, df, **kwargs):
        pass

# Cell
class PandasEvaluator (Evaluator):
    def __init__ (self, groundtruth_col='label', prediction_col='pred', classification_col='classification',
                  **kwargs):
        super().__init__ (**kwargs)

    def _apply (self, df, **kwargs):
        dict_results = {metric.__name__: metric (df[self.groundtruth_col], df[self.classification_col])
                        for metric in self.classification_metrics}
        dict_results.update( {metric.__name__: metric (df[self.groundtruth_col], df[self.prediction_col])
                                for metric in self.regression_metrics})
        for metric in self.custom_metrics:
            dict_results.update (metric (df, label_col=self.groundtruth_col, prediction_col=self.prediction_col,
                                         classification_col=self.classification_col))
        return dict_results