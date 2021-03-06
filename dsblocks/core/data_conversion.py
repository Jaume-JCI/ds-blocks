# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/core/data_conversion.ipynb (unless otherwise specified).

__all__ = ['DataConverter', 'NoConverter', 'GenericConverter', 'StandardConverter', 'PandasConverter',
           'Window2Dto3Dconverter', 'data_converter_factory']

# Cell
import abc
import pandas as pd
import numpy as np
import warnings

#block-types
from ..config import bt_defaults as dflt
from ..utils.utils import set_logger

# Cell
class DataConverter ():
    """
    Convert input and output data format.

    This class allows to convert the format of the data before fitting
    and before transforming, and revert the changes back after performing
    these operations. This allows to decouple the implementation of a
    particular component from the remaining components in the pipeline,
    making it more reusable across different pipelines.
    """
    def __init__ (self, logger=None, verbose: int=dflt.verbose, inplace: bool=True,
                  convert_before=None, convert_before_transforming=None, convert_before_fitting=None,
                  convert_after=None, convert_after_transforming=None, convert_after_fitting=None,
                  convert_before_transforming_after_fit=None,
                  convert_after_transforming_after_fit=None,
                  unpack_single_tuple_for_fitting=True, unpack_single_tuple_for_transforming=True,
                  unpack_single_tuple=None, unpack_single_tuple_for_result_func=False,
                  ensure_tuple=True, **kwargs):
        """
        Initialize common attributes and fields, in particular the logger.

        Parameters
        ----------
        logger : logging.Logger or None, optional
            Logger used to write messages
        verbose : int, optional
            Verbosity, 0: warning or critical, 1: info, 2: debug.
        """
        # logger used to display messages
        if logger is None:
            self.logger = set_logger ('dsblocks', verbose=verbose)
        else:
            self.logger = logger
        self.inplace = inplace
        self._set_convert_from_functions (
            convert_before=convert_before,
            convert_before_transforming=convert_before_transforming,
            convert_before_fitting=convert_before_fitting,
            convert_after=convert_after,
            convert_after_transforming=convert_after_transforming,
            convert_after_fitting=convert_after_fitting,
            convert_before_transforming_after_fit=convert_before_transforming_after_fit,
            convert_after_transforming_after_fit=convert_after_transforming_after_fit)

        unpack_single_tuple_for_fitting = (
            unpack_single_tuple if unpack_single_tuple is not None
            else unpack_single_tuple_for_fitting)
        unpack_single_tuple_for_transforming = (
            unpack_single_tuple if unpack_single_tuple is not None
            else unpack_single_tuple_for_transforming)
        self.convert_single_tuple_for_fitting = (
            self.convert_single_tuple if unpack_single_tuple_for_fitting
            else self.do_not_convert_single_tuple)
        self.convert_single_tuple_for_transforming = (
            self.convert_single_tuple if unpack_single_tuple_for_transforming
            else self.do_not_convert_single_tuple)

        self.convert_single_tuple_for_result_func = (
            self.convert_single_tuple if unpack_single_tuple_for_result_func
            else self.do_not_convert_single_tuple)

        self.convert_no_tuple = (self.convert_no_tuple if ensure_tuple
                                 else self.do_not_convert_no_tuple)

    def convert_single_tuple (self, X):
        return X[0] if (len(X)==1 and type(X[0]) is tuple) else X

    def do_not_convert_single_tuple (self, X):
        return X

    def convert_no_tuple (self, X):
        X = X if type (X) is tuple else (X,)
        return X

    def do_not_convert_no_tuple (self, X):
        return X

    def convert_varargs_to_x_y (self, X):
        assert len(X)==1 or len(X)==2
        X, y = X if len(X)==2 else (X[0], None)
        return X, y

    def convert_before_fitting (self, *X):
        """
        Convert incoming data before running fit method.

        Parameters
        ----------
        X : data (N observations x D dimensions)
            data used for fitting model parameters

        Returns
        -------
        X : data (N observations x D dimensions)
            data with transformed format but same content
        """
        return X

    def convert_after_fitting (self, *X):
        """
        Convert data after running fit method.

        Calling this method is only required when convert_before_fitting
        changes X "in place", instead of changing a copy of X. This might
        be more efficient sometimes, and we have convert_after_fitting to
        revert the previous change.

        Parameters
        ----------
        X : data (N observations x D dimensions)
            data used for fitting model parameters

        Returns
        -------
        X : data (N observations x D dimensions)
            data with transformed format but same content
        """
        return X

    def convert_before_transforming (self, *X, **kwargs):
        """
        Convert data before running transform method.

        Parameters
        ----------
        X : data (N observations x D dimensions)
            data used to be transformed

        Returns
        -------
        X : data (N observations x D dimensions)
            data with transformed format but same content
        """
        return X

    def convert_after_transforming (self, result, **kwargs):
        """
        Convert result obtained after by transform method.

        Parameters
        ----------
        result : data (N' observations x D' dimensions)
                result obtained by transformed method

        Returns
        -------
        result : data (N' observations x D' dimensions)
            result with transformed format but same content
        """
        return result

    def convert_before_fit_apply (self, *X, sequential_fit_apply=False, **kwargs):
        #return self.convert_before_fitting (*X)
        X_original = copy.deepcopy (X) if self.inplace else X
        _ = self.convert_before_transforming (
            *X_original, fit_apply=True, sequential_fit_apply=sequential_fit_apply, **kwargs)
        X = self.convert_before_fitting (*X)
        if self.inplace:
            self.X = X
        return X

    def convert_after_fit_apply (self, result, sequential_fit_apply=False, **kwargs):
        #return self.convert_after_transforming (result, **kwargs)
        if self.inplace:
            _ = self.convert_after_fitting (*self.X)
            self.X = None
        return self.convert_after_transforming (
            result, fit_apply=True, sequential_fit_apply=sequential_fit_apply, **kwargs)

    ## methods based on passed-in functions
    def _set_convert_from_functions (self, convert_before=None, convert_before_transforming=None,
                                     convert_before_fitting=None, convert_after=None,
                                     convert_after_transforming=None, convert_after_fitting=None,
                                     convert_before_transforming_after_fit=None,
                                     convert_after_transforming_after_fit=None):
        # functions
        if convert_before is not None:
            if convert_before_transforming is None: convert_before_transforming = convert_before
            if convert_before_fitting is None:
                self._convert_before_fitting = convert_before
                self.convert_before_fitting = self.convert_before_fitting_from_function
            #if convert_before_fit_apply is None: convert_before_fit_apply=convert_before

        if convert_before_transforming is not None:
            self._convert_before_transforming = convert_before_transforming
            self.convert_before_transforming = self.convert_before_transforming_from_function
            self._convert_before_transforming_after_fit = (
                self._convert_before_transforming if convert_before_transforming_after_fit is None
                else convert_before_transforming_after_fit)
        if convert_before_fitting is not None:
            self._convert_before_fitting = convert_before_fitting
            self.convert_before_fitting = self.convert_before_fitting_from_function

        if convert_after is not None:
            if convert_after_transforming is None: convert_after_transforming = convert_after
            if convert_after_fitting is None: convert_after_fitting = convert_after
        if convert_after_transforming is not None:
            self._convert_after_transforming = convert_after_transforming
            self.convert_after_transforming = self.convert_after_transforming_from_function
            self._convert_after_transforming_after_fit = (
                self._convert_after_transforming if convert_after_transforming_after_fit is None
                else convert_after_transforming_after_fit)
        if convert_after_fitting is not None:
            self._convert_after_fitting = convert_after_fitting
            self.convert_after_fitting = self.convert_after_fitting_from_function

    def convert_before_fitting_from_function (self, *X):
        return self._convert_before_fitting (*X)

    def convert_after_fitting_from_function (self, *X):
        return self._convert_after_fitting (*X)

    def convert_before_transforming_from_function (self, *X, fit_apply=False,
                                                   sequential_fit_apply=False, **kwargs):
        if fit_apply or sequential_fit_apply:
            return self._convert_before_transforming_after_fit (*X, **kwargs)
        else:
            return self._convert_before_transforming (*X, **kwargs)

    def convert_after_transforming_from_function (self, result, fit_apply=False,
                                                  sequential_fit_apply=False, **kwargs):
        if fit_apply or sequential_fit_apply:
            return self._convert_after_transforming_after_fit (result, **kwargs)
        else:
            return self._convert_after_transforming (result, **kwargs)

# Cell
class NoConverter (DataConverter):
    """Performs no conversion."""
    def __init__ (self, **kwargs):
        super().__init__(inplace=False, **kwargs)

# Cell
class GenericConverter (DataConverter):
    """
    Supply X, y to `fit`, and provide only X to `transform` / `predict` / `apply`

    Cases:
    - Usual case:
        (X, y) are provided to fit.
        Only X is provided to transform.
        Only X is returned by transform.
    - Transform uses labels:
        (X, y) are provided to fit.
        (X, y) are provided to transform.
        (X, y) are returned by transform.
    - separate_labels = False, or no_labels=True
        X is provided to fit
        X is provided to transform
        X is returned by transform
    """

    error_warning_message = 'Did not find y as separate argument, but no_labels is False'

    def __init__ (self, transform_uses_labels=False, separate_labels=True, no_labels=False,
                  labels_returned_by_transform=None, labels_to_be_returned_by_transform=None,
                  labels_included_without_fitting=False,
                  raise_error_if_no_label_inconsistency=False,
                  raise_warning_if_no_label_inconsistency=False,
                  inplace=False, **kwargs):
        """
        Initialize attributes and fields.

        Parameters
        ----------
        transform_uses_labels : bool, optional
            If True, the `transform` method receives both `X` and `y`.
            If False, the `transform` method only receives `X`.
        """

        super().__init__(inplace=False, **kwargs)

        # whether the _transform method receives a DataFrame that includes the labels, or it doesn't
        self.separate_labels = separate_labels
        self.no_labels = (not separate_labels) or no_labels
        self.transform_uses_labels = transform_uses_labels and not self.no_labels
        self.stored_y = False
        self.labels_returned_by_transform = (labels_returned_by_transform
                                             if labels_returned_by_transform is not None
                                             else self.transform_uses_labels)
        self.labels_included_without_fitting = labels_included_without_fitting
        self.labels_to_be_returned_by_transform = (
            labels_to_be_returned_by_transform if labels_to_be_returned_by_transform is not None
            else (self.transform_uses_labels or self.labels_included_without_fitting))
        self.raise_error_if_no_label_inconsistency = raise_error_if_no_label_inconsistency
        self.raise_warning_if_no_label_inconsistency = raise_warning_if_no_label_inconsistency


    def convert_before_transforming (self, *X, fit_apply=False, sequential_fit_apply=False, **kwargs):
        """
        By default, remove labels from incoming input.
        """
        self.stored_y = False
        fit_apply = fit_apply or sequential_fit_apply
        if not fit_apply and not self.labels_included_without_fitting:
            return X
        if not(self.no_labels or self.transform_uses_labels or len(X)<=1):
            self.stored_y = True
            *X, self.y = X
            #if len (X) > 1: X = tuple(X)
            X = tuple(X)
            return X
        if (fit_apply or self.transform_uses_labels) and len(X)>1:
            self.stored_y = True
            *_, self.y = X
        if not self.no_labels and not self.stored_y:
            if self.raise_error_if_no_label_inconsistency:
                raise TypeError (self.error_warning_message)
            elif self.raise_warning_if_no_label_inconsistency:
                warnings.warn (self.error_warning_message)
                print (self.error_warning_message)
        return X

    def convert_after_transforming (self, result, fit_apply=False, sequential_fit_apply=False, **kwargs):
        """
        Convert the result produced by `transform`to DataFrame format.

        If the input to `transform` was in DataFrame format, the `result`
        given by `transform` is converted to DataFrame if it is not
        produced in this format. Furthermore, if the `label` column was
        in the input to `transform` and it is not in the output given
        by `transform`, it is appended to the result.
        """
        fit_apply = fit_apply or sequential_fit_apply
        if ((not fit_apply or not self.stored_y) and
            (not self.stored_y or not self.labels_to_be_returned_by_transform or self.no_labels
            or (self.labels_returned_by_transform and (type(result) is tuple) and len(result)>1))):
            return result
        elif type(result) is tuple:
            result = result + (self.y, )
        else:
            result = (result, self.y)
        self.stored_y = False
        self.y = None
        return result

# Cell
class StandardConverter (DataConverter):
    """Convert input and output data format.

    Assumes that, when fitting, the data is introduced either as a single element or
    as a tuple with more than one element."""
    def __init__ (self, inplace=False, unpack_single_tuple=False,
                  unpack_single_tuple_for_result_func=True, **kwargs):
        """
        Initialize common attributes and fields, in particular the logger.
        """
        # logger used to display messages
        super().__init__(inplace=False, unpack_single_tuple=False,
                         unpack_single_tuple_for_result_func=True, **kwargs)

    def convert_before_transforming (self, *X, fit_apply=False, sequential_fit_apply=False, **kwargs):
        """
        Convert data before running transform method.
        """
        if ((fit_apply or sequential_fit_apply) and len(X)==2):
            X, self.y = X
        else:
            self.y = None
        return X

    def convert_after_transforming (self, result, sequential_fit_apply=False, **kwargs):
        """
        Convert result obtained after by transform method.
        """
        if sequential_fit_apply and self.y is not None:
            result = (result, self.y)
        self.y = None
        return result

# Cell
class PandasConverter (DataConverter):
    """
    Convert DataFrame to numpy array and back, if needed.

    By default, this class assumes the following:

        - When calling the fit method, the data is received
          as a DataFrame. This DataFrame contains not only the
          data to be used for fitting our model, but also the
          ground-truth labels. The `PandasConverter` takes only
          the data needed for fitting the model, and puts it
          into a matrix `X`, and then takes the labels and puts
          them into a separate vector `y`. While all this is done
          by default, the `PandasConverter` also allows other
          possibilities: receiving the data and the labels separately
          in `X` and `y`, in which case no action is needed, or avoiding
          to separate the data and the labels (if the flag `separate_labels` is False),
          in which case the matrix `X` will contain both data and labels.
          It also allows to receive numpy arrays instead of DataFrames,
          in which case the data format is preserved.

        - When calling the `transform` method, the `PandasConverter`
          removes by default the labels from the incoming DataFrame,
          and then puts them back after performing the transformation.
          This behaviour can change if we set `transform_needs_labels=True`.
          In this case, the labels are kept in the matrix `X` so that
          they can be used during the transformation. This is done in
          particular by one type of component called `SamplingComponent`,
          defined in `core.component_types`. This is useful for
          components that do some sort of under-sampling or over-sampling,
          changing the number of observations. When this occurs, the
          labels need to be adjusted accordingly, so that the `transform`
          method modifies both the data and the labels, both of whom are
          contained in the output matrix `X`.

        The  default `DataConverter` used in the current implementation is the
        `PandasConverter`.

        #### Note on generic use of metadata (to be implemented)

        In general, our DataFrames behave like a single-table in-memory DataBases
        from which we can take the necessary data and metadata to perform any
        operation needed in our pipeline. Although currently we only consider
        groundtruth labels as metadata, in the future we plan to allow any other
        metadata indicated by configuration. This includes the `chiller_id`, which
        might be needed by some of the components, to differentiate between the data of
        different chillers, for data-sets with more than one chiller. Currently
        our dataset contains a single chiller, and this type of metadata is not needed.
        Regardless of the metadata being used, the `PandasConverter` takes only the data
        needed for fitting the model, puts it into a matrix `X`, and then takes the
        labels and puts them into a separate vector `y`. The rest of the metadata is
        discarded unless the component needs it for some purpose, in which case this
        will be indicated by a parameter called something like `metadata`, which contains
        the list of columns in the DataFrame which contain the rest of metadata.
    """
    def __init__ (self, transform_uses_labels=False, transformed_index=None, transformed_columns=None,
                  separate_labels=True, inplace=False, metadata=None, **kwargs):
        """
        Initialize attributes and fields.

        Parameters
        ----------
        transform_uses_labels : bool, optional
            If True, the `transform` method receives as input data `X` a DataFrame where
            one of the columns is `label`, containing the ground-truth labels. This allows
            the transform method to modify the number of observations,
            changing the number of rows in the data and in the labels.
            See `SamplingComponent` class in `dsblocks.core.component_types`.
            If False, the input data `X` only contains data consumed by , without
            ground-truth labels.
        transformed_index : array-like or None, optional
            Used after transforming the data. If the result of the transformation is
            a numpy array, two things can happen: 1) if the number of rows of this array
            is the same as the number of rows of the input DataFrame, then we convert
            the array to a DataFrame with the same index as the original; 2) if the number
            of rows is not the same, the index used for the new DataFrame is
            `transformed_index` if provided, or 0..N-1 (where N=number of rows) if not
            provided.
        transformed_columns : array-like or None, optional
            Used after transforming the data. If the result of the transformation is
            a numpy array, two things can happen: 1) if the number of columns of this array
            is the same as the number of columns of the input DataFrame, then we convert
            the array to a DataFrame with the same columns as the original; 2) if the number
            of columns is not the same, the columns used for the new DataFrame is
            `transformed_columns` if provided, or 0..D-1 (where D=number of columns) if not
            provided.
        separate_labels : bool, optional
            Used before calling the fit method. If separate_labels=True (default value),
            the `fit` method receives the data and labels separately in `X` and `y`
            respectively. If separate_labels=False, the `fit` method receives both the
            data and the labels in the same input `X`, where the labels are in a
            column of `X` called `label` (TODO: make this configurable). This last
            option is used by the `Pipeline` class, and its rationale is provided in
            the description of that class.
        """

        super().__init__(inplace=inplace, **kwargs)

        # whether the _transform method receives a DataFrame that includes the labels, or it doesn't
        self.transform_uses_labels = transform_uses_labels

        # configuration for converting the transformed data into a DataFrame
        self.transformed_index = transformed_index
        self.transformed_columns = transformed_columns

        # whether the _fit method receives a DataFrame that includes the labels, or the labels are placed separately in y
        self.separate_labels = separate_labels

        self.metadata=metadata

    def convert_before_fitting (self, *X):
        """
        By default, convert DataFrame X to numpy arrays X and y

        The most common use of this method is:
        - When calling the fit method, the data is received
          as a DataFrame.
        - This DataFrame contains not only the data to be
          used for fitting our model, but also the
          ground-truth labels. This method takes only
          the data needed for fitting the model, and puts it
          into a matrix `X`, and then takes the labels and puts
          them into a separate vector `y`.

        Other possibilities are:
          - If the data and the labels are separated in `X` and `y`
          (i.e., X does not include labels), no action is performed.
          - If `self.separate_labels` is False, the data and the labels
          are not separated, in which case the data `X`
          passed to the fit method will contain both data and labels.
          - It also allows to receive numpy arrays instead of DataFrames,
          in which case the data format is preserved.
        """
        X, y = self.convert_varargs_to_x_y (X)
        if self.separate_labels and (type(X) is pd.DataFrame) and ('label' in X.columns):
            if y is None:
                y = X['label']
            else:
                assert (y==X['label']).all(), "discrepancy between y and X['label']"

            X = X.drop(columns='label')
            self.restore_label_fitting = True
            self.y_fitting = y
        else:
            self.restore_label_fitting = False

        if self.metadata is not None:
            self.df = X[self.metadata]
            X = X.drop(columns=self.metadata)

        return X, y

    def convert_after_fitting (self, *X):
        """Do nothing. Return same data received."""
        return X

    def convert_before_transforming (self, X, new_columns=None, **kwargs):
        """
        By default, remove labels from incoming DataFrame.

        This method allows to remove the labels from the incoming DataFrame,
        and then put them back after performing the transformation.
        This behaviour can change if we set `self.transform_needs_labels=True`.
        In this case, the labels are kept in the matrix `X` so that they can be
        used during the transformation. This is done in particular by one type of
        component called `SamplingComponent`, defined in `core.component_types`.
        This is useful for components that do some sort of under-sampling or
        over-sampling, changing the number of observations. When this occurs,
        the labels need to be adjusted accordingly, so that the `transform` method
        modifies both the data and the labels, both of whom are contained in the output
        matrix `X`.


        """
        if new_columns is None:
            new_columns = self.transformed_columns
        self.new_columns = new_columns
        if (type(X) is pd.DataFrame) and ('label' in X.columns) and (not self.transform_uses_labels):
            y = X['label']
            X = X.drop(columns='label')
            self.restore_label_transform = True
            self.y_transform = y
        else:
            self.restore_label_transform = False

        if self.metadata is not None:
            self.df = X[self.metadata]
            X = X.drop(columns=self.metadata)

        self.type_X = type(X)
        if self.type_X is pd.DataFrame:
            self.X_shape = X.shape
            self.X_index = X.index
            self.X_columns = X.columns
            if 'label' in self.X_columns:
                self.X_label = X['label']

        return X

    def convert_after_transforming (self, result, **kwargs):
        """
        Convert the result produced by `transform`to DataFrame format.

        If the input to `transform` was in DataFrame format, the `result`
        given by `transform` is converted to DataFrame if it is not
        produced in this format. Furthermore, if the `label` column was
        in the input to `transform` and it is not in the output given
        by `transform`, it is appended to the result.
        """

        result = self.convert_to_dataframe (result)
        if self.restore_label_transform:
            if type(result) is pd.DataFrame:
                if 'label' in result.columns:
                    self.logger.warning ('label already part of result')
                result['label'] = self.y_transform
            else:
                self.logger.warning ('result is not DataFrame')

        if self.metadata is not None:
            result[self.metadata] = self.df
            del self.df

        return result

    def convert_to_dataframe (self, result):
        """Convert the `result` produced by `transform`to DataFrame format."""

        if self.type_X is pd.DataFrame:
            if type(result) is np.ndarray or type(result) is pd.Series:
                if result.shape[0] == self.X_shape[0]:
                    index = self.X_index
                else:
                    index = self.transformed_index if (self.transformed_index is None) else range(result.shape[0])
                if (result.ndim > 1) and (result.shape[1] == self.X_shape[1]):
                    columns = self.X_columns
                else:
                    columns = self.new_columns if (self.new_columns is not None) else range(result.shape[1]) if (result.ndim > 1) else [0]

                result = pd.DataFrame (result, index=index, columns=columns)
            elif (type(result) is pd.DataFrame and self.new_columns is not None and
                  result.shape[1]==len(self.new_columns) and not (result.columns==self.new_columns).all()):
                result.columns = self.new_columns

            if type(result) is pd.DataFrame:
                if ('label' in self.X_columns) and ('label' not in result.columns):
                    self.logger.info ('label column not found in result, but found in input DataFrame')
                    result['label'] = self.X_label
        return result

# Cell
class Window2Dto3Dconverter (DataConverter):
    """Convert sequence of windows from WindowGenerator's 2D format to 3D.

    Given a 2D Dataframe of size N x (W*D), where N=number of windows,
    D=number of variables (dimensions), and W=size of windows, converts this
    to a numpy array of N x D x W. Note that the order of the elements is
    transposed: for each window, the has first the elements of a window in
    one dimension, then the elements in the second dimension, etc. This
    is transposed in the output to have the second and third axis be D and W
    respectively.
    """
    def __init__ (self, sequence_length: int, data_converter: DataConverter = None, **kwargs):
        """
        Initialize common attributes and fields.

        Parameters
        ----------
        sequence_length : int
            Size of each window.
        data_converter : DataConverter, optional
            DataConverter that will transform the input data to a 2D DataFrame of
            size N x (D*W), if it is not already in this format. PandasConverter
            is used by default.
        """
        self.sequence_length = sequence_length
        if data_converter is None:
            self.data_converter = PandasConverter (**kwargs)
        else:
            self.data_converter = data_converter
        super ().__init__ (inplace=self.data_converter.inplace, **kwargs)

    def convert_before_fitting (self, X, y=None):
        """
        Convert incoming data before running fit method.

        Parameters
        ----------
        X : data (N observations x D dimensions)
            data used for fitting model parameters
        y : labels (N observations), optional
            One dimensional array with N groundtruth labels.

        Returns
        -------
        X : data (N observations x D dimensions)
            data with transformed format but same content
        y : labels (N observations)
            labels with transformed format but same content
        """
        X, y = self.data_converter.convert_before_fitting (X, y)
        X = self.transform (X)
        return X, y

    def convert_after_fitting (self, X):
        """
        Convert data after running fit method.

        Calling this method is only required when convert_before_fitting
        changes X "in place", instead of changing a copy of X. This might
        be more efficient sometimes, and we have convert_after_fitting to
        revert the previous change.

        Parameters
        ----------
        X : data (N observations x D dimensions)
            data used for fitting model parameters

        Returns
        -------
        X : data (N observations x D dimensions)
            data with transformed format but same content
        """
        return self.data_converter.convert_after_fitting (X)

    def convert_before_transforming (self, X, **kwargs):
        """
        Convert data before running transform method.

        Parameters
        ----------
        X : data (N observations x D dimensions)
            data used to be transformed

        Returns
        -------
        X : data (N observations x D dimensions)
            data with transformed format but same content
        """
        X = self.data_converter.convert_before_transforming (X, **kwargs)
        X = self.transform (X)
        return X

    def convert_after_transforming (self, result, **kwargs):
        """
        Convert result obtained after by transform method.

        Parameters
        ----------
        result : data (N' observations x D' dimensions)
                result obtained by transformed method

        Returns
        -------
        result : data (N' observations x D' dimensions)
            result with transformed format but same content
        """
        result = self.inverse_transform (result)
        result = self.data_converter.convert_after_transforming (result, **kwargs)
        return result

    def transform (self, df):
        """
        Convert input DataFrame `df` to numpy array in 3D format.

        Given a 2D Dataframe of size N x (W*D), where N=number of windows,
        D=number of variables (dimensions), and W=size of windows, converts this
        to a numpy array of N x D x W. Note that the order of the elements is
        transposed: for each window, the has first the elements of a window in
        one dimension, then the elements in the second dimension, etc. This
        is transposed in the output to have the second and third axis be D and W
        respectively.
        """
        data = df.values.reshape(df.shape[0], -1, self.sequence_length)
        data = np.transpose(data, (0,2,1))
        return data

    def inverse_transform (self, data):
        """
        Convert 3D numpy array `data` to 2D DataFrame.

        Given a 3D numpy array of size N x D x W, convert this to Dataframe
        of size N x (W*D), where N=number of windows, D=number of variables
        (dimensions), and W=size of windows. Note that the order of the
        elements is transposed: for each window, the output provides first
        the elements of the first variable across the time-steps of the window,
        then the elements of the second variable, etc.
        """
        data = np.transpose (data, (0,2,1))
        data = data.reshape (data.shape[0], -1)
        return data

# Cell
def data_converter_factory (converter,
                            *args,
                            **kwargs):
    if type(converter) is str:
        cls = eval(converter)
    elif type(converter) is type:
        cls = converter
    elif isinstance (converter, DataConverter):
        return converter
    else:
        raise ValueError (f'invalid converter {converter}, must be str, class or object instance of DataConverter')
    return cls(*args, **kwargs)