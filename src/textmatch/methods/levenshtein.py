from ..typings import PolarsDataframe
import polars
import polars_distance

def compare(data: PolarsDataframe, header1: str, header2: str, header_degree: str) -> PolarsDataframe:
    return data.with_columns(polars.lit(1).sub(polars_distance.col(header1).dist_str.damerau_levenshtein(header2, normalized=True)).cast(polars.Float32).alias(header_degree))
