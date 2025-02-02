from typing import Optional
import sys
import warnings
import colorama
import polars
import dedupe
import dedupe.core
import dedupe.variables

from ..typings import (
    PolarsDataframe,
    DedupeLabelledData,
    Ticker,
    Alert
)

def execute(
        data1: PolarsDataframe,
        data2: PolarsDataframe,
        fieldmap1: dict[str, str],
        fieldmap2: dict[str, str],
        threshold: float,
        index: int,
        ticker: Ticker,
        alert: Optional[Alert]) -> PolarsDataframe:
    fields1 = list(fieldmap1.keys())
    fields2 = list(fieldmap2.keys())
    headers1 = list(fieldmap1.values())
    headers2 = list(fieldmap2.values())
    # add match columns to data1 and data2
    for i, (header1, header2) in enumerate(zip(headers1, headers2)):
        match_column = f'_block{index}_match_col{i}'
        data1 = data1.with_columns(polars.col(header1).alias(match_column))
        data2 = data2.with_columns(polars.col(header2).alias(match_column))
    # transform data1 and data2 into the format required by Dedupe
    input1 = {row['_data1_id']: row for row in data1.to_dicts()}
    input2 = {row['_data2_id']: row for row in data2.to_dicts()}
    # remove the match columns from data1 and data2
    for i, _ in enumerate(zip(headers1, headers2)):
        match_column = f'_block{index}_match_col{i}'
        data1 = data1.drop(match_column)
        data2 = data2.drop(match_column)
    # create a Dedupe variable specification listing all the match columns
    variables = [dedupe.variables.String(f'_block{index}_match_col{i}') for i in range(len(headers1))]
    # set up Dedupe
    linker = dedupe.RecordLink(variables, in_memory=True) # generate pairs in-memory, uses more memory, but faster
    linker.prepare_training(input1, input2, sample_size=15_000) # this sample size is what's used in the Dedupe docs
    with warnings.catch_warnings():
        def warning_alert(warning, *args):
            message = str(warning)
            if message.startswith('The least populated class'):
                message = 'More training will produce better results!'
            if alert: alert(message, importance='warning')
        warnings.showwarning = warning_alert
        while True:
            label(linker, fields1, fields2)
            try:
                linker.train() # throws a ValueError if not enough training has been done
                break
            except ValueError:
                if alert: alert('Not enough training has been completed to run a match', importance='warning')
        tick = ticker(3) if ticker else None
        if tick: tick()
        # run a Dedupe join
        pairs = linker.join(input1, input2, threshold, 'many-to-many')
        if tick: tick()
        # transform Dedupe output into something that can be converted back into a dataframe
        matches = {}
        for ([data1_id, data2_id], degree) in pairs:
            for column_number, column in enumerate(data1.columns):
                if f'_block{index}_match_col' in column: continue
                item = data1.filter(polars.col('_data1_id') == int(data1_id)).select(polars.col(column)).item()
                matches.setdefault(column, []).append(item)
            for column_number, column in enumerate(data2.columns):
                if f'_block{index}_match_col' in column: continue
                item = data2.filter(polars.col('_data2_id') == int(data2_id)).select(polars.col(column)).item()
                matches.setdefault(column, []).append(item)
            matches.setdefault(f'_block{index}_degree', []).append(degree)
        if tick: tick()
        return polars.from_dict(matches)

def label(linker: dedupe.RecordLink, fields1: list[str], fields2: list[str]) -> None:
    colorama.just_fix_windows_console()
    sys.stderr.write(f'\n{colorama.Style.BRIGHT}{colorama.Fore.BLUE}To answer questions:\n y - yes\n n - no\n s - skip\n f - finished{colorama.Style.RESET_ALL}\n')
    fieldlength = len(max([*fields1, *fields2], key=len))
    fields = dedupe.core.unique(variable.field for variable in linker.data_model.field_variables)
    unlabelled = []
    labels_positive = 0
    labels_negative = 0
    finished = False
    while not finished:
        try:
            if not unlabelled: unlabelled = linker.uncertain_pairs()
            pair = unlabelled.pop()
        except IndexError:
            break
        for i, record in enumerate(pair):
            sys.stderr.write('\n')
            for j, field in enumerate(fields):
                header = fields1[j] if i == 0 else fields2[j]
                spacer = ' ' * (fieldlength - len(header))
                sys.stderr.write(f'{spacer}{colorama.Style.BRIGHT}{header}: {colorama.Style.RESET_ALL}{record[field]}\n')
        sys.stderr.write('\n')
        sys.stderr.write(f'{colorama.Style.BRIGHT}{colorama.Fore.BLUE}Progress: {labels_positive} positive, {labels_negative} negative{colorama.Style.RESET_ALL}\n')
        response = ''
        responded = False
        while not responded:
            sys.stderr.write(f'{colorama.Style.BRIGHT}{colorama.Fore.BLUE}Do these records refer to the same thing? [y/n/s/f]{colorama.Style.RESET_ALL} ')
            response = input()
            if response in {'y', 'n', 's', 'f'}: responded = True
        labelled: DedupeLabelledData = {
            'distinct': [],
            'match': []
        }
        match response:
            case 'y':
                labelled['match'].append(pair)
                labels_positive += 1
            case 'n':
                labelled['distinct'].append(pair)
                labels_negative += 1
            case 's':
                labelled['match'].append(pair)
                labelled['distinct'].append(pair)
            case 'f':
                finished = True
        linker.mark_pairs(labelled)
        sys.stderr.write('\n')
