# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/utils/nbdev_utils.ipynb (unless otherwise specified).

__all__ = ['cd_root', 'nbdev_setup', 'TestRunner', 'replace_imports', 'nbdev_build_test']

# Cell
import os
import shutil
import joblib
import re
from pathlib import Path
import socket
from configparser import ConfigParser

# Cell
def cd_root ():
    max_count=10
    while not os.path.exists('settings.ini'):
        os.chdir('..')
        max_count = max_count - 1
        if max_count <= 0:
            break

# Cell
def nbdev_setup (no_warnings=True):
    if no_warnings:
        from warnings import filterwarnings
        filterwarnings("ignore")
    cd_root ()

# Cell
class TestRunner ():
    def __init__ (self, do_all=False, do_test=None, all_tests=None, tags=None, targets=None,
                  remote_targets=None, load=False, save=True, path_config='config_test/test_names.pk',
                  localhostname=None, show=True):

        if save:
            Path(path_config).parent.mkdir(parents=True, exist_ok=True)

        if load and Path(path_config).exists():
            do_test_, all_tests_, tags_, targets_, remote_targets_, localhostname_ = joblib.load (path_config)
            do_test = do_test_ if do_test is None else do_test
            all_tests = all_tests_ if all_tests is None else all_tests
            tags = tags_ if tags is None else tags
            targets = targets_ if targets is None else targets
            remote_targets = remote_targets_ if remote_targets is None else remote_targets
            localhostname = localhostname_ if localhostname is None else localhostname
        else:
            do_test = [] if do_test is None else do_test
            all_tests = [] if all_tests is None else all_tests
            tags = {} if tags is None else tags
            targets = [] if targets is None else targets
            remote_targets = ['dummy'] if remote_targets is None else remote_targets
            localhostname = 'DataScience-VMs-03' if localhostname is None else localhostname

        if not isinstance(targets, list):
            targets = [targets]

        self.do_test = do_test
        self.all_tests = all_tests
        self.tags = tags
        self.do_all = do_all
        self.targets = targets
        self.save = save
        self.path_config = path_config
        self.hostname = socket.gethostname()
        self.localhostname = localhostname
        self.remote_targets = remote_targets
        self.is_remote = self.localhostname != self.hostname
        self.show = show
        self.storage = {}

    def get_data (self, data_func, *args, store=False, **kwargs):
        name = data_func.__name__
        if name in self.storage:
            data = self.storage[name]
        else:
            data = data_func(*args, **kwargs)
            if store:
                self.storage[name] = data
        return data

    def run (self, test_func, data_func=None, do=False, include=False, debug=False,
            exclude=False, tag=None, show=None, store=False):
        name = test_func.__name__
        show = self.show if show is None else show
        if (name not in self.all_tests) and not exclude:
            self.all_tests.append (name)
        if include and name not in self.do_test:
            self.do_test.append (name)
        if tag is not None:
            if tag in self.tags and name not in self.tags[tag]:
                self.tags[tag].append(name)
            else:
                self.tags[tag] = [name]
        if self.save:
            joblib.dump ([self.do_test, self.all_tests, self.tags, self.targets,
                         self.remote_targets, self.localhostname], self.path_config)
        targets = self.remote_targets if self.is_remote else self.targets
        if ((name in self.do_test) or do or (self.do_all and not exclude) or
            (tag is not None) and (tag in targets)):
            if data_func is not None:
                data = self.get_data (data_func, store=store)
                args = [data]
            else:
                args = []
            if debug:
                import pdb
                pdb.runcall (test_func, *args)
            else:
                if show:
                    print (f'running {name}')
                test_func (*args)

# Cell
def replace_imports (path_file, library_name):
    file = open (path_file, 'rt')
    text = file.read ()
    file.close ()
    text = re.sub (r'from \.+', f'from {library_name}.', text)

    file = open (path_file, 'wt')
    file.write (text)
    file.close ()

# Cell
def nbdev_build_test (library_name=None, test_folder='tests'):
    cd_root ()
    if (library_name is None) or (test_folder is None):
        config = ConfigParser(delimiters=['='])
        config.read('settings.ini')
        cfg = config['DEFAULT']
    if library_name is None:
        library_name = cfg['lib_name']
    if test_folder is None:
        test_folder = cfg['test_path']
    print (f'moving {library_name}/{test_folder} to root path: {os.getcwd()}')
    if os.path.exists (test_folder):
        print (f'{test_folder} exists, removing it')
        shutil.rmtree (test_folder)
    shutil.move (f'{library_name}/{test_folder}', '.')
    for root, dirs, files in os.walk(test_folder, topdown=False):
        for name in files:
            if name.endswith('.py'):
                print (f'replacing imports in {os.path.join(root, name)}')
                replace_imports (os.path.join(root, name), library_name)