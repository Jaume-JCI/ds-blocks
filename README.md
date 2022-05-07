# DS Blocks
> Write highly modular, compact, and decoupled data science pipelines.


`ds-blocks` makes it easy to write highly modular and compact data science pipelines. It is based on a generalization of the well-known scikit-learn pipeline design, enriching and extending them in multiple ways. By doing so, `ds-blocks` makes it possible to express the ML solution in terms of independent building blocks that can be easily moved around and reused to create different solutions. At the same time, `ds-blocks` makes it possible to write concise code by automatically taking care of common steps that are needed when buildling a data science pipeline, resulting in a significant reduction of boiler-plate code.

The following are a selectiong of some of the features provided by `ds-blocks`:

- Automatize common steps that are usually present in ML code, including common caching / loading of intermediate results across the entire pipeline, logging, profiling, conversion of data to appropriate format, and more. 

- Make it possible to easily show statistics and other types of information about the output of each component in the pipeline, print a summary of the pipeline, plot a diagram of the components, and show the dimensionality of the output provided by each component. 

- Extend scikit-learn pipelines in several ways, including: i) make it possible to use any data type in the communication between components. This is done through data conversion layers that facilitate reusing the components across different pipelines, regardless of the data format used by rest of the components. In particular, two important data types enabled in `ds-blocks` are DataFrames and dictionaries. Using pandas DataFrame is suitable for many data science problems such as time-series analysis, making it easy to visualize different periods of time, subsets of variables and categories (i.e., normal vs anomaly). While standard scikit-learn components accept DataFrame as input data type, the output is always provided as a numpy array, making it necessary to manually convert the output back to the original DataFrame format every time, with the corresponding proliferation of boiler-plate code. `ds-blocks` enables a consistent use of DataFrames across the whole pipeline: when the input is a DataFrame, the output will be a DataFrame  as well, and when the input is a numpy array the output is a numpy array.

- Enable the use of sampling components that not only change the variables (or columns) but also change the number of observations (or rows), by either under-sampling or over-sampling. This is not supported by standard scikit-learn components. 

For further details, please see the [documentation](https://jaume-jci.github.io/ds-blocks/)

## Install

pip install dsblocks

## Documentation

Documentation can be found [here](https://jaume-jci.github.io/ds-blocks/)
