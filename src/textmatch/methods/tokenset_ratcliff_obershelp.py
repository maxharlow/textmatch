from ..typings import PolarsDataframe
from .ratcliff_obershelp import ratcliff_obershelp
import polars

def compare(data: PolarsDataframe, header1: str, header2: str, header_degree: str) -> PolarsDataframe:
    # tokenise and deduplicate to get the unique token sets
    set1 = polars.col(header1).str.split(' ').list.eval(polars.element().filter(polars.element().str.len_chars() > 0)).list.unique()
    set2 = polars.col(header2).str.split(' ').list.eval(polars.element().filter(polars.element().str.len_chars() > 0)).list.unique()
    # derive the intersection and remainders, then sort them
    intersection = set1.list.set_intersection(set2).list.sort()
    remainder1 = set1.list.set_difference(intersection).list.sort()
    remainder2 = set2.list.set_difference(intersection).list.sort()
    # create strings for comparison
    t0 = intersection.list.join(' ')
    t1 = polars.concat_list([intersection, remainder1]).list.join(' ')
    t2 = polars.concat_list([intersection, remainder2]).list.join(' ')
    # triple max comparison
    comparison1 = ratcliff_obershelp(t0, t1)
    comparison2 = ratcliff_obershelp(t0, t2)
    comparison3 = ratcliff_obershelp(t1, t2)
    degree = polars.max_horizontal(comparison1, comparison2, comparison3).cast(polars.Float32)
    return data.with_columns(degree.alias(header_degree))
