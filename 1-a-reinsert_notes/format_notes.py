"""Reformat the existing nalanda-note format to have better readability.

Existing format of nalanda-notes are found to be difficult to refer to when reading the text.
So, this module helps to improve the nalanda-note format to have better readability.

Readibility issues with existing nalanda-notes are:
    1. Note doesn't have span of word (note doesn't imply any meaning)
    2. Particle note doesn't have context (hard to cross check)
    3. Some peydurma notes in the base are not the best compared to other edition (base is not the best)
    4. Chunk to be deleted from base is specified in note with remark says it doesn't exists other editions.
       A better note is left and right context of that chunk with editions where chunk doesn't exists.
    5. Note to be inserted doesn't have context.
"""

from collections import defaultdict

from pybo import Text


def to_word_span_note(note, syl, index):
    """Insert the missing syllable and generate foot-note

    Insert the missing syllable to note in a given position(index) to have
    note with word span.

    Args:
        note (dict): note of different editions
        syl (str): missing syllabel to be inserted
        index (int): position of syllabel to inserted (at begining or at end)

    Returns:
        str: foot-notes of formatted note

    """

    # insert the missing syllable and classify the edition base on note content.
    formatted_note = defaultdict(list)
    for edition, syls in note.items():
        syls.insert(0, syl)
        formatted_note[''.join(syls)].append(edition.replace('་', '།'))

    # Convert classified formatted note to foot-note (one liner)
    string_note = []
    for f_note, editions in formatted_note.items():
        if 'སྡེ།' in editions: continue
        string_note.append(f_note)
        string_note.extend(editions)
    return ' '.join(string_note)


def basic_format(text, notes, notes_insert_point):
    '''Format note to have word span'''
    text_with_base = ''
    added_base_len = 0
    formatted_notes = []
    for note, note_insert_point in zip(notes, notes_insert_point):
        # prepare text with base note, mostly སྡེ་'
        if not text_with_base:
            left_text, right_text = text[:note_insert_point+1], text[note_insert_point+1:]
        else:
            left_text = text_with_base[:note_insert_point+added_base_len] 
            right_text = text_with_base[note_insert_point+added_base_len:]

        # insert base note in the text
        base_note = ''.join(note['སྡེ་'])
        text_with_base += f"{left_text}{base_note}{right_text}"

        # format the note from all edition based on word token
        tokenized_text = Text(text_with_base).tokenize_words_raw_text
        char_idx = 0
        base_note_syls = base_note.split('་')
        for token in tokenized_text.split():
            char_idx += len(token)
            if note_insert_point+added_base_len <= char_idx:
                first_syl_idx = token.find(base_note_syls[0])
                if first_syl_idx != -1:
                    formatted_note = to_word_span_note(note, token[:first_syl_idx], 0)
                    formatted_notes.append(formatted_note)

        added_base_len += len(note['སྡེ་'])
    
    return formatted_notes
 