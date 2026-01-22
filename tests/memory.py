import time
import textmatch

def test_out_of_memory():
    for count in [10_000, 50_000, 100_000]:
        print(f'\nRunning with {count} × {count} rows...')
        data1 = {
            'code1': ['A' if i % 2 == 0 else 'B' for i in range(count)],
            'number1': [str(i) * 10 for i in range(count)]
        }
        data2 = {
            'code2': ['A' if i % 2 == 0 else 'Z' for i in range(count)],
            'number2': [str(i) * 10 for i in range(count)]
        }
        start = time.time()
        results = textmatch.run(
            data1,
            data2,
            matching=[
                {
                    'fields': [{'1': 'code1', '2': 'code2'}],
                    'method': 'literal'
                },
                {
                    'fields': [{'1': 'number1', '2': 'number2'}],
                    'method': 'damerau-levenshtein'
                }
            ],
            alert=lambda message, importance=None: print(message)
        )
        duration = time.time() - start
        print(f'Success: matched {len(results):,} rows in {duration:.0f}s')
