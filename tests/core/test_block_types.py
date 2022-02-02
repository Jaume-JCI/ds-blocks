# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/00_tests/core/tst.block_types.ipynb (unless otherwise specified).

__all__ = ['component_save_data_fixture', 'test_component_config', 'test_component_store_attrs',
           'test_component_aliases', 'test_component_predict', 'test_component_multiple_inputs',
           'TransformWithFitApply', 'TransformWithoutFitApply', 'test_component_fit_apply', 'MyDataConverter',
           'TransformWithFitApplyDC', 'test_fit_apply_inplace', 'test_component_validation_test',
           'TransformWithoutFitApply2', 'TransformWithFitApply2', 'component_save_data', 'test_component_save_load',
           'Transform1', 'test_component_run_depend_on_existence', 'test_component_logger',
           'test_component_data_converter', 'test_component_data_io', 'test_component_equal', 'test_set_paths',
           'test_sampling_component', 'test_sklearn_component', 'test_no_saver_component', 'get_data_for_one_class',
           'test_one_class_sklearn_component', 'test_pandas_component']

# Cell
import pytest
import os
import joblib
from IPython.display import display
import pandas as pd
import numpy as np
from sklearn.utils import Bunch
from pathlib import Path

from block_types.core.block_types import *
from block_types.core.data_conversion import DataConverter, NoConverter, PandasConverter, data_converter_factory
from block_types.core.utils import DataIO, SklearnIO, PandasIO, NoSaverIO
from block_types.utils.utils import remove_previous_results
from block_types.utils.utils import set_logger
import block_types.config.bt_defaults as dflt
from block_types.core.data_conversion import DataConverter

# Cell
@pytest.fixture (name='component_save_data')
def component_save_data_fixture():
    return component_save_data()

# Comes from block_types.ipynb, cell
#@pytest.mark.reference_fails
def test_component_config ():

    # **********************************************************************
    # test obtain_config_params method
    # **********************************************************************
    tr = Component(name='sky')
    config = dict(first=1,
                  second=2,
                  third=3,
                  sky=dict (second=4)
                 )
    config_r = tr.obtain_config_params (**config)
    logger = set_logger (dflt.name_logger, verbose=dflt.verbose)
    assert config_r=={'first': 1, 'second': 4, 'third': 3, 'sky': {'second': 4}, 'verbose': dflt.verbose, 'logger': logger}
    assert config == {'first': 1, 'second': 2, 'third': 3, 'sky': {'second': 4}}

    # **********************************************************************
    # test that component saves results when using global
    # parameter save=True
    # **********************************************************************
    class MyTransform (Component):
        def __init__ (self,**kwargs):
            super().__init__ (**kwargs)
            self.create_estimator ()

        def _fit (self, X, y=None):
            self.estimator.mu = X.mean()
        def _transform (self, X):
            return X-self.estimator.mu

    path_results = 'testing_configuration'
    tr = MyTransform (path_results=path_results,
                      save = True)

    X = np.array([[1,2,3],[4,5,6]])
    tr.fit_transform(X)

    import os
    l = sorted(os.listdir(path_results))
    assert l==['models','whole'], f'found: {l}'

    # **********************************************************************
    # test that component does not save results when we
    # use component-specific parameter MyTransform = dict(save=False)
    # **********************************************************************
    from block_types.utils.utils import remove_previous_results
    remove_previous_results (path_results)

    tr = MyTransform (data_io = SklearnIO(
                                  path_results='testing_configuration',
                                  save = True,
                                  MyTransform = dict(save=False)
                                )
                     )
    tr.fit_transform(X)
    import pytest
    with pytest.raises(FileNotFoundError):
        os.listdir(path_results)

# Comes from block_types.ipynb, cell
#@pytest.mark.reference_fails
def test_component_store_attrs ():
    # recursively storing __init__ attrs across hiearchy of classes
    class Intermediate (Component):
        def __init__ (self, x=3, y=4, **kwargs):
            super().__init__ (**kwargs)

    class Final (Intermediate):
        def __init__ (self, z=6, h=[2,3,5], **kwargs):
            super().__init__ (**kwargs)

    o = Final (x=9, h=[1,2,4])
    assert o.x==9 and o.y==4 and o.z==6 and o.h==[1,2,4]

    o = Final (y=7, z=10, h=[1,2,4], Final={'h': [9,11,10]})
    assert o.x==3 and o.y==7 and o.z==10 and o.h==[9,11,10]

    # only attributes specific of Final are replaced.
    # trying to replace attributes specific of Intermediate
    # does not work
    o = Final (y=7, z=10, h=[1,2,4], Intermediate={'y': 12})
    assert o.x==3 and o.y==7 and o.z==10 and o.h==[1,2,4]

    class Intermediate (Component):
        def __init__ (self, x=3, y=4, **kwargs):
            super().__init__ (**kwargs)

    class Final (Intermediate):
        def __init__ (self, z=6, h=[2,3,5], **kwargs):
            super().__init__ (**kwargs)

    o = Final (x=9, h=[1,2,4], group='group_1', group_1={'y': 10, 'z':60})
    assert o.x==9 and o.y==10 and o.z==60 and o.h==[1,2,4]


     # *******************
    # test using same field in B4 and in A3, but
    # B4 passes that value to A3 in super(),
    # after modifying it
    # *****************
    class A (Component):
        def __init__ (self, x=3, path_results='test_recursive', **kwargs):
            path_results = f'{path_results}/another'
            super ().__init__ (path_results=path_results, error_if_present=True,
                               **kwargs)

    class B (A):
        def __init__ (self, x=30, y=10, **kwargs):
            x = x*2
            super().__init__ (x=x, **kwargs)
            self.ab = A (**kwargs)

    b = B ()
    assert b.x==60 and b.ab.x==3 and b.y==10 and b.path_results==Path('test_recursive/another').resolve()

    b = B (x=6, path_results='new_path')
    assert b.x==12 and b.ab.x==3 and b.y==10 and b.path_results==Path('new_path/another').resolve()

    # *******************
    # test using same field in C and in A, but
    # the field is modified in a parent B
    # *****************
    class C(B):
        def __init__ (self, x=40, z=100, **kwargs):
            super().__init__ (x=x, **kwargs)
            self.b = B(**kwargs)

    with pytest.raises (RuntimeError):
        c = C()

    c = C(ignore={'x'})
    assert c.x==80 and c.y==10 and c.z==100 and c.b.x==60 and c.b.y==10

    c = C (x=9, ignore={'x'})
    assert c.x==18 and c.y==10 and c.z==100 and c.b.x==60 and c.b.y==10

    assert not hasattr(c, 'ignore')

# Comes from block_types.ipynb, cell
#@pytest.mark.reference_fails
def test_component_aliases ():

    # test that we can implement _transform and use all the aliases
    # (transform, predict, apply,  __call__)
    class MyTransform (Component):
        def _apply (self, x):
            return x*2

    my_transform = MyTransform()
    assert my_transform.transform (3) == 6
    assert my_transform.predict (3) == 6
    assert my_transform.apply (3) == 6
    assert my_transform (3) == 6

    # test that we can implement _apply and use all the aliases
    # (transform, predict, apply and __call__)
    class MyTransform2 (Component):
        def _apply (self, x):
            return x*2

    my_transform2 = MyTransform2()
    assert my_transform2.transform (3) == 6
    assert my_transform2.predict (3) == 6
    assert my_transform2.apply (3) == 6
    assert my_transform2 (3) == 6

    # test that we can implement _predict and use all the aliases
    # (transform, predict, apply and __call__)
    class MyTransform3 (Component):
        def _predict (self, x):
            return x*2

    my_transform3 = MyTransform3()
    assert my_transform3.transform (3) == 6
    assert my_transform3.predict (3) == 6
    assert my_transform3.apply (3) == 6
    assert my_transform3 (3) == 6

    # test that an exception is raised if neither _tranform nor _apply are defined
    class MyTransform4 (Component):
        def _wrong_method (self, x):
            return x*2

    my_transform4 = MyTransform4 ()

    import pytest
    with pytest.raises(Exception):
        my_transform4.transform(3)


    # test that an exception is raised if more than one alias is implemented
    class MyTransform5 (Component):
        def _predict (self, x):
            return x*2
        def _apply (self, x):
            return x*2

    my_transform5 = MyTransform5 ()

    import pytest
    with pytest.raises(Exception):
        my_transform5.transform(3)

# Comes from block_types.ipynb, cell
#@pytest.mark.reference_fails
def test_component_predict ():
# TODO: remove this cell

    class MyTransform (Component):
        def __init__ (self, **kwargs):
            super().__init__ (
                data_converter=PandasConverter(**kwargs),
                **kwargs)

        def _predict (self, x):
            return x['a']+x['b']

    my_transform = MyTransform()

    df = pd.DataFrame ({'a': [10,20,30],'b':[4,5,6]})

    pd.testing.assert_frame_equal(my_transform.transform (df).to_frame(),
                                  pd.DataFrame ({0: [14,25,36]})
                                 )

    if False:
        pd.testing.assert_frame_equal(my_transform.predict (df),
                                      pd.DataFrame ({0: [14,25,36]})
                                     )

# Comes from block_types.ipynb, cell
#@pytest.mark.reference_fails
def test_component_multiple_inputs ():
# test that we can apply tranform to multiple data items
    class MyTransform (Component):
        def _apply (self, x, y):
            return x+y

    my_transform = MyTransform ()
    result = my_transform.transform (3, 4)
    print (result)
    assert result==7

    # test that we can apply tranform to single data items
    class MyTransform2 (Component):
        def _apply (self, x):
            return x*2

    my_transform2 = MyTransform2 ()
    result = my_transform2.transform (3)
    print (result)
    assert result==6

# Comes from block_types.ipynb, cell
# example with _fit_apply implemented
class TransformWithFitApply (Component):
    def __init__ (self, **kwargs):
        super().__init__ (**kwargs)
    def _fit (self, X, y=None):
        self.sum = X.sum(axis=0)
    def _apply (self, X):
        return X + self.sum
    def _fit_apply (self, X, y=None):
        self.sum = X.sum(axis=0)*10
        return X + self.sum

    # example without _fit_apply implemented
class TransformWithoutFitApply (Component):
    def __init__ (self, **kwargs):
        super().__init__ (**kwargs)
    def _fit (self, X, y=None):
        self.sum = X.sum(axis=0)
    def _apply (self, X):
        return X + self.sum

#@pytest.mark.reference_fails
def test_component_fit_apply ():

    tr1 = TransformWithFitApply ()
    X = np.array ([100, 90, 10])
    result = tr1.fit_apply (X)
    assert (result==(X+2000)).all()

    # same result obtained by aliases
    result = tr1.fit_transform (X)
    assert (result==(X+2000)).all()

    # different result if we apply fit and apply separately
    result = tr1.fit (X).transform (X)
    assert (result==(X+200)).all()

    # transform without fit_apply
    tr2 = TransformWithoutFitApply ()
    result = tr2.fit_apply (X)
    assert (result==(X+200)).all()

    # same result obtained by aliases
    result = tr2.fit_transform (X)
    assert (result==(X+200)).all()

# Comes from block_types.ipynb, cell
# example with _fit_apply implemented
class MyDataConverter (DataConverter):
    def __init__ (self, **kwargs):
        super ().__init__ (**kwargs)
    def convert_before_fitting (self, X, y=None):
        self.orig = X[0]
        X[0] = 0
        return X, y
    def convert_after_fitting (self, X, y=None):
        X[0] = self.orig
        return X
    def convert_before_transforming (self, X, **kwargs):
        self.orig2 = X[1]
        X[1] = 0
        return X
    def convert_after_transforming (self, X, **kwargs):
        X[1] = self.orig2
        return X

class TransformWithFitApplyDC (Component):
    def __init__ (self, **kwargs):
        super().__init__ (data_converter=MyDataConverter,**kwargs)
    def _fit (self, X, y=None):
        self.sum = X.sum(axis=0)
    def _apply (self, X):
        return X + self.sum
    def _fit_apply (self, X, y=None):
        self.sum = X.sum(axis=0)
        return X + self.sum

#@pytest.mark.reference_fails
def test_fit_apply_inplace ():
    tr1 = TransformWithFitApplyDC ()
    X = np.array ([100, 90, 10])
    result = tr1.fit_apply (X)
    assert (result==[100,  90, 110]).all()
    assert (X==[100,  90,  10]).all()

    tr1 = TransformWithFitApplyDC (inplace=False)
    X = np.array ([100, 90, 10])
    result = tr1.fit_apply (X)
    assert (result==[10, 90, 20]).all()
    assert (X==[ 0,  0, 10]).all()

# Comes from block_types.ipynb, cell
#@pytest.mark.reference_fails
def test_component_validation_test ():
    class Transform1 (Component):
        def __init__ (self, **kwargs):
            super().__init__ (**kwargs)
        def _fit (self, X, y=None, validation_data=None, test_data=None):
            self.sum = X.sum(axis=0)

            print (f'validation_data: {validation_data}')
            print (f'test_data: {test_data}')

            self.validation_data = validation_data
            self.test_data = test_data

        def _apply (self, X):
            return X + self.sum

    tr1 = Transform1 ()
    X = np.array ([100, 90, 10])

    # case 1: validation_data and test_data are not tuples
    validation_data = np.array ([100, 90, 10])*10
    test_data = np.array ([100, 90, 10])*100
    result = tr1.fit_apply (X, validation_data=validation_data, test_data=test_data)
    assert (tr1.validation_data==validation_data).all()
    assert (tr1.test_data==test_data).all()

    # case 2: validation_data is a tuple, and test_data is not given
    result = tr1.fit_apply (X, validation_data=(validation_data,1))
    assert (tr1.validation_data[0]==validation_data).all()
    assert tr1.validation_data[1]==1
    assert tr1.test_data is None

    # case 3: validation_data is a tuple with more than 2 elements, exception is raised
    import pytest
    with pytest.raises(ValueError):
        result = tr1.fit_apply (X, validation_data=(validation_data,1,2))

# Comes from block_types.ipynb, cell

# example with _fit_apply implemented
class TransformWithoutFitApply2 (Component):
    def __init__ (self, error_if_fit=False, error_if_apply=False,  **kwargs):
        super().__init__ (data_io='SklearnIO', **kwargs)
        self.estimator = Bunch(sum=None)
    def _fit (self, X, y=None):
        if self.error_if_fit: raise RuntimeError ('fit should not run')
        print ('running _fit')
        self.estimator.sum = X.sum(axis=0)
    def _apply (self, X):
        if self.error_if_apply: raise RuntimeError ('apply should not run')
        if self.estimator.sum is None: raise RuntimeError ('fit should be called before apply')
        print ('running _apply')
        return X + self.estimator.sum

Transform1 = TransformWithoutFitApply2

class TransformWithFitApply2 (Component):
    def __init__ (self, error_if_fit=False, error_if_apply=False, error_if_fit_apply=False,
                  **kwargs):
        super().__init__ (data_io='SklearnIO', **kwargs)
        self.estimator = Bunch(sum=None)
    def _fit (self, X, y=None):
        if self.error_if_fit: raise RuntimeError ('fit should not run')
        print ('running _fit')
        self.estimator.sum = X.sum(axis=0)
    def _apply (self, X):
        if self.error_if_apply: raise RuntimeError ('apply should not run')
        if self.estimator.sum is None: raise RuntimeError ('fit should be called before apply')
        print ('running _apply')
        return X + self.estimator.sum
    def _fit_apply (self, X, y=None):
        if self.error_if_fit_apply: raise RuntimeError ('fit_apply should not run')
        print ('running _fit_apply')
        self.estimator.sum = X.sum(axis=0)
        return X + self.estimator.sum

def component_save_data ():
    X = np.array ([100, 90, 10])
    return X

#@pytest.mark.reference_fails
def test_component_save_load (component_save_data):

    X = component_save_data

    path_results = 'component_loading_saving'
    remove_previous_results (path_results=path_results)

    tr1 = Transform1 (path_results=path_results)
    tr1.fit (X)
    result = tr1.apply (X)

    tr2 = Transform1 (path_results=path_results)
    tr2.load_estimator()
    assert tr2.estimator.sum == tr1.estimator.sum

    result2 = tr2.data_io.load_result ()
    assert (result2 == sum(X)+X).all()

    import os

    assert os.listdir (f'{path_results}/whole')==['transform_without_fit_apply2_result.pk']
    assert os.listdir (f'{path_results}/models')==['transform_without_fit_apply2_estimator.pk']

    result_b = tr1.apply (X*2, split='test')
    result2b = tr2.data_io.load_result (split='test')
    assert (result_b==result2b).all()
    assert os.listdir (f'{path_results}/test')==['transform_without_fit_apply2_result.pk']

    result2b = tr2.data_io.load_result ()
    assert (result_b!=result2b).all()

    remove_previous_results (path_results=path_results)


    # Test that no saving is done if save=False
    tr1 = Transform1 (path_results=path_results, save=False)
    tr1.fit (X)
    result = tr1.apply (X)
    assert not os.path.exists(path_results)


# Comes from block_types.ipynb, cell
#@pytest.mark.reference_fails
def test_component_run_depend_on_existence ():

    path_results = 'component_run_existence'
    remove_previous_results (path_results=path_results)

    tr1 = TransformWithFitApply2 (path_results=path_results, error_if_fit=True, error_if_apply=True)
    X = np.array ([100, 90, 10])
    result = tr1.fit_apply (X)
    assert (result==(X+200)).all()

    assert os.listdir(f'{path_results}/models')==['transform_with_fit_apply2_estimator.pk']

    assert os.listdir(f'{path_results}/whole')==['transform_with_fit_apply2_result.pk']

    tr1 = TransformWithFitApply2 (path_results=path_results, error_if_fit=True, error_if_apply=True,
                                  error_if_fit_apply=True)
    result2 = tr1.fit_apply (X)
    assert (result2==(X+200)).all()

    assert tr1.estimator=={'sum': 200}

    tr2 = TransformWithFitApply2 (path_results=path_results, error_if_fit=True, error_if_apply=True,
                                  error_if_fit_apply=True)
    result3 = tr2.apply (X)

    assert (result3==(X+200)).all()
    assert tr2.estimator=={'sum': None}

    os.remove (f'{path_results}/models/transform_with_fit_apply2_estimator.pk')

    with pytest.raises (RuntimeError):
        result3 = tr2.fit_apply (X)

    tr2.error_if_fit_apply = False
    result4 = tr2.fit_apply (X)
    assert tr2.estimator=={'sum': 200}
    assert (result4==(X+200)).all()

    os.remove (f'{path_results}/whole/transform_with_fit_apply2_result.pk')

    tr3 = TransformWithFitApply2 (path_results=path_results, error_if_fit=True, error_if_apply=True,
                                  error_if_fit_apply=True)
    with pytest.raises (RuntimeError):
        _ = tr3.apply (X)
    with pytest.raises (RuntimeError):
        _ = tr3.fit_apply (X)
    tr3.error_if_fit_apply = False
    result5 = tr3.fit_apply (X)
    assert tr3.estimator=={'sum': 200}
    assert (result5==(X+200)).all()

    assert os.listdir (f'{path_results}/whole')==['transform_with_fit_apply2_result.pk']
    assert os.listdir (f'{path_results}/models')==['transform_with_fit_apply2_estimator.pk']

    remove_previous_results (path_results)

    tr4 = TransformWithFitApply2 (path_results=path_results, error_if_fit=False, error_if_apply=False,
                                  error_if_fit_apply=True)
    result6 = tr4.fit(X).apply (X)
    assert tr4.estimator=={'sum': 200}
    assert (result6==(X+200)).all()
    assert os.listdir (f'{path_results}/whole')==['transform_with_fit_apply2_result.pk']
    assert os.listdir (f'{path_results}/models')==['transform_with_fit_apply2_estimator.pk']

    remove_previous_results (path_results)

    tr5 = TransformWithoutFitApply2 (path_results=path_results, error_if_fit=False, error_if_apply=False)
    result7 = tr5.fit(X).apply (X)
    assert tr5.estimator=={'sum': 200}
    assert (result7==(X+200)).all()
    assert os.listdir (f'{path_results}/whole')==['transform_without_fit_apply2_result.pk']
    assert os.listdir (f'{path_results}/models')==['transform_without_fit_apply2_estimator.pk']

    remove_previous_results (path_results)

# Comes from block_types.ipynb, cell
#@pytest.mark.reference_fails
def test_component_logger (component_save_data):

    X = component_save_data

    tr1 = Transform1 (verbose=0)
    tr1.fit (X)
    result = tr1.apply (X)

    tr1 = Transform1 (verbose=1)
    tr1.fit (X)
    result = tr1.apply (X)

    tr1 = Transform1 (verbose=2)
    tr1.fit (X)
    result = tr1.apply (X)

# Comes from block_types.ipynb, cell
#@pytest.mark.reference_fails
def test_component_data_converter ():
    class MyTransform (Component):
        def __init__ (self, **kwargs):
            super().__init__ (data_converter='PandasConverter',
                              **kwargs)
        def _apply (self, x):
            return x*2

    my_transform = MyTransform (separate_labels=False)
    assert my_transform.data_converter.separate_labels is False
    assert type(my_transform.data_converter) is PandasConverter

    # example where data-converter uses class-specific parameters
    config = dict(separate_labels=False, MyTransform=dict(separate_labels=True))
    my_transform = MyTransform (**config)
    assert my_transform.data_converter.separate_labels is True
    assert config['separate_labels'] is False

# Comes from block_types.ipynb, cell
# exports tests.core.test_block_types
#@pytest.mark.reference_fails
def test_component_data_io ():
    import pandas as pd
    from block_types.utils.utils import remove_previous_results

    path_results = 'test_data_io'
    remove_previous_results (path_results=path_results)

    class MyTransform (Component):
        def __init__ (self, **kwargs):
            super().__init__ (result_io='pandas',
                              **kwargs)
        def _fit (self, X, y=None):
            self.estimator = Bunch(sum=100)

        def _apply (self, x):
            return pd.DataFrame ([[1,2],[3,4]], columns=['a','b'])

    my_transform = MyTransform (path_results='do_not_use', MyTransform=dict(path_results=path_results))
    my_transform.fit (1)
    assert os.listdir (f'{path_results}/models')==['my_transform_estimator.pk']

    df1 = my_transform.apply (1)
    assert os.listdir (f'{path_results}/whole')==['my_transform_result.parquet']

    assert not os.path.exists ('do_not_use')

    del my_transform
    my_transform = MyTransform (path_results='do_not_use', MyTransform=dict(path_results=path_results))
    #assert my_transform.estimator is None
    my_transform.load_estimator()
    assert my_transform.estimator == Bunch(sum=100)

    df2 = my_transform.load_result ()
    pd.testing.assert_frame_equal (df1, df2)

    remove_previous_results (path_results=path_results)

# Comes from block_types.ipynb, cell
#@pytest.mark.reference_fails
def test_component_equal ():
    path_results = 'assert_equal'
    remove_previous_results (path_results=path_results)

    class MyTransform (Component):
        def __init__ (self, noise=1e-10, different = False, **kwargs):
            super().__init__ (result_io='pandas',
                              **kwargs)
        def _fit (self, X, y=None):
            self.estimator = Bunch(sum=100)

        def _generate_noise (self):
            while True:
                noise = np.random.rand() * self.noise
                if noise > self.noise/10:
                    break
            return noise

        def _apply (self, x):
            df = pd.DataFrame ([[1.0,2.0],[3.0,4.0]], columns=['a','b']) + self._generate_noise ()
            if self.different:
                df = df+10
            x = np.array([[10.0,20.0],[30.0,40.0]]) + self._generate_noise ()
            result = dict(sequence=[[1.0,2.0], x+1, dict(vector=x, data=df)],
                          array=x+10)
            return result

    tr = MyTransform ()
    tr2= MyTransform ()
    tr.assert_equal (tr(1), tr2(1), significant_digits=7)

    import pytest
    with pytest.raises (AssertionError):
        tr = MyTransform (noise=1e-3, verbose=1)
        tr2= MyTransform (noise=1e-3, verbose=1)
        tr.assert_equal (tr(1), tr2(1), significant_digits=7)

    with pytest.raises (AssertionError):
        tr = MyTransform (verbose=1, different=True)
        tr2= MyTransform (verbose=1)
        tr.assert_equal (tr(1), tr2(1))

    result = tr.assert_equal (tr(1), tr2(1), raise_error=False)
    assert result is False
    remove_previous_results (path_results=path_results)

# Comes from block_types.ipynb, cell
#@pytest.mark.reference_fails
def test_set_paths ():
    def assert_paths (x, path_results, path_models):
        base = os.path.abspath('.')
        assert x.path_results==Path(f'{base}/{path_results}')
        assert x.data_io.path_results==Path(f'{base}/{path_results}')
        assert x.path_models==Path(f'{base}/{path_models}')
        assert x.data_io.path_models==Path(f'{base}/{path_models}')

    path_results = 'test_set_paths_1'
    path_models = 'test_set_paths_1'
    tr = Component (path_results=path_results)
    assert_paths (tr, path_results, path_models)
    path_results = 'test_set_paths_2'
    tr.data_io.set_path_results (path_results)
    assert_paths (tr, path_results, path_models)
    path_models='test_set_paths_models_1'
    tr.data_io.set_path_models (path_models)
    assert_paths (tr, path_results, path_models)

    path_results = 'test_set_paths_a'
    path_models = 'test_set_paths_models_a'
    tr = Component (path_results=path_results, path_models=path_models)
    assert_paths (tr, path_results, path_models)

    path_results = 'test_set_paths_b'
    tr.data_io.set_path_results (path_results)
    assert_paths (tr, path_results, path_models)

    path_models = 'test_set_paths_models_b'
    tr.data_io.set_path_models (path_models)
    assert_paths (tr, path_results, path_models)

# Comes from block_types.ipynb, cell
#@pytest.mark.reference_fails
def test_sampling_component ():
    c = SamplingComponent ()
    assert c.transform_uses_labels
    assert not hasattr(c.data_converter,'transform_uses_labels')
    c = SamplingComponent (data_converter='PandasConverter')
    assert c.data_converter.transform_uses_labels

# Comes from block_types.ipynb, cell
#@pytest.mark.reference_fails
def test_sklearn_component ():
    c = SklearnComponent ()
    assert c.data_io.fitting_load_func==joblib.load
    assert c.data_io.result_save_func==joblib.dump

# Comes from block_types.ipynb, cell
#@pytest.mark.reference_fails
def test_no_saver_component ():
    c = NoSaverComponent ()
    assert c.data_io.__class__.__name__ == 'NoSaverIO'

# Comes from block_types.ipynb, cell
#@pytest.mark.reference_fails

def get_data_for_one_class ():
    data = np.r_[np.ones ((5,2)), 2*np.ones((5,2))]
    y = np.r_[np.ones ((5,)), np.zeros((5,))]
    return data, y

def test_one_class_sklearn_component ():
    path_results = 'one_class_sklearn_component'
    remove_previous_results (path_results=path_results)

    data, y = get_data_for_one_class ()
    from sklearn.preprocessing import MinMaxScaler
    result1 = OneClassSklearnComponent (MinMaxScaler()).fit(data,y).transform (data)
    result2 = MinMaxScaler().fit(data[y==0]).transform (data)
    assert (result1==result2).all().all()

    remove_previous_results (path_results=path_results)

# Comes from block_types.ipynb, cell
#@pytest.mark.reference_fails
def test_pandas_component ():
    c = PandasComponent ()
    assert c.data_converter.__class__.__name__ == 'PandasConverter'
    assert c.data_io.__class__.__name__ == 'PandasIO'