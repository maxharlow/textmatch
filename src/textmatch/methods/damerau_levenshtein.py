from ..typings import PolarsDataframe
import polars
import polars_ds

def damerau_levenshtein(a: polars.Expr, b: polars.Expr) -> polars.Expr:
    return polars_ds.str_d_leven(a, b, return_sim=True, parallel=True).cast(polars.Float32)

def compare(data: PolarsDataframe, header1: str, header2: str, header_degree: str) -> PolarsDataframe:
    degree = damerau_levenshtein(polars.col(header1), polars.col(header2))
    return data.with_columns(degree.alias(header_degree))
