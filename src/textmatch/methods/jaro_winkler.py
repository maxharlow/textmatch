from ..typings import PolarsDataframe
import polars
import polars_ds

def compare(data: PolarsDataframe, header1: str, header2: str, header_degree: str) -> PolarsDataframe:
    return data.with_columns(polars_ds.str_jw(polars.col(header1), polars.col(header2), parallel=True).cast(polars.Float32).alias(header_degree))
