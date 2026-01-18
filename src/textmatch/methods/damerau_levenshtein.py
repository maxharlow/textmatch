from ..typings import PolarsDataframe
import polars
import polars_ds

def compare(data: PolarsDataframe, header1: str, header2: str, header_degree: str) -> PolarsDataframe:
    degree = polars_ds.str_d_leven(polars.col(header1), polars.col(header2), return_sim=True, parallel=True).cast(polars.Float32)
    return data.with_columns(degree.alias(header_degree))
