from PyTib.common import open_file, write_file
import os
from collections import deque
import re


def increment_counter(counter, side):
    increment = False
    change = False
    if side == 'བ':
        increment = True
    if side == 'ན':
        change = True

    if increment:
        return counter + 1, 'ན'
    if change:
        return counter, 'བ'


def page_num(counter, side):
    equivalences = [('1', '༡'), ('2', '༢'), ('3', '༣'), ('4', '༤'), ('5', '༥'), ('6', '༦'), ('7', '༧'), ('8', '༨'), ('9', '༩'), ('0', '༠')]
    num = str(counter)
    for n in equivalences:
        num = num.replace(n[0], n[1])
    return '\[{}{}\]'.format(num, side)


def create_page(lines, size, counter, side):
    page = []
    for i in range(size):
        page.append(lines.popleft())
    return page_num(counter, side) + '\n'.join(page)


def reinsert(in_path, out_path1, out_path2, patterns):
    print('reinsertion with notes')
    for f in os.listdir(in_path):
        work_name = f.replace('_a_reinserted.txt', '')
        if work_name in patterns:
            print('\t', work_name)
            content = open_file('{}/{}'.format(in_path, f))
            if not re.findall(r'\n\[\^[0-9A-Z]+\]\:', content):
                text = content
                notes = ''
            else:
                text, notes = [a for a in re.split(r'((?:\n?\[\^[0-9A-Z]+\]\:[^\n]+\n?)+)', content) if a != '']
            lines = deque(text.replace('\n', ' ').split('a'))

            pages = []
            text_pattern = patterns[work_name][2:]
            counter = patterns[work_name][0][1]
            side = patterns[work_name][0][2]

            # beginning pages
            for num in text_pattern[0]:
                pages.append(create_page(lines, num, counter, side))
                counter, side = increment_counter(counter, side)

            # body of the text
            while len(lines) > 0:
                if len(lines) >= text_pattern[1]:
                    pages.append(create_page(lines, text_pattern[1], counter, side))
                    counter, side = increment_counter(counter, side)
                elif text_pattern[2] == len(lines):
                    pages.append(create_page(lines, len(lines), counter, side))
                    counter, side = increment_counter(counter, side)
                else:
                    print('There is a line number issue: only {} lines were left for the last page.'.format(len(lines)))
                    pages.append(create_page(lines, len(lines), counter, side))
                    counter, side = increment_counter(counter, side)

            output = '\n{}\n'.format('-'*100).join(pages) + '\n\n' + notes

            write_file('{}/{}_page_reinserted.txt'.format(out_path1, work_name), output)

            # write to the file to 3-2-compared if it is not yet there
            existing = [g.replace('_compared.txt', '') for g in os.listdir(out_path2) if g.endswith('.txt')]
            #if work_name not in existing:
            write_file('{}/{}_compared.txt'.format(out_path2, work_name), output)
            text_path = '{}/extra_copies/{}'.format(out_path2, work_name)
            if not os.path.exists(text_path):
                os.makedirs(text_path)


def reinsert_raw(in_path, out_path, patterns):
    print('raw reinsertion')
    for f in os.listdir(in_path):
        work_name = f.replace('_with_a.txt', '')
        if work_name in patterns:
            print('\t', work_name)
            content = open_file('{}/{}'.format(in_path, f))
            lines = deque(content.replace('\n', ' ').split('a'))

            pages = []
            text_pattern = patterns[work_name][2:]
            counter = patterns[work_name][0][1]
            side = patterns[work_name][0][2]

            # beginning pages
            for num in text_pattern[0]:
                pages.append(create_page(lines, num, counter, side))
                counter, side = increment_counter(counter, side)

            # body of the text
            while len(lines) > 0:
                if len(lines) >= text_pattern[1]:
                    pages.append(create_page(lines, text_pattern[1], counter, side))
                    counter, side = increment_counter(counter, side)
                elif text_pattern[2] == len(lines):
                    pages.append(create_page(lines, len(lines), counter, side))
                    counter, side = increment_counter(counter, side)
                else:
                    pages.append(create_page(lines, len(lines), counter, side))
                    counter, side = increment_counter(counter, side)

            output = '\n{}\n'.format('-' * 100).join(pages)

            write_file('{}/{}_raw_page_reinserted.txt'.format(out_path, work_name), output)
# # works, but not needed for now…
# def create_missing_dir(origin_path, target_path, origin_name_end):
#     to_compare_texts = [g.replace(origin_name_end, '') for g in os.listdir(origin_path) if g.endswith('.txt')]
#     for text in to_compare_texts:
#         text_path = '{}/{}'.format(target_path, text)
#         if not os.path.exists(text_path):
#             os.makedirs(text_path)
#
# origin_path = 'output/3-2-compared'
# target_path = '{}/extra_copies'.format(origin_path)
# origin_name_end = '_compared.txt'
# create_missing_dir(origin_path, target_path, origin_name_end)


in_path = './output/2-1-a_reinserted'
out_path1 = './output/3-1-page_reinserted'
out_path2 = './output/3-2-compared'
raw_in_path = './output/2-0-with_a'
raw_out_path = './output/2-2-raw_page_reinserted'

    # '': [
    #     ('start', 0, ''),     # page start + front/back
    #     ('end', 0, ''),       # idem
    #     [0],                  # list of lines per page for the beginning of the text
    #     0,                    # general number of lines per page
    #     0                     # number of lines pertaining to the current text on the last page
    # ]

patterns_raw = open_file('../4-a-final_formatting/resources/དཀར་ཆག་ཀུན་གསལ་མེ་ལོང་། - format example.csv').strip().split('\n')
patterns = {}
for line in patterns_raw[1:]:
    parts = line.split(',')
    names = patterns_raw[0].split(',')
    # 'ཆོས་ཚན།'
    title = re.sub(r'_conc.*', '', parts[1])
    # 'དབུ།'
    b_page = int(parts[2])
    sides = {'a': 'ན', 'b': 'བ'}
    # 'རྒྱབ་འདུན།' (of 'དབུ།')
    b_side = sides[parts[3]]
    # 'ཞབས།'
    e_page = int(parts[6])
    # 'རྒྱབ་འདུན།' (of 'ཞབས།')
    e_side = sides[parts[7]]
    # 'ཤོག་ངོས་གཞན་གྱི་ཐིག་གྲངས།'
    lines_per_page = int(parts[5])
    # lines on first pages excepting the first two
    last_first_pages_lines = [int(a) for a in parts[11:] if a != '']
    # if 'ཞབས་ཀྱི་ཐིག་གྲངས།' == 7 and 'ཤོག་ངོས་གཞན་གྱི་ཐིག་གྲངས།' == 7
    if int(parts[8]) == 7 and int(parts[5]) == 7:
        last_page_lines = 7
    else:
        # 'ཤོག་ངོས་གཞན་གྱི་ཐིག་གྲངས།' - 'ཞབས་ཀྱི་ཐིག་གྲངས།'
        last_page_lines = int(parts[5])-int(parts[8])+1
    # 'ཤོག་ངོས་༢ པའི་ཐིག་གྲངས།' == 7
    if int(parts[10]) == 7:
        # 'ཤོག་ངོས་༡ པོའི་ཐིག་གྲངས།' - 'དབུའི་ཐིག་ཕྲེང་།' + 1
        first_pages_lines = [int(parts[9]) - int(parts[4]) + 1]
        first_pages_lines += last_first_pages_lines
    else:
        # ['ཤོག་ངོས་༡ པོའི་ཐིག་གྲངས།' - 'དབུའི་ཐིག་ཕྲེང་།' + 1, 'ཤོག་ངོས་༢ པའི་ཐིག་གྲངས།']
        first_pages_lines = [int(parts[9])-int(parts[4])+1, int(parts[10])]
        first_pages_lines += last_first_pages_lines
    #patterns[title] = [('start', b_page, b_side), ('end', e_page, e_side), first_pages_lines, lines_per_page, last_page_lines]
    if e_page == b_page + 1 and b_side != e_side:
        # ['ཤོག་ངོས་༡ པོའི་ཐིག་གྲངས།' - 'དབུའི་ཐིག་ཕྲེང་།' + 1]
        patterns[title] = [('start', b_page, b_side), ('end', e_page, e_side), [int(parts[9])-int(parts[4])+1]+last_first_pages_lines, lines_per_page,
                           last_page_lines]
    elif b_page == e_page and b_side == e_side:
        # ['ཞབས་ཀྱི་ཐིག་གྲངས།' - 'དབུའི་ཐིག་ཕྲེང་།' + 1] … ['ཞབས་ཀྱི་ཐིག་གྲངས།' - 'དབུའི་ཐིག་ཕྲེང་།' + 1]
        patterns[title] = [('start', b_page, b_side), ('end', e_page, e_side), [int(parts[8]) - int(parts[4]) + 1]+last_first_pages_lines, lines_per_page,
                           int(parts[8]) - int(parts[4]) + 1]
    else:
        patterns[title] = [('start', b_page, b_side), ('end', e_page, e_side), first_pages_lines, lines_per_page,
                           last_page_lines]

no_valid_lines = ['1-95 རྩོད་པ་བཟློག་པའི་འགྲེལ་པ།',
                  '1-76 གཡུའི་ཐང་མ་ཀྲས་དགུ།',
                  '1-3 འཇིག་རྟེན་ལས་འདས་པར་བསྟོད་པ།',
                  '1-79 གནོད་སྦྱིན་མཁའ་འགྲོ་ཀུན་འཁྱིལ་རྟོགས་པ་ལས་བྱུང་བའི་གྭ་ཐབས།',
                  '1-31 ནག་པོ་ཆེན་པོའི་སྒྲུབ་ཐབས།',
                  '1-75 རྣམ་རྒྱལ་འཕགས་མའི་སྒྲུབ་ཐབས།',
                  '1-107 འཕགས་པ་སཱ་ལུ་ལྗང་པ་ཞེས་བྱ་བ།',
                  '1-34 དཔལ་གསང་བ་འདུས་པའི་རྒྱུད་ཀྱི་རྒྱུད་འགྲེལ།',
                  '117 ལག་ན་རྡོ་རྗེ་གོས་སྔོན་ཅན་གྱི་སྒྲུབ་ཐབས་ཀྱི་རྒྱ་འགྲེལ།'
                  ]
for problem in no_valid_lines:
    del patterns[problem]

reinsert_raw(raw_in_path, raw_out_path, patterns)
reinsert(in_path, out_path1, out_path2, patterns)

