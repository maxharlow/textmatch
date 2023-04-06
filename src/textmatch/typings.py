from typing import Optional, Callable, Union, TypeAlias, TypeVar
import polars
import pyarrow # transitive dependency of polars
import pandas # transitive dependency of polars
import dedupe._typing

PolarsDataframe: TypeAlias = polars.DataFrame
ArrowDataframe: TypeAlias = pyarrow.Table
PandasDataframe: TypeAlias = pandas.DataFrame

DedupeVariable = dedupe._typing.VariableDefinition
DedupeLabels = dedupe._typing.TrainingData

TextmatchSource: TypeAlias = dict[str, str] | PolarsDataframe | ArrowDataframe | PandasDataframe
TextmatchBlocks: TypeAlias = list[tuple[int, dict[str, str], dict[str, str], list[str], str, float]]
TextmatchProgress: TypeAlias = Optional[Callable[[str, int], Callable[[], None]]]
TextmatchAlert: TypeAlias = Optional[Callable[[str, Optional[str]], None]]
TextmatchTicker: TypeAlias = Callable[[int], Optional[Callable[[], None]]]

I = TypeVar('I')
