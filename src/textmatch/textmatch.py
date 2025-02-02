from typing import Callable, Optional, cast
import importlib.resources
import re
import unidecode
import polars

from .typings import (
    PolarsDataframe,
    PandasDataframe,
    ArrowDataframe,
    Source,
    Blocks,
    Ticker,
    Progress,
    Alert
)

def run(source1: Source,
        source2: Source,
        fields1: Optional[list[list[str]]] = None,
        fields2: Optional[list[list[str]]] = None,
        ignores: list[list[str]] = [[]],
        methods: list[str] = ['literal'],
        thresholds: list[float] = [0.6],
        output: Optional[list[str]] = None,
        join: str = 'inner',
        progress: Optional[Progress] = None,
        alert: Optional[Alert] = None) -> ArrowDataframe:
    data1 = use(source1)
    data2 = use(source2)
    data1, columnmap1 = disambiguate(data1, 'data1')
    data2, columnmap2 = disambiguate(data2, 'data2')
    fields1 = fields1 if fields1 else [list(columnmap1.keys())]
    fields2 = fields2 if fields2 else [list(columnmap2.keys())]
    blocks_number = max(len(fields1), len(fields2), len(ignores), len(methods))
    indexes = range(blocks_number)
    fields1 = fix(fields1, blocks_number)
    fields2 = fix(fields2, blocks_number)
    for fieldset in fields1:
        for field in fieldset:
            if field not in columnmap1.keys(): raise Exception(f'{field}: field not found')
            if data1.schema[columnmap1[field]] != polars.String: raise Exception(f'{field}: field is not a string')
    for fieldset in fields2:
        for field in fieldset:
            if field not in columnmap2.keys(): raise Exception(f'{field}: field not found')
            if data2.schema[columnmap2[field]] != polars.String: raise Exception(f'{field}: field is not a string')
    for fieldpairs1, fieldpairs2 in zip(fields1, fields2):
        if len(fieldpairs1) != len(fieldpairs2): raise Exception('both inputs must have the same number of fields specified')
    headers1 = [[columnmap1[field] for field in fieldset] for fieldset in fields1]
    headers2 = [[columnmap2[field] for field in fieldset] for fieldset in fields2]
    fieldmaps1 = [dict([(fields1[i][j], value) for j, value in enumerate(fieldslist)]) for i, fieldslist in enumerate(headers1)]
    fieldmaps2 = [dict([(fields2[i][j], value) for j, value in enumerate(fieldslist)]) for i, fieldslist in enumerate(headers2)]
    ignores_fixed = fix(ignores, blocks_number)
    methods_fixed = fix(methods, blocks_number)
    thresholds_fixed = fix(thresholds, blocks_number)
    blocks = list(zip(indexes, fieldmaps1, fieldmaps2, ignores_fixed, methods_fixed, thresholds_fixed))
    if alert:
        for block in blocks:
            (index, fieldmap1, fieldmap2, ignoreset, method, threshold) = block
            plan_index = f'({index + 1}) ' if len(blocks) > 1 else ''
            plan_method = method.capitalize() + (f' {threshold}' if method in {'levenshtein', 'jaro', 'bilenko'} else '')
            plan_ignore = ' – ignoring ' + ', '.join(ignoreset) if len(ignoreset) > 0 else ''
            plan_fields = ', '.join(f'"{a}" × "{b}"' for a, b in zip(fieldmap1.keys(), fieldmap2.keys()))
            alert(f'{plan_index}{plan_method} match{plan_ignore}: {plan_fields}')
    matches = match(data1, data2, blocks, progress, alert)
    outputs = supplement(join, data1, data2, matches)
    results = format(outputs, columnmap1, columnmap2, output, alert)
    return results.to_arrow()

def use(source: Source) -> PolarsDataframe:
    form = str(type(source)).split('\'')[1]
    if form == 'dict':
        return polars.from_dict(cast(dict, source))
    elif form == 'polars.dataframe.frame.DataFrame':
        return cast(PolarsDataframe, source)
    elif form == 'pyarrow.lib.Table':
        return cast(PolarsDataframe, polars.from_arrow(source))
    elif form == 'pandas.core.frame.DataFrame':
        return polars.from_pandas(cast(PandasDataframe, source))
    else:
        raise Exception('unknown data format')

def disambiguate(data: PolarsDataframe, name: str) -> tuple[PolarsDataframe, dict[str, str]]:
    columns = data.columns
    if len(columns) != len(set(columns)):
        number = 'first' if name == 'data1' else 'second'
        raise Exception(f'{number} dataset has duplicate headers')
    columnlist = [(column, f'_{name}_col{i}') for i, column, in enumerate(columns)]
    for column, identifier in columnlist:
        data = data.rename({column: identifier})
    data = data.with_row_index(f'_{name}_id')
    return data, dict(columnlist)

def fix[I](items: list[I], length: int) -> list[I]:
    if len(items) < length:
        return items + [items[-1]] * (length - len(items))
    else: # assumes items can't be longer than length
        return items

def match(
        data1: PolarsDataframe,
        data2: PolarsDataframe,
        blocks: Blocks,
        progress: Optional[Progress],
        alert: Optional[Alert],
        parent: Optional[PolarsDataframe] = None) -> PolarsDataframe:
    if len(blocks) == 0:
        if parent is None: raise Exception('nothing to match') # should never happen
        return parent # exit recursion
    (index, fieldmap1, fieldmap2, ignores, method, threshold) = blocks[0]
    if threshold < 0 or threshold > 1:
        raise Exception('threshold must be between 0.0 and 1.0 (inclusive)')
    if parent is not None: # filter down to only rows which are contained within the parent
        parent_data1_ids = parent.select('_data1_id').unique('_data1_id')
        parent_data2_ids = parent.select('_data2_id').unique('_data2_id')
        data1 = parent_data1_ids.join(data1, on='_data1_id', how='left')
        data2 = parent_data2_ids.join(data2, on='_data2_id', how='left')
    for header in fieldmap1.values(): data1 = ignorance(data1, header, ignores, index)
    for header in fieldmap2.values(): data2 = ignorance(data2, header, ignores, index)
    progress_text = f'{method.capitalize()} matching...' if parent is None and len(blocks) == 1 else f'({index + 1}) {method.capitalize()} matching...'
    def ticker(total: int) -> Optional[Callable[[], None]]:
        if progress is None: return None
        return progress(progress_text, total)
    match method:
        case 'literal':
            matches = match_apply(None, data1, data2, fieldmap1, fieldmap2, index, ticker)
        case 'levenshtein':
            from .methods import levenshtein
            function = levenshtein.compare
            matches = match_compare(function, data1, data2, fieldmap1, fieldmap2, threshold, index, ticker)
        case 'jaro':
            from .methods import jaro
            function = jaro.compare
            matches = match_compare(function, data1, data2, fieldmap1, fieldmap2, threshold, index, ticker)
        case 'metaphone':
            from .methods import metaphone
            function = metaphone.apply
            matches = match_apply_double(function, data1, data2, fieldmap1, fieldmap2, index, ticker)
        case 'bilenko':
            from .methods import bilenko
            function = bilenko.execute
            matches = function(data1, data2, fieldmap1, fieldmap2, threshold, index, ticker, alert)
        case _:
            raise Exception(f'{method}: method does not exist')
    if len(matches) == 0: return matches # exit early
    block_id = f'_block{index}_id'
    parent_block_id = f'_block{index - 1}_id'
    parent_block_degree = f'_block{index - 1}_degree'
    matches = matches.with_columns(polars.format('{}-{}', '_data1_id', '_data2_id').alias(block_id))
    child = matches.join(parent.select(polars.col([parent_block_id, parent_block_degree])), left_on=block_id, right_on=parent_block_id, how='inner') if parent is not None else matches
    return match(data1, data2, blocks[1:], progress, alert, child) # recursion

def match_apply(
        function: Optional[Callable[[str], str]],
        data1: PolarsDataframe,
        data2: PolarsDataframe,
        fieldmap1: dict[str, str],
        fieldmap2: dict[str, str],
        index: int,
        ticker: Ticker) -> PolarsDataframe:
    tick = ticker(2) # no way to do this live, so just have two ticks, before and after the join
    def application(data, header_ignorant, header_applied):
        if function is None: return data.with_columns(polars.col(header_ignorant).alias(header_applied))
        data = data.with_columns(polars.col(header_ignorant).map_elements(function, polars.String).alias(header_applied))
        return data
    headerset1_ignorant = [f'_block{index}{header}_ignorant' for header in fieldmap1.values()]
    headerset2_ignorant = [f'_block{index}{header}_ignorant' for header in fieldmap2.values()]
    headerset1_applied = [f'_block{index}{header}_applied' for header in fieldmap1.values()]
    headerset2_applied = [f'_block{index}{header}_applied' for header in fieldmap2.values()]
    for header_ignorant, header_applied in zip(headerset1_ignorant, headerset1_applied):
        data1 = application(data1, header_ignorant, header_applied)
    for header_ignorant, header_applied in zip(headerset2_ignorant, headerset2_applied):
        data2 = application(data2, header_ignorant, header_applied)
    if tick: tick()
    joined = data2.join(data1, left_on=headerset2_applied, right_on=headerset1_applied, how='inner')
    joined = joined.with_columns(polars.lit('1.0').alias(f'_block{index}_degree'))
    if tick: tick()
    return joined

def match_apply_double(
        function: Callable[[str], list[str]],
        data1: PolarsDataframe,
        data2: PolarsDataframe,
        fieldmap1: dict[str, str],
        fieldmap2: dict[str, str],
        index: int,
        ticker: Ticker) -> PolarsDataframe:
    tick = ticker(6)
    def application(data, header_ignorant, header_applied, header_applied1, header_applied2):
        data = data.with_columns(polars.col(header_ignorant).map_elements(function, polars.List(polars.String)).alias(header_applied))
        data = data.with_columns(polars.col(header_applied).list.get(0).alias(header_applied1))
        data = data.with_columns(polars.col(header_applied).list.get(1).alias(header_applied2))
        return data
    headerset1_ignorant = [f'_block{index}{header}_ignorant' for header in fieldmap1.values()]
    headerset2_ignorant = [f'_block{index}{header}_ignorant' for header in fieldmap2.values()]
    headerset1_applied = [f'_block{index}{header}_applied' for header in fieldmap1.values()]
    headerset2_applied = [f'_block{index}{header}_applied' for header in fieldmap2.values()]
    headerset1_applied1 = [f'_block{index}{header}_applied1' for header in fieldmap1.values()]
    headerset2_applied1 = [f'_block{index}{header}_applied1' for header in fieldmap2.values()]
    headerset1_applied2 = [f'_block{index}{header}_applied2' for header in fieldmap1.values()]
    headerset2_applied2 = [f'_block{index}{header}_applied2' for header in fieldmap2.values()]
    for header_ignorant, header_applied, header_applied1, header_applied2 in zip(headerset1_ignorant, headerset1_applied, headerset1_applied1, headerset1_applied2):
        data1 = application(data1, header_ignorant, header_applied, header_applied1, header_applied2)
    for header_ignorant, header_applied, header_applied1, header_applied2 in zip(headerset2_ignorant, headerset2_applied, headerset2_applied1, headerset2_applied2):
        data2 = application(data2, header_ignorant, header_applied, header_applied1, header_applied2)
    if tick: tick()
    joined_set_1x1 = data2.join(data1, left_on=headerset2_applied1, right_on=headerset1_applied1, how='inner')
    if tick: tick()
    joined_set_1x2 = data2.join(data1, left_on=headerset2_applied2, right_on=headerset1_applied1, how='inner')
    if tick: tick()
    joined_set_2x1 = data2.join(data1, left_on=headerset2_applied1, right_on=headerset1_applied2, how='inner')
    if tick: tick()
    joined_set_2x2 = data2.join(data1, left_on=headerset2_applied2, right_on=headerset1_applied2, how='inner')
    if tick: tick()
    joined_sets = [joined_set_1x1, joined_set_1x2, joined_set_2x1, joined_set_2x2]
    joined = polars.concat(joined_sets, how='diagonal').unique(['_data1_id', '_data2_id'])
    joined = joined.with_columns(polars.lit('1.0').alias(f'_block{index}_degree'))
    if tick: tick()
    return joined

def match_compare(
        function: Callable[[PolarsDataframe, str, str, str], PolarsDataframe],
        data1: PolarsDataframe,
        data2: PolarsDataframe,
        fieldmap1: dict[str, str],
        fieldmap2: dict[str, str],
        threshold: float,
        index: int,
        ticker: Ticker) -> PolarsDataframe:
    tick = ticker(4)
    headerset1 = list(fieldmap1.values())
    headerset2 = list(fieldmap2.values())
    data1_connector = f'_block{index}_data1_connector'
    data2_connector = f'_block{index}_data2_connector'
    data1 = data1.with_columns(polars.concat_str([polars.col(header) for header in headerset1], separator='|').alias(data1_connector))
    data2 = data2.with_columns(polars.concat_str([polars.col(header) for header in headerset2], separator='|').alias(data2_connector))
    block_degree = f'_block{index}_degree'
    if tick: tick()
    pairsets = []
    for i in range(0, len(data1)):
        pairset_index = f'_pairset{i}'
        data2 = data2.with_columns(polars.lit(i, polars.UInt32).alias(pairset_index))
        pairset = data1.join(data2, left_on='_data1_id', right_on=pairset_index, how='inner')
        data2 = data2.drop(pairset_index)
        pairsets.append(pairset)
    if tick: tick()
    pairs = polars.concat(pairsets)
    pairs = function(pairs, data1_connector, data2_connector, block_degree)
    if tick: tick()
    matching = pairs.filter(polars.col(block_degree) >= threshold)
    matching = matching.with_columns(polars.col(block_degree).cast(polars.String))
    if tick: tick()
    return matching

def ignorance(
        data: PolarsDataframe,
        header: str,
        ignores: list[str],
        index: int) -> PolarsDataframe:
    regex_index = ([i for i, ignore in enumerate(ignores) if ignore.startswith('regex=')] or [None])[0]
    ignores = ignores.copy()
    ignore_regex_filters = None
    if regex_index is not None:
        ignore_regex_filters = [re.sub(r'^regex=', '', ignores[regex_index])]
        ignores[regex_index] = 'regex'
    processes = {
        'case': ignore_case,
        'regex': ignore_regex(ignore_regex_filters, 'case' in ignores),
        'nonlatin': ignore_nonlatin, # must be after regex in case it expects an accented character that would then be removed and prevent a match
        'titles': ignore_titles('case' in ignores), # must be after nonlatin so characters are convered at this point (also as no titles include accented characters)
        'words-leading': ignore_words_leading, # must be after titles so they go first
        'words-tailing': ignore_words_tailing, # must be before nonalpha so there are still spaces
        'words-order': ignore_words_order, # must be after titles and regex so regex anchors work, and after nonlatin so words sorted in comparable orders
        'nonalpha': ignore_nonalpha # must be after everything that splits words so there are still spaces
    }
    for ignore in ignores:
        if ignore not in processes.keys():
            raise Exception(f'{ignore}: ignorance property not known')
    functions = [function for name, function in processes.items() if name in ignores]
    header_ignorant = f'_block{index}{header}_ignorant'
    data = data.with_columns(polars.col(header).alias(header_ignorant))
    for function in functions:
        data = function(data, header_ignorant)
    return data

def ignore_case(data: PolarsDataframe, header: str) -> PolarsDataframe:
    return data.with_columns(polars.col(header).str.to_lowercase())

def ignore_nonalpha(data: PolarsDataframe, header: str) -> PolarsDataframe:
    regex = '[^a-zA-Z0-9]+'
    return data.with_columns(polars.col(header).str.replace_all(regex, ''))

def ignore_nonlatin(data: PolarsDataframe, header: str) -> PolarsDataframe:
    return data.with_columns(polars.col(header).map_elements(unidecode.unidecode, polars.String))

def ignore_words_leading(data: PolarsDataframe, header: str) -> PolarsDataframe:
    return data.with_columns(polars.col(header).str.split(' ').list.get(-1))

def ignore_words_tailing(data: PolarsDataframe, header: str) -> PolarsDataframe:
    return data.with_columns(polars.col(header).str.split(' ').list.get(0))

def ignore_words_order(data: PolarsDataframe, header: str) -> PolarsDataframe:
    return data.with_columns(polars.col(header).str.split(' ').list.sort().list.join(' '))

def ignore_regex(filters: Optional[list[str]], ignore_case: bool) -> Callable[[PolarsDataframe, str], PolarsDataframe]:
    def filterer(data: PolarsDataframe, header: str) -> PolarsDataframe:
        if filters is None: return data
        regex = ('(?i)' if ignore_case else '') + '|'.join(filters)
        return data.with_columns(polars.col(header).str.replace_all(regex, ''))
    return filterer

def ignore_titles(ignore_case: bool) -> Callable[[PolarsDataframe, str], PolarsDataframe]:
    titles_file = importlib.resources.files('textmatch').joinpath('ignored-titles.txt').open()
    titles = [line[:-1] for line in titles_file]
    return ignore_regex(titles, ignore_case)

def supplement(
        join: str,
        data1: PolarsDataframe,
        data2: PolarsDataframe,
        matches: PolarsDataframe) -> PolarsDataframe:
    if join.lower() not in ['inner', 'left-outer', 'right-outer', 'full-outer']:
        raise Exception(f'{join}: join type not known')
    if join.lower() == 'full-outer' or join.lower() == 'left-outer':
        data1_combination = data1.join(matches, on='_data1_id', how='left', suffix='_matches')
        unmatches_data1 = data1_combination.filter(polars.col('_data2_id').is_null()).select(matches.columns)
        matches = polars.concat([matches, unmatches_data1])
    if join.lower() == 'full-outer' or join.lower() == 'right-outer':
        data2_combination = data2.join(matches, on='_data2_id', how='left', suffix='_matches')
        unmatches_data2 = data2_combination.filter(polars.col('_data1_id').is_null()).select(matches.columns)
        matches = polars.concat([matches, unmatches_data2])
    return matches

def format(
        matches: PolarsDataframe,
        columnmap1: dict[str, str],
        columnmap2: dict[str, str],
        output: Optional[list[str]],
        alert: Optional[Alert]) -> PolarsDataframe:
    matches = matches.with_columns(polars.concat_str(polars.col([column for column in matches.columns if column.endswith('_degree')]), separator='; ').alias('_degree'))
    headerset = []
    if output is None:
        headerset = list(columnmap1.values()) + list(columnmap2.values())
    else:
        duplicate_names = ', '.join(set([definition for definition in output if output.count(definition) > 1]))
        if duplicate_names: raise Exception(f'output cannot contain duplicates: {duplicate_names}')
        for definition in output:
            if re.match(r'^[1|2]\..*', definition): # standard header definitions
                number, field = definition.split('.', 1)
                if (number == '1' and field not in columnmap1.keys()) or (number == '2' and field not in columnmap2.keys()):
                    raise Exception(f'{field}: field not found in dataset {number}')
                if number == '1':
                    headerset.append(columnmap1[field])
                if number == '2':
                    headerset.append(columnmap2[field])
            elif re.match(r'^[1|2]\*$', definition): # expand 1* and 2* to all columns from that dataset
                number = definition.split('*')[0]
                if number == '1':
                    headerset = headerset + list(columnmap1.values())
                elif number == '2':
                    headerset = headerset + list(columnmap2.values())
            elif definition == 'degree': # the matching degree
                headerset.append('_degree')
            else: raise Exception('output format must be the dataset number, followed by a dot, followed by the name of the column')
    column_items = list(columnmap1.items()) + list(columnmap2.items())
    column_names = list(columnmap1.keys()) + list(columnmap2.keys())
    duplicates = {pair for pair in column_items if column_names.count(pair[0]) > 1}
    for name, identifier in duplicates:
        if identifier.startswith('_data1'):
            if alert: alert(f'{name}: column appears in both datasets, will be disambiguated', importance='warning')
            columnmap1[f'{name}_1'] = columnmap1.pop(name)
        if identifier.startswith('_data2'):
            columnmap2[f'{name}_2'] = columnmap2.pop(name)
    columnmap = {**columnmap1, **columnmap2}
    columnmap_inverse = {header: name for name, header in columnmap.items()}
    columnmap_inverse['_degree'] = 'degree'
    for header in headerset:
        matches = matches.rename({header: columnmap_inverse[header]})
    fields = [columnmap_inverse[header] for header in headerset]
    return matches.select(*fields)
