from ..typings import PolarsDataframe
import polars
import polars_ds

def ratcliff_obershelp(a: polars.Expr, b: polars.Expr) -> polars.Expr:
    a_length = a.str.len_chars()
    b_length = b.str.len_chars()
    subsequence_length = polars_ds.str_lcs_subseq(a, b).str.len_chars()
    return (2 * subsequence_length / (a_length + b_length)).fill_nan(0.0).fill_null(0.0)

def compare(data: PolarsDataframe, header1: str, header2: str, header_degree: str) -> PolarsDataframe:
    degree = ratcliff_obershelp(polars.col(header1), polars.col(header2)).cast(polars.Float32)
    return data.with_columns(degree.alias(header_degree))
