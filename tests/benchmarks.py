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
    fields = [list(specification.keys())]
    data1, data2 = mock(specification, 100)
    benchmark(textmatch.run, data1, data2, fields1=fields, fields2=fields)

def test_literal_ignore_case(benchmark):
    specification = {
        'Person': 'name',
        'Office': 'company'
    }
    fields = [list(specification.keys())]
    data1, data2 = mock(specification, 100)
    benchmark(textmatch.run, data1, data2, fields1=fields, fields2=fields, ignores=[['case']])

def test_levenshtein(benchmark):
    specification = {
        'Person': 'name',
        'Office': 'company'
    }
    fields = [list(specification.keys())]
    data1, data2 = mock(specification, 100)
    benchmark(textmatch.run, data1, data2, fields1=fields, fields2=fields, methods=['levenshtein'])

def test_metaphone(benchmark):
    specification = {
        'Person': 'name',
        'Office': 'company'
    }
    fields = [list(specification.keys())]
    data1, data2 = mock(specification, 100)
    benchmark(textmatch.run, data1, data2, fields1=fields, fields2=fields, methods=['metaphone'])

def test_blocking(benchmark):
    specification = {
        'Surname': 'last_name',
        'Forename': 'first_name'
    }
    fields = [['Surname'], ['Forename']]
    data1, data2 = mock(specification, 100)
    benchmark(textmatch.run, data1, data2, fields1=fields, fields2=fields, methods=['literal', 'metaphone'])
