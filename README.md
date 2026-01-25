Textmatch
=========

Find fuzzy matches between datasets.

Fuzzy matching is the art and science of connecting up bits of information that are written differently but represent the same _thing_ – such as a person or company.

See also: [CSV Match](https://github.com/maxharlow/csvmatch), a command-line tool based on Textmatch.


Installing
----------

    $ pip install textmatch


Getting started
---------------

The best way to approach fuzzy matching with Textmatch is to start with an exact match. From there, you can incrementally improve the results by telling Textmatch about relevant information that should be taken into account and irrelevant information that should be disregarded. Experiment with different approaches. It is helpful to know what the data looks like, and how it has been collected.

The input datasets can be dataframes from [PyArrow](https://arrow.apache.org/docs/python), [Pandas](https://github.com/pandas-dev/pandas), or [Polars](https://github.com/pola-rs/polars). The output results will be in PyArrow format – which can then be converted to Pandas with `matches.to_pandas()`, or to Polars with `polars.from_arrow(matches)`.

```python
import textmatch
```

<details>
  <summary>Example</summary>

  **`data1`**:
  | name           | codename  |
  |----------------|-----------|
  | Percy Alleline | Tinker    |
  | Bill Haydon    | Tailor    |
  | Roy Bland      | Soldier   |
  | Toby Esterhase | Poorman   |
  | George Smiley  | Beggerman |

  **`data2`**:
  | Person Name     | Alias   |
  |-----------------|---------|
  | Percy Alleline  | Chief   |
  | Bill Haydon     | Tailor  |
  | Howard Staunton | Control |

  To run an exact match on the **name** column from the first dataset against **Person Name** from the second:

  ```python
  textmatch.run(
    data1,
    data2,
    matching=[
      {'fields': [{'1': 'name', '2': 'Person Name'}]}
    ]
  )
  ```

  This gives us matches for the two names which are in both datasets, despite the differences in the other column:

  | name           | codename | Person Name    | Alias  |
  |----------------|----------|----------------|--------|
  | Percy Alleline | Tinker   | Percy Alleline | Chief  |
  | Bill Haydon    | Tailor   | Bill Haydon    | Tailor |

</details>

Matches are _many-to-many_, ie. it is possible for one row in the first dataset to match several rows in the second, and vice-versa.

> [!TIP]
> There is a tradeoff between false negatives and false positives – it is often better to have some incorrect matches in your results that can be manually checked afterwards than to have correct matches missing.


Usage
-----

Textmatch has one function, `run`, which accepts the first dataset followed by the second. All other arguments are optional.

The `match` argument accepts a list of dictionaries, where each dictionary represents a matching block.

### Match fields
Within each match block, the `fields` key defines which columns should be compared. It accepts a list of dictionaries, where each dictionary maps a column from the first dataset (`1`) to a column from the second dataset (`2`). Defaults to comparing all columns.

<details>
  <summary>Example</summary>

  **`data1`**:
  | name           | codename  |
  |----------------|-----------|
  | Percy Alleline | Tinker    |
  | Bill Haydon    | Tailor    |
  | Roy Bland      | Soldier   |
  | Toby Esterhase | Poorman   |
  | George Smiley  | Beggerman |

  **`data2`**:
  | Person Name    | Alias  |
  |----------------|--------|
  | Percy Alleline | Chief  |
  | Bill Haydon    | Tailor |

  To match on the **name** and **codename** columns from the first dataset against **Person Name** and **Alias** from the second:

  ```python
  textmatch.run(
    data1,
    data2,
    matching=[
      {
        'fields': [
          {'1': 'name', '2': 'Person Name'},
          {'1': 'codename', '2': 'Alias'}
        ]
      }
    ]
  )
  ```

  This gives us a match in the single case where both columns from both datasets are the same:

  | name        | codename | Person Name | Alias  |
  |-------------|----------|-------------|--------|
  | Bill Haydon | Tailor   | Bill Haydon | Tailor |
</details>


### Match ignorance
Within each match block, the `ignores` key accepts a list of characteristics which should be disregarded for two records to be considered a match.

Combining different forms of ignorance can be quite powerful. The order in which you specify them is not significant.

**`case`** ignores how text is capitalised.

<details>
  <summary>Example</summary>

  **`data1`**:
  | name                 |
  |----------------------|
  | Florence Nightingale |

  **`data2`**:
  | Person Name          |
  |----------------------|
  | Florence NIGHTINGALE |

  ```python
  textmatch.run(
    data1,
    data2,
    matching=[
      {
        'fields': [{'1': 'name', '2': 'Person Name'}],
        'ignores': ['case']
      }
    ]
  )
  ```

  This gives us a match despite the capitalised surname in the second dataset:

  | name                 | Person Name          |
  |----------------------|----------------------|
  | Florence Nightingale | Florence NIGHTINGALE |
</details>

**`nonalpha`** ignores anything that isn't a number or a letter. Note that this includes whitespace.

<details>
  <summary>Example</summary>

  **`data1`**:
  | name          |
  |---------------|
  | John Lennon   |
  | Daniel DeFoe  |

  **`data2`**:
  | Person Name   |
  |---------------|
  | John-Lennon   |
  | Daniel De Foe |

  ```python
  textmatch.run(
    data1,
    data2,
    matching=[
      {
        'fields': [{'1': 'name', '2': 'Person Name'}],
        'ignores': ['nonalpha']
      }
    ]
  )
  ```

  This gives us a match in the first case despite the hypen, and in the second case despite the space between the two parts of the surname:

  | name          | Person Name   |
  |---------------|---------------|
  | John Lennon   | John-Lennon   |
  | Daniel DeFoe | Daniel De Foe  |
</details>

**`nonlatin`** ignores non-Latin characters. You may also want to consider applying [Unicode normalisation](https://docs.python.org/3/library/unicodedata.html#unicodedata.normalize) beforehand.

<details>
  <summary>Example</summary>

  **`data1`**:
  | name             |
  |------------------|
  | Jérôme Bonaparte |
  | Ehrich Weiß      |
  | Александр Пушкин |

  **`data2`**:
  | Person Name       |
  |-------------------|
  | Jerome Bonaparte  |
  | Ehrich Weiss      |
  | Alexander Pushkin |

  ```python
  textmatch.run(
    data1,
    data2,
    matching=[
      {
        'fields': [{'1': 'name', '2': 'Person Name'}],
        'ignores': ['nonlatin']
      }
    ]
  )
  ```

  This gives us a match despite the diacritics in the first case, matches `ß` to `ss` in the second, and transliterates in the last case. The further the script is from the Latin alphabet, the less accurate this transliteration will be.

  | name             | Person Name         |
  |------------------|---------------------|
  | Jérôme Bonaparte | Jerome Bonaparte    |
  | Ehrich Weiß      | Ehrich Weiss        |
  | Александр Пушкин | Alexander Pushkin   |
</details>

**`words-leading`** ignores all words except the last. This is useful for matching on surnames only.

<details>
  <summary>Example</summary>

  **`data1`**:
  | name          |
  |---------------|
  | Boris Johnson |
  | Mary Tudor    |

  **`data2`**:
  | Person Name                        |
  |------------------------------------|
  | Alexander Boris de Pfeffel Johnson |
  | Elizabeth Tudor                    |


  ```python
  textmatch.run(
    data1,
    data2,
    matching=[
      {
        'fields': [{'1': 'name', '2': 'Person Name'}],
        'ignores': ['words-leading']
      }
    ]
  )
  ```

  This gives us a match in the first case despite middle names being included, and in the second case gives us an erronious match between different people sharing a surname:

  | name           | Person Name                        |
  |----------------|------------------------------------|
  | Boris Johnson  | Alexander Boris de Pfeffel Johnson |
  | Mary Tudor     | Elizabeth Tudor                    |
</details>

**`words-tailing`** ignore all words except the first.

<details>
  <summary>Example</summary>

  **`data1`**:
  | name         |
  |--------------|
  | Turing, Alan |

  **`data2`**:
  | Person Name           |
  |-----------------------|
  | Turing, Alan Mathison |

  ```python
  textmatch.run(
    data1,
    data2,
    matching=[
      {
        'fields': [{'1': 'name', '2': 'Person Name'}],
        'ignores': ['words-tailing']
      }
    ]
  )
  ```

  This gives us a match in this example where surnames are listed first, despite middle names being included in the second dataset:

  | name         | Person Name           |
  |--------------|-----------------------|
  | Turing, Alan | Turing, Alan Mathison |
</details>

**`words-order`** ignores the order in which the words are given. This is useful for matching names given surname-first with those given forename-first.

<details>
  <summary>Example</summary>

  **`data1`**:
  | name       |
  |------------|
  | Mao Zedong |

  **`data2`**:
  | Person Name |
  |-------------|
  | Zedong Mao  |

  ```python
  textmatch.run(
    data1,
    data2,
    matching=[
      {
        'fields': [{'1': 'name', '2': 'Person Name'}],
        'ignores': ['words-order']
      }
    ]
  )
  ```

  This gives us a match despite the name order difference:

  | name       | Person Name |
  |------------|-------------|
  | Mao Zedong | Zedong Mao  |
</details>

**`titles`** ignores common English name prefixes such as Mr and Ms. There is a full list of these titles [here](https://github.com/maxharlow/textmatch/blob/main/src/textmatch/ignored-titles.txt).

<details>
  <summary>Example</summary>

  **`data1`**:
  | name                  |
  |-----------------------|
  | Issac Newton          |
  | Sir Alexander Fleming |

  **`data2`**:
  | Person Name          |
  |----------------------|
  | Sir Issac Newton     |
  | Dr Alexander Fleming |

  ```python
  textmatch.run(
    data1,
    data2,
    matching=[
      {
        'fields': [{'1': 'name', '2': 'Person Name'}],
        'ignores': ['titles']
      }
    ]
  )
  ```

  This gives us matches despite there being no title in the first case, and the titles differing in the second case:

  | name                  | Person Name          |
  |-----------------------|----------------------|
  | Issac Newton          | Sir Issac Newton     |
  | Sir Alexander Fleming | Dr Alexander Fleming |
</details>

**`regex`** ignores terms specific to your data using a given regular expression. This is specified inline: `regex=EXPRESSION`.

<details>
  <summary>Example</summary>

  **`data1`**:
  | name      |
  |-----------|
  | Liz Truss |

  **`data2`**:
  | Person Name  |
  |--------------|
  | Liz Truss MP |

  To use the regular expression ` MP$` to ignore the word 'MP' where it appear at the end of a value:

  ```python
  textmatch.run(
    data1,
    data2,
    matching=[
      {
        'fields': [{'1': 'name', '2': 'Person Name'}],
        'ignores': ['regex= MP$']
      }
    ]
  )
  ```

  This gives us a match despite the MP suffix:

  | name         | Person Name  |
  |--------------|--------------|
  | Liz Truss    | Liz Truss MP |
</details>

### Match methods & thresholds

Within each match block, the `method` key specifies the algorithm used for matching.

There are three different categories of method:

* _Compared_ methods work by comparing every row from the first dataset with every row from the second, producing a number that represents the degree of the match. This means the amount of time required to run a match grows exponentially with the size of the input datasets. However, they are still useful for larger matches when using [blocking](#blocking).
* _Applied_ methods transform text into a different representation before they are matched up. These methods are quicker than compared ones, though no meaningful matching degree number is generated – either they match or they don't.
* _Custom_ methods have their own individual approach. Textmatch only has one, Bilenko. It generates a matching degree number.

For those matching methods that generate a matching degree number there is then a threshold filter for any two records to be considered to be a match – you can adjust this with the `threshold` key, which accepts a number between 0.0 and 1.0, defaulting to 0.6.

You can also include the matching degree number as a column by specifying it in the [output](#outputs).

> [!WARNING]
> When working with names of people, exact matches, even when other pieces of information such as birthdays are included, are not a guarantee that the two names actually refer to the same human. Furthermore, the chance of a mismatch is unintuitively high – as illustrated by [the birthday paradox](https://pudding.cool/2018/04/birthday-paradox/).

**`literal`** is the default – it matches strings exactly, after ignored characteristics have been taken into account.

[**`damerau-levenshtein`**](https://en.wikipedia.org/wiki/Damerau–Levenshtein_distance) (alias **`edit`**) counts the number of insertions, deletions, substitutions, and transpositions that would be required to transform one string into another. It is good at picking up typos and other small differences in spelling. Performs compared matching.

<details>
  <summary>Example</summary>

  **`data1`**:
  | name              |
  |-------------------|
  | Edmund Hillary    |
  | T. E. Lawrence    |
  | George Washington |

  **`data2`**:
  | Person Name            |
  |------------------------|
  | Edmund P. Hilly        |
  | Thomas Edward Lawrence |
  | Denzel Washington      |

  ```python
  textmatch.run(
    data1,
    data2,
    matching=[
      {
        'fields': [{'1': 'name', '2': 'Person Name'}],
        'method': 'damerau-levenshtein',
      }
    ],
    output=['1*', '2*', 'degree']
  )
  ```

  This gives us a 66.7% match for Hillary despite the inclusion of a middle initial and misspelling of the surname. The two other examples show some problems with this approach. Lawrence doesn't appear as a 55% match doesn't meet the threshold despite them looking like the same person. Conversely, Washington does appear at a 71% match, despite them certainly not being the same person:

  | name              | Person Name       | degree    |
  |-------------------|-------------------|-----------|
  | Edmund Hillary    | Edmund P. Hilly   | 0.6666667 |
  | George Washington | Denzel Washington | 0.7058824 |
</details>

[**`ratcliff-obershelp`**](https://en.wikipedia.org/wiki/Gestalt_pattern_matching) first looks for the longest common substring between the two. It then looks either side of that substring for further common substrings, and so on recursively. The final score is the sum of the lengths of all common substrings divided by the sum of the lengths of the two strings. Performs compared matching.

<details>
  <summary>Example</summary>

  **`data1`**:
  | name              |
  |-------------------|
  | Edmund Hillary    |
  | T. E. Lawrence    |
  | George Washington |

  **`data2`**:
  | Person Name            |
  |------------------------|
  | Edmund P. Hilly        |
  | Thomas Edward Lawrence |
  | Denzel Washington      |

  ```python
  textmatch.run(
    data1,
    data2,
    matching=[
      {
        'fields': [{'1': 'name', '2': 'Person Name'}],
        'method': 'ratcliff-obershelp',
      }
    ],
    output=['1*', '2*', 'degree']
  )
  ```

  This gives us a good match for Hilary and Lawrence, although we still have an erronious match for Washington:

  | name              | Person Name            | degree     |
  |-------------------|------------------------|------------|
  | Edmund Hillary    | Edmund P. Hilly        | 0.82758623 |
  | T. E. Lawrence    | Thomas Edward Lawrence | 0.6666667  |
  | George Washington | Denzel Washington      | 0.7647059  |
</details>

[**`jaro-winkler`**](https://en.wikipedia.org/wiki/Jaro–Winkler_distance) counts characters in common between the two strings, though it considers differences near the start of the string to be more significant than differences near the end. Performs compared matching.

[**`double-metaphone`**](https://en.wikipedia.org/wiki/Metaphone#Double_Metaphone) (alias **`phonetic`**) converts the words in each string into a representation of how they are pronounced. Tends to work well for data which has been transcribed or transliterated. Performs applied matching.

<details>
  <summary>Example</summary>

  **`data1`**:
  | name            |
  |-----------------|
  | Joaquin Phoenix |

  **`data2`**:
  | Person Name   |
  |---------------|
  | Wakeen Feenix |

  ```python
  textmatch.run(
    data1,
    data2,
    matching=[
      {
        'fields': [{'1': 'name', '2': 'Person Name'}],
        'method': 'double-metaphone'
      }
    ],
    output=['1*', '2*', 'degree']
  )
  ```

  This gives us a match that we would not have got with other methods:

  | name            | Person Name   | degree |
  |-----------------|---------------|--------|
  | Joaquin Phoenix | Wakeen Feenix | 1.0    |
</details>

**`bilenko`** uses [Dedupe](https://github.com/dedupeio/dedupe), a library built by Forest Gregg and Derek Eder based on the work of Mikhail Bilenko that will ask you to train it by asking whether different pairs of records should match. The information you give it is then extrapolated to match up the rest of the dataset. The more examples you give it, the better the results will be. At minimum, try to provide 10 positive matches and 10 negative matches. Performs custom matching.

This uses Python multiprocessing, which requires you wrap your code in an if statement [as described here](https://docs.python.org/3/library/multiprocessing.html#multiprocessing-safe-main-import).

### Blocking

Blocking is the approach of performing multiple matches, with subsequent matches only applying to the subset of matches resulting from the previous match. This can make matches both quicker and more precise. This is an advanced topic, and can be ignored if you are happy with the quality of matches and are dealing with smaller datasets.

In a 'regular' match, you are really just matching using a single block. Each block is defined by: a list of fields for each dataset, a list of ignores, a method, and a threshold. To perform a blocked match, provide multiple dictionaries in the `match` list. Each dictionary corresponds to one block.

<details>
  <summary>Example</summary>

  **`data1`**:
  | name            |
  |-----------------|
  | Tim Berners-Lee |

  **`data2`**:
  | Person Name      |
  |------------------|
  | Time BERNERS-LEE |
  | Tim Berners-Leed |

  To specify a first block that does a case-insensitive literal match on surnames, then a second block performing a Damerau-Levenshtein match on forenames:

  ```python
  textmatch.run(
    data1,
    data2,
    matching=[
      {
          'fields': [{'1': 'name', '2': 'Person Name'}],
          'ignores': ['case', 'words-leading'],
          'method': 'literal'
      },
      {
          'fields': [{'1': 'name', '2': 'Person Name'}],
          'ignores': ['words-tailing'],
          'method': 'damerau-levenshtein'
      }
    ],
    output=['1*', '2*', 'degree']
  )
  ```

  The first block matches the capitalised surname 100% after ignoring the case, then the second block runs a Damerau-Levenshtein match on the forename, which matches 75%:

  | name            | Person Name      | degree    |
  |-----------------|------------------|-----------|
  | Tim Berners-Lee | Time BERNERS-LEE | 0.75; 1.0 |
</details>

### Outputs

The `output` argument accepts a list of column names which should appear in the output, each prefixed with a number and a dot indicating which dataset that field is from. They are case-sensitive, and can be in any order you desire. It defaults to all columns in the first dataset, followed by all columns in the second.

There are some special column definitions: `1*` and `2*` expand into all columns from the first and second datasets respectively, and `degree` will add a column with the matching degree number.

<details>
  <summary>Example</summary>

  **`data1`**:
  | name           | codename  |
  |----------------|-----------|
  | Percy Alleline | Tinker    |
  | Bill Haydon    | Tailor    |
  | Roy Bland      | Soldier   |
  | Toby Esterhase | Poorman   |
  | George Smiley  | Beggerman |

  **`data2`**:
  | Person Name      | Alias   | Location |
  |------------------|---------|----------|
  | Perci Alleline   | Chief   | London   |
  | Bill Haydon      | Tailor  | London   |
  | Howhard Staunton | Control | Unknown  |

  To output the **codename** column from the first dataset, followed by every column from the second dataset, followed by the matching degree:

  ```python
  textmatch.run(
    data1,
    data2,
    matching=[
      {
        'fields': [{'1': 'name', '2': 'Person Name'}],
        'method': 'damerau-levenshtein'
      }
    ],
    output=['1.codename', '2*', 'degree']
  )
  ```

  | codename | Person Name    | Alias  | Location | degree     |
  |----------|----------------|--------|----------|------------|
  | Tinker   | Perci Alleline | Chief  | London   | 0.9285714  |
  | Tailor   | Bill Haydon    | Tailor | London   | 1.0        |
</details>

### Join types

The `join` argument takes a string that indicates what other nonmatching records should be included in the output. A `left-outer` join will return everything from the first dataset, whether there was a match or not, a `right-outer` to do the same but for the second dataset, and a `full-outer` to return everything from both datasets. Where two rows didn't match the values will be blank. Defaults to an `inner` join, where only successful matches are returned.

<details>
  <summary>Example</summary>

  **`data1`**:
  | name           | codename  |
  |----------------|-----------|
  | Percy Alleline | Tinker    |
  | Bill Haydon    | Tailor    |
  | Roy Bland      | Soldier   |
  | Toby Esterhase | Poorman   |
  | George Smiley  | Beggerman |

  **`data2`**:
  | Person Name      | Alias   | Location |
  |------------------|---------|----------|
  | Perci Alleline   | Chief   | London   |
  | Bill Haydon      | Tailor  | London   |
  | Howhard Staunton | Control | Unknown  |

  To include all rows from the first dataset, but only those that match from the second:

  ```python
  textmatch.run(
    data1,
    data2,
    matching=[
      {'fields': [{'1': 'name', '2': 'Person Name'}]}
    ],
    join='left-outer'
  )
  ```

  | name           | codename  | Person Name | Alias  | Location |
  |----------------|-----------|-------------|--------|----------|
  | Bill Haydon    | Tailor    | Bill Haydon | Tailor | London   │
  | Percy Alleline | Tinker    |             |        |          │
  | Roy Bland      | Solder    |             |        |          │
  | Toby Esterhase | Poorman   |             |        |          │
  | George Smiley  | Beggarman |             |        |          │
</details>


Progress bars & alerts
----------------------

By default Textmatch does not print out any details of its operations, however it is possible to to display progress bars and logging alerts by defining `progress` and `alert` functions that handle these events. This is especially useful in an interactive Jupyter environment.

For example, using [`tqdm`](https://github.com/tqdm/tqdm) and [`ipywidgets`](https://github.com/jupyter-widgets/ipywidgets):

```python
import tqdm.notebook

def progress(operation, total):
    bar = tqdm.notebook.tqdm(desc=operation, total=total, bar_format='{desc} {bar} {percentage:3.0f}% {remaining} left', dynamic_ncols=True)
    return bar.update

def alert(message, *, importance = None):
    print(f'[{importance.upper()}] {message}' if importance else message)
```

These functions are then passed as arguments when you run Textmatch:

```python
textmatch.run(
    data1,
    data2,
    matching=[
        {'fields': [{'1': 'name', '2': 'Person Name'}]}
    ],
    progress=progress,
    alert=alert
).to_pandas()
```


Other libraries
---------------

### Python

* [RecordLinkage](https://github.com/J535D165/recordlinkage)
* [Splink](https://github.com/moj-analytical-services/splink)
* [DeezyMatch](https://github.com/Living-with-machines/DeezyMatch)
* [Dedupe](https://github.com/dedupeio/dedupe)
* [DeepMatcher](https://github.com/anhaidgroup/deepmatcher)
* [Hlink](https://github.com/ipums/hlink)
* [Skrub](https://github.com/skrub-data/skrub)
* [RLTK](https://github.com/usc-isi-i2/rltk)
* [String Grouper](https://github.com/Bergvca/string_grouper)
* [PyEntityMatching](https://github.com/anhaidgroup/py_entitymatching)
* [TextPack](https://github.com/lukewhyte/textpack)
* [String2String](https://github.com/stanfordnlp/string2string)
* [RapidFuzz](https://github.com/maxbachmann/RapidFuzz)
* [TheFuzz](https://github.com/seatgeek/thefuzz)

### R

* [Zoomerjoin](https://github.com/beniaminogreen/zoomerjoin)
* [Reclin2](https://github.com/djvanderlaan/reclin2)
* [Fedmatch](https://github.com/seunglee98/fedmatch)
* [FastLink](https://github.com/kosukeimai/fastLink)
* [Fuzzyjoin](https://github.com/dgrtwo/fuzzyjoin)
