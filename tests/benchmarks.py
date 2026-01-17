import math
import random
import faker
import textmatch

def mock(specification, length):
    data1 = {}
    data2 = {}
    length_half = math.ceil(length / 2)
    fake = faker.Faker('en')
    for column, form in specification.items():
        items_matching = [getattr(fake, form)() for _ in range(length_half)]
        items_unmatching1 = [getattr(fake, form)() for _ in range(length - length_half)]
        items_unmatching2 = [getattr(fake, form)() for _ in range(length - length_half)]
        data1[column] = [*items_matching, *items_unmatching1]
        data2[column] = [*items_matching, *items_unmatching2]
        random.shuffle(data1[column]) # in-place
        random.shuffle(data2[column])
    return (data1, data2)

def test_literal(benchmark):
    specification = {
        'Person': 'name',
        'Office': 'company'
    }
    data1, data2 = mock(specification, 100)
    benchmark(
        textmatch.run,
        data1,
        data2,
        matching=[{
            'method': 'literal',
            'fields': [{'1': key, '2': key} for key in specification]
        }]
    )

def test_literal_ignore_case(benchmark):
    specification = {
        'Person': 'name',
        'Office': 'company'
    }
    data1, data2 = mock(specification, 100)
    benchmark(
        textmatch.run,
        data1,
        data2,
        matching=[{
            'method': 'literal',
            'fields': [{'1': key, '2': key} for key in specification],
            'ignores': ['case']
        }]
    )

def test_damerau_levenshtein(benchmark):
    specification = {
        'Person': 'name',
        'Office': 'company'
    }
    data1, data2 = mock(specification, 100)
    benchmark(
        textmatch.run,
        data1,
        data2,
        matching=[{
            'method': 'damerau-levenshtein',
            'fields': [{'1': key, '2': key} for key in specification]
        }]
    )

def test_jaro_winkler(benchmark):
    specification = {
        'Person': 'name',
        'Office': 'company'
    }
    data1, data2 = mock(specification, 100)
    benchmark(
        textmatch.run,
        data1,
        data2,
        matching=[{
            'method': 'jaro-winkler',
            'fields': [{'1': key, '2': key} for key in specification]
        }]
    )

def test_double_metaphone(benchmark):
    specification = {
        'Person': 'name',
        'Office': 'company'
    }
    data1, data2 = mock(specification, 100)
    benchmark(
        textmatch.run,
        data1,
        data2,
        matching=[{
            'method': 'double-metaphone',
            'fields': [{'1': key, '2': key} for key in specification]
        }]
    )

def test_blocking(benchmark):
    specification = {
        'Surname': 'last_name',
        'Forename': 'first_name'
    }
    data1, data2 = mock(specification, 100)
    benchmark(
        textmatch.run,
        data1,
        data2,
        matching=[
            {
                'method': 'literal',
                'fields': [{'1': key, '2': key} for key in specification]
            },
            {
                'method': 'double-metaphone',
                'fields': [{'1': key, '2': key} for key in specification]
            }
        ]
    )
