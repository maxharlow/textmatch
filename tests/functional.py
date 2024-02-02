import textmatch

def test_simple():
    data1 = {
        'name': ['William Shakespeare', 'Christopher Marlowe']
    }
    data2 = {
        'person': ['Anne Hathaway', 'William Shakespeare']
    }
    results = textmatch.run(data1, data2)
    assert results.to_pydict() == {
        'name': ['William Shakespeare'],
        'person': ['William Shakespeare']
    }

def test_spaces_in_column_names():
    data1 = {
        'name': ['William Shakespeare', 'Christopher Marlowe']
    }
    data2 = {
        'person name': ['Anne Hathaway', 'William Shakespeare']
    }
    results = textmatch.run(data1, data2)
    assert results.to_pydict() == {
        'name': ['William Shakespeare'],
        'person name': ['William Shakespeare']
    }

def test_multiple_columns():
    data1 = {
        'name': ['William Shakespeare', 'Christopher Marlowe'],
        'born': ['1564', '1583']
    }
    data2 = {
        'person': ['Christopher Marlowe', 'William Shakespeare'],
        'birth': ['unknown', '1564']
    }
    results = textmatch.run(data1, data2)
    assert results.to_pydict() == {
        'name': ['William Shakespeare'],
        'born': ['1564'],
        'person': ['William Shakespeare'],
        'birth': ['1564']
    }

def test_multiple_matches():
    data1 = {
        'name': ['Anne Hathaway', 'Anne Hathaway', 'Christopher Marlowe']
    }
    data2 = {
        'person': ['Anne Hathaway', 'Christopher Marlowe', 'Christopher Marlowe']
    }
    results = textmatch.run(data1, data2)
    assert results.to_pydict() == {
        'name': ['Anne Hathaway', 'Anne Hathaway', 'Christopher Marlowe', 'Christopher Marlowe'],
        'person': ['Anne Hathaway', 'Anne Hathaway', 'Christopher Marlowe', 'Christopher Marlowe']
    }

def test_multiple_matches2():
    data1 = {
        'forename': ['William', 'Mary', 'Anne']
    }
    data2 = {
        'firstname': ['Anne', 'Anne', 'Hamlet']
    }
    results = textmatch.run(data1, data2)
    assert results.to_pydict() == {
        'forename': ['Anne', 'Anne'],
        'firstname': ['Anne', 'Anne']
    }

def test_no_matches():
    data1 = {
        'name': ['Anne Hathaway', 'Christopher Marlowe']
    }
    data2 = {
        'person': ['William Shakespeare', 'Someone Else']
    }
    results = textmatch.run(data1, data2)
    assert results.to_pydict() == {
        'name': [],
        'person': []
    }

def test_same_headers():
    data1 = {
        'name': ['Anne Hathaway', 'Christopher Marlowe']
    }
    data2 = {
        'name': ['William Shakespeare', 'Christopher Marlowe']
    }
    results = textmatch.run(data1, data2)
    assert results.to_pydict() == {
        'name_1': ['Christopher Marlowe'],
        'name_2': ['Christopher Marlowe']
    }

def test_fields_specified():
    data1 = {
        'name': ['William Shakespeare', 'Christopher Marlowe'],
        'born': ['1564', '1564']
    }
    data2 = {
        'person': ['William Shakespeare', 'Anne Hathaway'],
        'hometown': ['Stratford-upon-Avon', 'Stratford-upon-Avon']
    }
    results = textmatch.run(data1, data2, fields1=[['name']], fields2=[['person']])
    assert results.to_pydict() == {
        'name': ['William Shakespeare'],
        'person': ['William Shakespeare'],
        'born': ['1564'],
        'hometown': ['Stratford-upon-Avon']
    }

def test_fields_ordering():
    data1 = {
        'name': ['William Shakespeare', 'Christopher Marlowe'],
        'born': ['1564', '1564']
    }
    data2 = {
        'birth': ['1564', '1556'],
        'person': ['William Shakespeare', 'Anne Hathaway']
    }
    results = textmatch.run(data1, data2, fields1=[['name', 'born']], fields2=[['person', 'birth']])
    assert results.to_pydict() == {
        'name': ['William Shakespeare'],
        'born': ['1564'],
        'person': ['William Shakespeare'],
        'birth': ['1564']
    }

def test_blocks_simple():
    data1 = {
        'forename': ['William', 'Christopher'],
        'surname': ['Shakespeare', 'Marlowe']
    }
    data2 = {
        'last_name': ['Shakespeare', 'Shakespeare', 'Hathaway'],
        'first_name': ['William', 'John', 'Anne']
    }
    results = textmatch.run(data1, data2, fields1=[['surname'], ['forename']], fields2=[['last_name'], ['first_name']])
    assert results.to_pydict() == {
        'forename': ['William'],
        'surname': ['Shakespeare'],
        'last_name': ['Shakespeare'],
        'first_name': ['William']
    }

def test_ignore_case():
    data1 = {
        'name': ['Anne Hathaway', 'Christopher Marlowe']
    }
    data2 = {
        'person': ['william shakespeare', 'christopher marlowe']
    }
    results = textmatch.run(data1, data2, ignores=[['case']])
    assert results.to_pydict() == {
        'name': ['Christopher Marlowe'],
        'person': ['christopher marlowe']
    }

def test_ignore_regex():
    data1 = {
        'name': ['ONE Anne Hathaway', 'TWO Christopher Marlowe']
    }
    data2 = {
        'person': ['THREE Christopher Marlowe', 'FOUR William Shakespeare']
    }
    results = textmatch.run(data1, data2, ignores=[['regex=ONE|TWO|THREE|FOUR']])
    assert results.to_pydict() == {
        'name': ['TWO Christopher Marlowe'],
        'person': ['THREE Christopher Marlowe']
    }

def test_ignore_titles():
    data1 = {
        'name': ['Ms. Anne Hathaway', 'Mr. William Shakespeare']
    }
    data2 = {
        'person': ['Mr. Christopher Marlowe', 'Mrs. Anne Hathaway']
    }
    results = textmatch.run(data1, data2, ignores=[['titles']])
    assert results.to_pydict() == {
        'name': ['Ms. Anne Hathaway'],
        'person': ['Mrs. Anne Hathaway']
    }

def test_ignore_nonlatin():
    data1 = {
        'name': ['Charlotte Brontë', 'Gabriel García Márquez']
    }
    data2 = {
        'person': ['Gabriel Garcia Marquez', 'Leo Tolstoy']
    }
    results = textmatch.run(data1, data2, ignores=[['nonlatin']])
    assert results.to_pydict() == {
        'name': ['Gabriel García Márquez'],
        'person': ['Gabriel Garcia Marquez']
    }

def test_ignore_nonalpha():
    data1 = {
        'name': ['William Shakespeare', 'Anne-Hathaway', 'Christopher Marlowe']
    }
    data2 = {
        'person': ['Anne Hathaway!', 'William Shakespeare.']
    }
    results = textmatch.run(data1, data2, ignores=[['nonalpha']])
    assert results.to_pydict() == {
        'name': ['William Shakespeare', 'Anne-Hathaway'],
        'person': ['William Shakespeare.', 'Anne Hathaway!']
    }

def test_ignore_words_leading():
    data1 = {
        'name': ['William Shakespeare', 'Anne Hathaway']
    }
    data2 = {
        'person': ['Christopher Marlowe', 'Billy Shakespeare']
    }
    results = textmatch.run(data1, data2, ignores=[['words-leading']])
    assert results.to_pydict() == {
        'name': ['William Shakespeare'],
        'person': ['Billy Shakespeare']
    }

def test_ignore_words_tailing():
    data1 = {
        'name': ['William Shakespeare', 'Anne Hathaway']
    }
    data2 = {
        'person': ['Christopher Marlowe', 'William S.']
    }
    results = textmatch.run(data1, data2, ignores=[['words-tailing']])
    assert results.to_pydict() == {
        'name': ['William Shakespeare'],
        'person': ['William S.']
   }

def test_ignore_words_order():
    data1 = {
        'name': ['William Shakespeare', 'Anne Hathaway']
    }
    data2 = {
        'person': ['Anne Hathaway', 'Shakespeare William']
    }
    results = textmatch.run(data1, data2, ignores=[['words-order']])
    assert results.to_pydict() == {
        'name': ['William Shakespeare', 'Anne Hathaway'],
        'person': ['Shakespeare William', 'Anne Hathaway']
    }

def test_ignore_multiples1():
    data1 = {
        'name': ['William Shakespeare', 'Ms Anne Hathaway']
    }
    data2 = {
        'person': ['Pröf William Shakespeare', 'Christopher Marlowe']
    }
    results = textmatch.run(data1, data2, ignores=[['nonlatin', 'titles']])
    assert results.to_pydict() == {
        'name': ['William Shakespeare'],
        'person': ['Pröf William Shakespeare']
    }

def test_ignore_multiples2():
    data1 = {
        'name': ['John Shakespeare', 'Mary Árden']
    }
    data2 = {
        'person': ['Arden, Mary', 'Hathaway, Anne']
    }
    results = textmatch.run(data1, data2, ignores=[['nonlatin', 'nonalpha', 'words-order']])
    assert results.to_pydict() == {
        'name': ['Mary Árden'],
        'person': ['Arden, Mary']
    }

def test_ignore_multiples3():
    data1 = {
        'name': ['EM Forster', 'JD Salinger']
    }
    data2 = {
        'person': ['Harper Lee', 'Fórster, ÉM']
    }
    results = textmatch.run(data1, data2, ignores=[['nonlatin', 'nonalpha', 'words-order']])
    assert results.to_pydict() == {
        'name': ['EM Forster'],
        'person': ['Fórster, ÉM']
    }

def test_ignore_multiples4():
    data1 = {
        'name': ['William Shakespeare', 'Charlotte Brontë']
    }
    data2 = {
        'person': ['BRONTE, CHARLOTTE', 'SHAKESPEARE, WILLIAM']
    }
    results = textmatch.run(data1, data2, ignores=[['case', 'nonlatin', 'nonalpha', 'words-order']])
    assert results.to_pydict() == {
        'name': ['William Shakespeare', 'Charlotte Brontë'],
        'person': ['SHAKESPEARE, WILLIAM', 'BRONTE, CHARLOTTE']
    }

def test_ignore_multiples5():
    data1 = {
        'name': ['William Shakéspeare', 'Christopher Marlowe']
    }
    data2 = {
        'person': ['Anne Hathaway', 'William Shakespeare']
    }
    results = textmatch.run(data1, data2, ignores=[['nonalpha', 'nonlatin']])
    assert results.to_pydict() == {
        'name': ['William Shakéspeare'],
        'person': ['William Shakespeare']
    }

def test_ignore_multiples6():
    data1 = {
        'name': ['Mr William Shakespeare', 'Christopher Marlowe']
    }
    data2 = {
        'person': ['Anne Hathaway', 'William SHAKESPEARE']
    }
    results = textmatch.run(data1, data2, ignores=[['case', 'titles']])
    assert results.to_pydict() == {
        'name': ['Mr William Shakespeare'],
        'person': ['William SHAKESPEARE']
    }

def test_methods_levenshtein():
    data1 = {
        'name': ['William Shakespeare', 'Anne Hathaway']
    }
    data2 = {
        'person': ['Ann Athawei', 'Will Sheikhspere']
    }
    results = textmatch.run(data1, data2, methods=['levenshtein'])
    assert results.to_pydict() == {
        'name': ['William Shakespeare', 'Anne Hathaway'],
        'person': ['Will Sheikhspere', 'Ann Athawei']
    }

def test_methods_levenshtein_no_matches():
    data1 = {
        'name': ['Anne Hathaway', 'Christopher Marlowe']
    }
    data2 = {
        'person': ['William Shakespeare', 'Someone Else']
    }
    results = textmatch.run(data1, data2, methods=['levenshtein'])
    assert results.to_pydict() == {
        'name': [],
        'person': []
    }

def test_methods_levenshtein_fields():
    data1 = {
        'name': ['William Shakespeare', 'Christopher Marlowe'],
        'address': ['Henley Street', 'Corpus Christi'],
        'born': ['5164', '1564']
    }
    data2 = {
        'birth': ['1564', '1556'],
        'person': ['Will Sheikhspere', 'Anne Hathaway'],
        'location': ['Henley Street', 'Cottage Lane']
    }
    results = textmatch.run(data1, data2, fields1=[['name', 'address']], fields2=[['person', 'location']], methods=['levenshtein'])
    assert results.to_pydict() == {
        'name': ['William Shakespeare'],
        'address': ['Henley Street'],
        'born': ['5164'],
        'birth': ['1564'],
        'person': ['Will Sheikhspere'],
        'location': ['Henley Street']
    }

def test_methods_jaro():
    data1 = {
        'name': ['William Shakespeare', 'Christopher Marlowe']
    }
    data2 = {
        'person': ['Chris Barlow', 'Willy Shake-Spear']
    }
    results = textmatch.run(data1, data2, methods=['jaro'])
    assert results.to_pydict() == {
        'name': ['William Shakespeare', 'Christopher Marlowe'],
        'person': ['Willy Shake-Spear', 'Chris Barlow']
    }

def test_methods_jaro_no_matches():
    data1 = {
        'name': ['Anne Hathaway', 'Christopher Marlowe']
    }
    data2 = {
        'person': ['William Shakespeare', 'Someone Else']
    }
    results = textmatch.run(data1, data2, methods=['jaro'])
    assert results.to_pydict() == {
        'name': [],
        'person': []
    }

def test_methods_metaphone():
    data1 = {
        'name': ['William Shakespeare', 'Anne Hathaway']
    }
    data2 = {
        'person': ['Ann Hathaweii', 'Will Sheikhspere']
    }
    results = textmatch.run(data1, data2, methods=['metaphone'])
    assert results.to_pydict() == {
        'name': ['Anne Hathaway'],
        'person': ['Ann Hathaweii']
    }

def test_methods_metaphone_no_matches():
    data1 = {
        'name': ['Anne Hathaway', 'Christopher Marlowe']
    }
    data2 = {
        'person': ['William Shakespeare', 'Someone Else']
    }
    results = textmatch.run(data1, data2, methods=['metaphone'])
    assert results.to_pydict() == {
        'name': [],
        'person': []
    }

def test_methods_multiple1():
    data1 = {
        'forename': ['William', 'Mary', 'Anne'],
        'surname': ['Shakespeare', 'Arden', 'Hathaway']
    }
    data2 = {
        'lastname': ['Athawei', 'Hathaway', 'Hathaway', 'Whateley'],
        'firstname': ['Anne', 'Hamnet', 'Ann', 'Anne']
    }
    results = textmatch.run(data1, data2, fields1=[['forename'], ['surname']], fields2=[['firstname'], ['lastname']], methods=['metaphone', 'literal'])
    assert results.to_pydict() == {
        'forename': ['Anne'],
        'surname': ['Hathaway'],
        'lastname': ['Hathaway'],
        'firstname': ['Ann']
    }

def test_methods_multiple2():
    data1 = {
        'forename': ['William', 'Mary', 'Anne', 'William'],
        'surname': ['Shakespeare', 'Arden', 'Hathaway', 'Sheikhspere'],
        'country': ['UK', 'UK', 'USA', 'USA']
    }
    data2 = {
        'residence': ['UK', 'UK', 'UK', 'UK'],
        'lastname': ['Athawei', 'Sheikhspere', 'Hathaway', 'Whateley'],
        'firstname': ['Ann', 'William', 'Anne', 'Anne']
    }
    results = textmatch.run(data1, data2, fields1=[['country'], ['forename', 'surname']], fields2=[['residence'], ['firstname', 'lastname']], methods=['literal', 'levenshtein'])
    assert results.to_pydict() == {
        'forename': ['William'],
        'surname': ['Shakespeare'],
        'country': ['UK'],
        'residence': ['UK'],
        'lastname': ['Sheikhspere'],
        'firstname': ['William']
    }

def test_output():
    data1 = {
        'Person Name': ['William Shakespeare', 'Christopher Marlowe'],
        'born': ['1564', '1583']
    }
    data2 = {
        'person': ['Anne Hathaway', 'William Shakespeare'],
        'death': ['1623', '1616']
    }
    results = textmatch.run(data1, data2, fields1=[['Person Name']], fields2=[['person']], output=['1*', '2.death', 'degree'])
    assert results.to_pydict() == {
        'Person Name': ['William Shakespeare'],
        'born': ['1564'],
        'death': ['1616'],
        'degree': ['1.0']
    }

def test_output_pairwise():
    data1 = {
        'Person Name': ['William Shakespeare', 'Christopher Marlowe'],
        'born': ['1564', '1583']
    }
    data2 = {
        'person': ['Anne Hathaway', 'Wiliam Shakspeare'],
        'death': ['1623', '1616']
    }
    results = textmatch.run(data1, data2, fields1=[['Person Name']], fields2=[['person']], methods=['levenshtein'], output=['1*', '2.death', 'degree'])
    assert results.to_pydict() == {
        'Person Name': ['William Shakespeare'],
        'born': ['1564'],
        'death': ['1616'],
        'degree': ['0.8947368']
    }

def test_output_blocks():
    data1 = {
        'forename': ['William', 'Christopher'],
        'surname': ['Shakespeare', 'Marlowe']
    }
    data2 = {
        'last_name': ['Shakespeare', 'Shakespeare', 'Hathaway'],
        'first_name': ['William', 'John', 'Anne']
    }
    results = textmatch.run(data1, data2, fields1=[['surname'], ['forename']], fields2=[['last_name'], ['first_name']], output=['1*', 'degree'])
    assert results.to_pydict() == {
        'forename': ['William'],
        'surname': ['Shakespeare'],
        'degree': ['1.0; 1.0']
    }

def test_join_left_outer():
    data1 = {
        'name': ['William Shakespeare', 'Christopher Marlowe']
    }
    data2 = {
        'person': ['Anne Hathaway', 'William Shakespeare']
    }
    results = textmatch.run(data1, data2, join='left-outer')
    assert results.to_pydict() == {
        'name': ['William Shakespeare', 'Christopher Marlowe'],
        'person': ['William Shakespeare', None]
    }

def test_join_right_outer():
    data1 = {
        'name': ['William Shakespeare', 'Christopher Marlowe']
    }
    data2 = {
        'person': ['Anne Hathaway', 'William Shakespeare']
    }
    results = textmatch.run(data1, data2, join='right-outer')
    assert results.to_pydict() == {
        'name': ['William Shakespeare', None],
        'person': ['William Shakespeare', 'Anne Hathaway']
    }

def test_join_full_outer():
    data1 = {
        'name': ['William Shakespeare', 'Christopher Marlowe']
    }
    data2 = {
        'person': ['Anne Hathaway', 'William Shakespeare']
    }
    results = textmatch.run(data1, data2, join='full-outer')
    assert results.to_pydict() == {
        'name': ['William Shakespeare', 'Christopher Marlowe', None],
        'person': ['William Shakespeare', None, 'Anne Hathaway']
    }
