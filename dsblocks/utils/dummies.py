# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/utils/dummies.ipynb (unless otherwise specified).

__all__ = ['SumXY', 'DummyEstimator', 'Intermediate', 'Higher', 'Sum1', 'Multiply10', 'NewParallel', 'MinMaxClass',
           'Min10', 'Max10', 'make_pipe_fit1', 'make_pipe_fit2', 'make_pipe1', 'make_pipe2', 'Min10direct',
           'Max10direct', 'Sum1direct', 'Multiply10direct', 'MaxOfPositiveWithSeparateLabels',
           'MinOfPositiveWithoutSeparateLabels', 'DataSource', 'subtract_xy', 'DummyClassifier']

# Cell
from functools import partial
import pandas as pd
import numpy as np
from sklearn.utils import Bunch

from ..core.components import (Component,
                                          PandasComponent,
                                          SamplingComponent,
                                          NoSaverComponent)
from ..core.compose import MultiComponent, Sequential, Parallel
import dsblocks.config.bt_defaults as dflt

# Cell
class SumXY (Component):
    def _apply (self, x, y):
        return x+y

# Cell
class DummyEstimator ():
    def __init__ (self, factor=3):
        self.factor = factor
    def fit (self, X, y=None):
        self.sum = sum(X)
    def transform (self, X):
        return X * self.factor + self.sum

# Cell
class Intermediate (MultiComponent):
    def __init__ (self, name=None, z=6, h=10, x=3, **kwargs):
        super().__init__ (name=name, **kwargs)
        self.first = Component (name='first_component', **kwargs)
        self.second = Component (name='second_component', **kwargs)

class Higher (MultiComponent):
    def __init__ (self, x=2, y=3, **kwargs):
        super().__init__ (**kwargs)
        self.first = Intermediate (name='first_intermediate', **kwargs)
        self.second = Intermediate (name='second_intermediate', **kwargs)
        self.gather_descendants()


# Cell
class Sum1 (Component):
    def __init__ (self, raise_error=False, **kwargs):
        super().__init__ (**kwargs)
        self.applied = False
    def _apply (self, X):
        return X+1
    def apply (self, *X, **kwargs):
        self.applied = True
        if self.raise_error: raise RuntimeError (f'{self.name}: apply should not be called')
        return super().apply (*X, **kwargs)
    __call__ = apply
    transform = apply

class Multiply10 (Component):
    def __init__ (self, raise_error=False, **kwargs):
        super().__init__ (**kwargs)
        self.applied = False
    def _apply (self, X):
        return X*10
    def apply (self, *X, **kwargs):
        self.applied = True
        if self.raise_error: raise RuntimeError (f'{self.name}: apply should not be called')
        return super().apply (*X, **kwargs)
    __call__ = apply
    transform = apply

# Cell
class NewParallel (Parallel):
    def __init__ (self, *components, raise_error=False, **kwargs):
        super().__init__ (*components, **kwargs)
        self.applied = False
    def apply (self, *X, **kwargs):
        self.applied = True
        if self.raise_error: raise RuntimeError (f'{self.name}: apply should not be called')
        return super().apply (*X, **kwargs)
    __call__ = apply
    transform = apply

# Cell
class MinMaxClass (Component):
    def __init__ (self, raise_error=False, **kwargs):
        super().__init__ (**kwargs)
        self.estimator = Bunch()
        self.applied = False
        self.fitted = False
        self.fit_applied = False
    def apply (self, *X, **kwargs):
        self.applied = True
        if self.raise_error: raise RuntimeError (f'{self.name}: apply should not be called')
        return super().apply (*X, **kwargs)
    __call__ = apply
    transform = apply
    def fit (self, X, y=None, **kwargs):
        self.fitted = True
        if self.raise_error: raise RuntimeError (f'{self.name}: fit should not be called')
        return super().fit (X, y=y, **kwargs)
    def fit_apply (self, X, y=None, **kwargs):
        self.fit_applied = True
        if self.raise_error: raise RuntimeError (f'{self.name}: fit_apply should not be called')
        return super().fit_apply (X, y=y, **kwargs)
    fit_transform = fit_apply
    fit_predict = fit_apply

class Min10 (MinMaxClass):
    def __init__ (self, **kwargs):
        super().__init__ (**kwargs)
    def _fit (self, X, y=None):
        self.estimator['minim'] = X.min(axis=0)
    def _apply (self, X):
        return X*10+self.estimator.minim

class Max10 (MinMaxClass):
    def __init__ (self, **kwargs):
        super().__init__ (**kwargs)
    def _fit (self, X, y=None):
        self.estimator['maxim'] = X.max(axis=0)
    def _apply (self, X):
        return X*10+self.estimator.maxim

# Cell
def make_pipe_fit1 (**kwargs):
    pipe = Sequential (Sum1 (name='A', **kwargs),
                       Min10 (name='B', **kwargs),
                        Max10 (name='C', **kwargs),
                        Sum1 (name='D', **kwargs),
                        Max10 (name='E', **kwargs),
                        Sum1 (name='F', **kwargs),
                        Min10 (name='G', **kwargs),
                        **kwargs)

    return pipe

def make_pipe_fit2 (new_parallel=False, **kwargs):
    ParallelClass = Parallel if not new_parallel else NewParallel
    parallel = ParallelClass (
        Multiply10 (name='B1', **kwargs),
        Min10 (name='B2', **kwargs),
        Sequential (Min10 (name='B3a', **kwargs), Max10 (name='B3b', **kwargs),
                    Sum1 (name='B3c', **kwargs), Min10 (name='B3d', **kwargs), **kwargs),
        Sequential (Sum1 (name='B4a', **kwargs), Max10 (name='B4b', **kwargs),
                    Min10 (name='B4c', **kwargs), Sum1 (name='B4d', **kwargs),
                    Max10 (name='B4e', **kwargs), **kwargs),
        Max10 (name='B5', **kwargs),
        initialize_result=lambda:np.array([]),
        join_result=lambda Xr, Xi_r, components, i: np.r_[Xr.reshape(-1,Xi_r.shape[1]), Xi_r],
        **kwargs)
    print (f'parallel class: {parallel.__class__}')
    pipe = Sequential (Sum1 (name='A0', **kwargs), Min10 (name='A1', **kwargs), parallel,
                       Sum1 (name='C', **kwargs), Max10 (name='D', **kwargs),
                       Sum1 (name='E', **kwargs), **kwargs)
    pipe.gather_descendants ()

    return pipe

# Cell
def make_pipe1 (**kwargs):
    pipe = Sequential (Sum1 (name='A', **kwargs),
                        Multiply10 (name='B', **kwargs),
                        Sum1 (name='C', **kwargs),
                        Multiply10 (name='D', **kwargs),
                        Sum1 (name='E', **kwargs),
                        **kwargs)

    return pipe

def make_pipe2 (new_parallel=False, **kwargs):
    ParallelClass = Parallel if not new_parallel else NewParallel
    parallel = ParallelClass (
        Multiply10 (name='B1', **kwargs),
        Sequential (Multiply10 (name='B2a', **kwargs), Sum1 (name='B2b', **kwargs),
                    Multiply10 (name='B2c', **kwargs), **kwargs),
        Sequential (Sum1 (name='B3a', **kwargs), Multiply10 (name='B3b', **kwargs),
                    Sum1 (name='B3c', **kwargs), **kwargs),
        Sum1 (name='B4', **kwargs),
        initialize_result=lambda:np.array([]),
        join_result=lambda Xr, Xi_r, components, i: np.r_[Xr.reshape(-1,Xi_r.shape[1]), Xi_r],
        **kwargs)
    print (f'parallel class: {parallel.__class__}')
    pipe = Sequential (Sum1 (name='A', **kwargs), parallel, Sum1 (name='C', **kwargs),
                       Sum1 (name='D', **kwargs), **kwargs)
    pipe.gather_descendants ()

    return pipe

# Cell
class Min10direct (Component):
    def __init__ (self, **kwargs):
        super().__init__ (**kwargs)
        self.create_estimator ()
    def _fit (self, X, y=None):
        self.estimator['minim'] = X.min(axis=0)
    def _apply (self, X):
        return X*10+self.estimator.minim

class Max10direct (Component):
    def __init__ (self, **kwargs):
        super().__init__ (**kwargs)
        self.create_estimator ()
    def _fit (self, X, y=None):
        self.estimator['maxim'] = X.max(axis=0)
    def _apply (self, X):
        return X*10+self.estimator.maxim

# Cell
class Sum1direct (Component):
    def __init__ (self, **kwargs):
        super().__init__ (**kwargs)
    def _apply (self, X):
        return X+1

class Multiply10direct (Component):
    def __init__ (self, **kwargs):
        super().__init__ (**kwargs)
    def _apply (self, X):
        return X*10

# Cell
class MaxOfPositiveWithSeparateLabels (Component):
    def __init__ (self, **kwargs):
        super().__init__ (**kwargs)
        self.create_estimator ()
    def _fit (self, X, y):
        self.estimator.update (max=np.max(X[y==1], axis=0))
    def _apply (self, X):
        return X*10 + self.estimator.max

class MinOfPositiveWithoutSeparateLabels (Component):
    def __init__ (self, **kwargs):
        super().__init__ (**kwargs)
        self.create_estimator ()
    def _fit (self, X):
        self.estimator.update (min=np.min(X[X.label==1].values[:,:-1], axis=0))
    def _apply (self, X):
        return X*10 + self.estimator.min

class DataSource (Component):
    def __init__ (self, **kwargs):
        super().__init__ (**kwargs)
    def _apply (self):
        X = pd.DataFrame ({'a': [1,2,3,4],
                           'b': [4,5,6,7],
                           'c': [10,20,30,40],
                           'd': [40,50,60,70]})
        Y = pd.DataFrame ({'a': [2,3,4,5],
                           'b': [5,6,7,8],
                           'c': [1,2,3,4],
                           'd': [4,5,6,7]})
        label = [0, 1, 1, 0]

        return X, Y, label

def subtract_xy (X, Y):
    return X-Y

# Cell
class DummyClassifier (Component):

    op_mapping = {'max': np.max, 'min': np.min, 'mean': np.mean, 'sum': np.sum}

    def __init__ (self, project_op='max', statistic='mean', factor=1000, apply_func='simple',
                  data_converter='StandardConverter', **kwargs):

        assert apply_func in {'simple', 'distance'}
        self._apply = (self._apply_simple if apply_func=='simple'
                      else self._apply_distance)

        self.project_op = partial (self.op_mapping[project_op], axis=1)
        self.statistic = self.op_mapping[statistic]

        super().__init__ (data_converter=data_converter, **kwargs)

    def _fit (self, X, y, **kwargs):
        Xproject = self.project_op (X)
        statistic_0 = self.statistic (Xproject[y==0])
        statistic_1 = self.statistic (Xproject[y==1])
        statistic = (statistic_0 - statistic_1) * self.factor
        self.create_estimator (statistic_0=statistic_0, statistic_1=statistic_1, statistic=statistic)

    def _apply_simple (self, X, **kwargs):
        return self.project_op(X) + self.estimator.statistic

    def _apply_distance (self, X, **kwargs):
        Xproject = self.project_op(X)
        return np.abs(Xproject - self.estimator.statistic_0) - np.abs(Xproject - self.estimator.statistic_1)