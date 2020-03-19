from pathlib import Path
import yaml

from format_notes import basic_format


DATA_PATH = Path(__file__).parent/'tests'


def prepare_input(fn):
    test_note = yaml.safe_load(fn.open())

    input_ = ''
    notes = []
    notes_insert_point = []
    idx = -1
    for syl in test_note['input']:
        if isinstance(syl, str):
            syl = syl.replace('_', ' ')
            input_ += syl
            idx += len(syl)
        else:
            notes_insert_point.append(idx)
            notes.append(syl)

    return (input_, notes, notes_insert_point), test_note['expected']



def test_basic_format():
    test_fns = [DATA_PATH/'formatting-split-word.yaml', DATA_PATH/'basic-formatting-normal.yaml']

    for test_fn in test_fns:
        input_, expected = prepare_input(test_fn)
        result = basic_format(*input_)

        assert expected['note'] == result[0]


if __name__ == "__main__":
    test_basic_format()