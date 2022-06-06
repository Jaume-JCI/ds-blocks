# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/00_tests/core/tst.utils.ipynb (unless otherwise specified).

__all__ = ['test_get_specific_data_io_parameters', 'DummyComponent', 'test_data_io_folder', 'dummy_component',
           'test_data_io_chaining', 'test_data_io_factory', 'test_profiler', 'MyTransformComparator', 'test_comparator',
           'test_comparator2']

# Cell
import pytest
import os
import joblib
from IPython.display import display
import pandas as pd
import numpy as np
import time
from pathlib import Path

from dsblocks.core.utils import *
from dsblocks.utils.utils import remove_previous_results
import dsblocks.config.bt_defaults as dflt
from dsblocks.core.components import Component

# Cell
#@pytest.fixture (name='example_people_data')
#def example_people_data_fixture():
#    return example_people_data()

# Comes from components.ipynb, cell
def test_get_specific_data_io_parameters ():
    component = Component ()
    config = component.get_specific_data_io_parameters (
        'data', **dict(x=3, par=[1,2], path_results='hello', path_results_data='world', other='yes',
                       load_result_data = True))
    assert config == dict (path_results='world', load_result=True)

# Comes from utils.ipynb, cell
#@pytest.mark.my_mark
class DummyComponent:
    def __init__ (self, **kwargs):
        self.name = 'my_component'
    def obtain_config_params (self, **kwargs):
        return kwargs

dummy_component = DummyComponent ()

def test_data_io_folder ():
    d = DataIO (component=dummy_component)
    assert d.folder==''

    assert d.get_path_result_file () is None
    assert d.get_path_model_file () is None

    d = DataIO (component=dummy_component,
            path_results ='/path/to/results',
            path_models='/other_path/example')
    assert d.get_path_result_file () == Path('/path/to/results/whole/my_component_result.pk')

    assert d.get_path_model_file () == Path('/other_path/example/models/my_component_estimator.pk')

    d.folder = 'my_folder'
    assert d.get_path_result_file () == Path('/path/to/results/my_folder/whole/my_component_result.pk')

    assert d.get_path_model_file () == Path('/other_path/example/my_folder/models/my_component_estimator.pk')

# Comes from utils.ipynb, cell
#@pytest.mark.my_mark
def test_data_io_chaining ():
    d = DataIO (component=dummy_component)
    d.chain_folders ('first')
    assert d.folder=='first'
    d.chain_folders ('second')
    assert d.folder=='second/first'
    d.chain_folders ('third')
    assert d.folder=='third/second/first'

    d.folder

    d.chain_folders ('')
    assert d.folder=='third/second/first'

    d = DataIO (component=dummy_component)
    d.chain_folders ('')
    assert d.folder==''

    d = DataIO (component=dummy_component, folder='new')
    d.chain_folders ('')
    assert d.folder=='new'
    d.chain_folders ('other')
    assert d.folder=='other/new'

    d = DataIO (component=dummy_component, folder='new',
                path_results ='/path/to/results',
                path_models='/other_path/example')
    d.chain_folders ('other')

    assert d.get_path_result_file () == Path('/path/to/results/other/new/whole/my_component_result.pk')

    assert d.get_path_model_file () == Path('/other_path/example/other/new/models/my_component_estimator.pk')

    d = DataIO (component=dummy_component, folder='__class__',
                path_results ='/path/to/results',
                path_models='/other_path/example')
    d.chain_folders ('other')
    assert d.folder == 'other/my_component'

# Comes from utils.ipynb, cell
#@pytest.mark.reference_fails
def test_data_io_factory ():
    data_io = data_io_factory ('NoSaverIO', force_save=False, save=True)
    assert type(data_io) is NoSaverIO
    assert data_io.save_flag is False

    data_io = data_io_factory ('NoSaverIO', force_save=True, save=True)
    assert type(data_io) is NoSaverIO
    assert data_io.save_flag is True

# Comes from utils.ipynb, cell
#@pytest.mark.reference_fails
def test_profiler ():
    class A():
        def __init__ (self, name='comp_a', time=1, hierarchy_level=0, **kwargs):
            self.name = name
            self.time = time
            self.hierarchy_level = hierarchy_level
            self.profiler = Profiler (self, **kwargs)
        def apply (self, split='test', method='apply'):
            self.profiler.start_timer ()
            self.profiler.start_no_overhead_timer ()
            time.sleep(self.time)
            self.profiler.finish_no_overhead_timer (method, split)
            time.sleep(self.time/10)
            self.profiler.finish_timer (method, split)
        def fit (self, split='training', method='fit'):
            self.profiler.start_timer ()
            self.profiler.start_no_overhead_timer ()
            time.sleep(self.time*2)
            self.profiler.finish_no_overhead_timer (method, split)
            time.sleep(self.time/10)
            self.profiler.finish_timer (method, split)

    a = A(name='comp_a', time=0.25)
    a.fit ()
    a.apply ()
    display(a.profiler.times['sum'])

    #assert np.floor(a.profiler.times.sum.loc['fit','training']*10)==5 and np.floor(a.profiler.times.sum.loc['apply','test']*100)==28
    assert a.profiler.times.number.loc['fit','training']==1.0 and a.profiler.times.number.loc['apply','test']==1.0

    a.apply ()

    #assert np.floor(a.profiler.times.sum.loc['fit','training']*10)==5 and np.floor(a.profiler.times.sum.loc['apply','test']*100)==55
    assert a.profiler.times.number.loc['fit','training']==1.0 and a.profiler.times.number.loc['apply','test']==2.0
    assert np.isnan(a.profiler.times.number.loc['fit','test']) and np.isnan(a.profiler.times.number.loc['apply','training'])

    df = a.profiler.retrieve_times(is_leaf=True)

    #assert float(np.floor(df.avg.loc[:,('test','apply')]*100))==27

    #assert float(np.floor(df.sum.loc[:,('test','apply')]*100))==55

    assert ((df.max >= df.min) | df.max.isna()).all().all()

    assert (df.max.loc[:,('test','apply')] > df.min.loc[:,('test','apply')]).all()

    b = A(name='comp_b', time=0.30)
    b.apply (split='validation', method='fit_apply')
    b.fit ()

    df = a.profiler.retrieve_times(is_leaf=True)
    df2 = b.profiler.retrieve_times(is_leaf=True)
    dfd = b.profiler.combine_times ([df, df2])
    display(dfd.avg)

    assert dfd.avg.shape==(2,8)
    assert (dfd.avg.index.get_level_values(0)==[0,0]).all()
    assert (dfd.avg.index.get_level_values(1)==['comp_a', 'comp_b']).all()

# Comes from utils.ipynb, cell
#@pytest.mark.reference_fails
class MyTransformComparator ():
    def __init__ (self, noise=1e-10, different = False, **kwargs):
        self.noise = noise
        self.different = different
        self.name = 'mine'
        self.logger = None
        self.data_io = None

    def _generate_noise (self):
        while True:
            noise = np.random.rand() * self.noise
            if noise > self.noise/10:
                break
        return noise

    def __call__ (self):
        df = pd.DataFrame ([[1.0,2.0],[3.0,4.0]], columns=['a','b']) + self._generate_noise ()
        if self.different:
            df = df+10
        x = np.array([[10.0,20.0],[30.0,40.0]]) + self._generate_noise ()
        result = dict(sequence=[[1.0,2.0], x+1, dict(vector=x, data=df)],
                      array=x+10)
        return result

def test_comparator ():
    tr = MyTransformComparator ()
    tr2= MyTransformComparator ()
    comp = Comparator (tr)
    result = comp.compare (tr(), tr2())
    assert len(result)==0

    tr2= MyTransformComparator (different=True)
    result = comp.compare (tr(), tr2())
    print (result)
    assert len(result)>0

    tr2= MyTransformComparator (noise=1e-10)
    result = comp.compare (tr(), tr2())
    assert len(result)==0

    tr2= MyTransformComparator (noise=1e-1)
    result = comp.compare (tr(), tr2())
    print(result)
    assert len(result)>0

# Comes from utils.ipynb, cell
#@pytest.mark.reference_fails
def test_comparator2 ():
    comp = Comparator ()
    X = np.array([1,2,3])
    Y = np.array([1,2,3])
    comp.assert_equal (X, Y)

    #os.makedirs ('test_comparator2')
    #joblib.dump (X, 'test_comparator2/res1.pk')
    #joblib.dump (Y, 'test_comparator2/res1.pk')
    comp.assert_equal (X, Y, data_io='PickleIO', name='res')