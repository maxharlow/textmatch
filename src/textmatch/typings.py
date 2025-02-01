from typing import Protocol, Callable, Optional
import polars
import pyarrow # transitive dependency of polars
import pandas # transitive dependency of polars
import dedupe._typing

type PolarsDataframe = polars.DataFrame
type ArrowDataframe = pyarrow.Table
type PandasDataframe = pandas.DataFrame

type DedupeLabelledData = dedupe._typing.TrainingData

type Source = dict[str, str] | PolarsDataframe | ArrowDataframe | PandasDataframe
type Blocks = list[tuple[int, dict[str, str], dict[str, str], list[str], str, float]]
type Ticker = Callable[[int], Optional[Callable[[], None]]]
type Progress = Callable[[str, int], Callable[[], None]]

class Alert(Protocol):
    def __call__(self, message: str, *, importance: Optional[str] = None) -> None: ...
