from ..typings import PolarsDataframe
import polars
import polars_ds

def compare(data: PolarsDataframe, header1: str, header2: str, header_degree: str) -> PolarsDataframe:
    column1_length = polars.col(header1).str.len_chars()
    column2_length = polars.col(header2).str.len_chars()
    subsequence_length = polars_ds.str_lcs_subseq(polars.col(header1), polars.col(header2)).str.len_chars()
    degree = (2 * subsequence_length / (column1_length + column2_length)).fill_nan(0.0).fill_null(0.0).cast(polars.Float32)
    return data.with_columns(degree.alias(header_degree))
