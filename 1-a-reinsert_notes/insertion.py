import sys, os
import re
from difflib import SequenceMatcher
from PyTib.common import open_file, write_file, pre_process
from xlwt import Workbook
import yaml
from pathlib import Path


parentDir = Path(__file__).resolve().parent
inDir = parentDir / 'input'
outDir = parentDir / 'output'


def is_punct(string):
    # put in common
    if '༄' in string or '༅' in string or '༆' in string or '༇' in string or '༈' in string or \
        '།' in string or '༎' in string or '༏' in string or '༐' in string or '༑' in string or \
        '༔' in string or '_' in string:
        return True
    else:
        return False


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def strip_particle(word):
    particles = ['འི','འུ','འོ','ར','འམ']
    for particle in particles:
        word = word.strip(particle)
    return word


def reinsert_notes(raw_text, raw_notes, basis_edition='སྡེ་'):
    global note_num
    raw_text = raw_text.replace('a', '').replace('\t', ' ').split('\n')
    raw_notes = re.sub(r'《([^《》་]+)》', r'《\1་》', raw_notes)  # add a tsek in the edition names that lack one.
    raw_notes = raw_notes.strip().split('\n')[1:]

    text = {}
    for t in raw_text:
        parts = re.split(r'([0-9]+)\.[\t\s]', t)[1:]
        if parts:
            note_number = parts[0]
            note_text = pre_process(parts[1], mode='syls')
            if note_text == []:
                note_text = ['']
            text[note_number] = note_text

    edition_regex = r'《([^《》]+)》'

    # finding all the editions that exist for that text
    edition_names = set([e for r in raw_notes for e in re.findall(edition_regex, r)])
    editions = {basis_edition: []}
    for e in edition_names:
        editions[e] = []

    error = False
    for n in raw_notes:
        #if debug == 1:
        if show_note == 1:
            print('\t\t'+n)
        if error:
            break
        if n.replace(',', '').replace(' ', '') == '':
            continue
        parts = n.split(',')
        number = str(int(parts[2])-1)
        # DEBUG. Enables to start debugging at a given note
        #note_num = 304
        if number == str(note_num-1):
            print('ok')
        page_number = parts[1]
        content = parts[4:]
        note = ''
        # keep track of which edition has already been replaced
        generated_versions = {basis_edition: False}
        for e in edition_names:
            generated_versions[e] = False
        # loop through tuples of (edition-s, note)
        max_pairs = len(content)-1
        if max_pairs > len(content):
            max_pairs = len(content)-1
        tuple_idx = [c for c in range(0, max_pairs) if c % 2 == 0]
        for a in tuple_idx:
            if error:
                break
            if content[a]:
            # filters the cases where the second tuple is empty
                note = content[a+1]
                if note == 'ལ་ཆུག་མོད་ཀྱི་ཞེས་བྱ་བ་ན།':
                    print('check')
                if '(' in note:
                    print('there is a note on top of the comparison.')
                    print('\t'.join(parts))
                    note = note.split('(')[0].strip()
                if '《' in note:
                    print('The following note needs to be edited. The execution will stop now.')
                    print('\t'.join(parts))
                    error = True
                    break
                # 0 prepare
                # separate in syllables not separating the fusioned particles
                modif_type = ''
                if note.startswith('m'):
                    modif_type = 'm'
                elif note.startswith('p'):
                    modif_type = 'p'
                version = pre_process(note.replace(modif_type, ''), mode='syls')
                # delete the last element in the list of the note
                #if is_punct(version[-1]):
                if is_punct(version[-1]) and len(version) > 1:
                    del version[-1]
                    # reconstitute the punctuation for comparing the syllables:

                    # add a tsek to it if the original text has one
                    # if the last syllable is not a punctuation
                    if not version[-1].endswith('་'):
                        if not is_punct(text[number][-1]):
                            if not text[number][-1].endswith('་'):
                                version[-1] += '་'   
                        # if the last syllable is a punctuation
                        elif is_punct(text[number][-1]) and len(text[number]) > 1:
                            if text[number][-2].endswith('་'):
                                version[-1] += '་'

                # 1 find index
                # 1.a
                # find the index of the syllable from which to start replacing the original
                index = len(text[number]) - len(version)
                # go one syllable left if the last syllable of the original text is a punctuation
                if is_punct(text[number][-1]):
                    index -= 1
                # put the index at 0 if the replacement text is longer than the original
                if index < 0:
                    index = 0

                # 1.b
                # try to find a point of correspondence in case there are more than a few syllables that are added
                orig_sync_idx = False
                version_sync_idx = False
                window_size = 4
                maximum = len(text[number]) - 1
                # attempts_num becomes 0 if window_size is larger than the length of version, making window_indexes an empty list.
                # this way, window_size decides wether we search for a syncronisation point or not.
                attempts_num = len(version[window_size:])
                window_indexes = [(a, a + window_size) for a in range(attempts_num)]
                # for v_w in window_indexes:
                #     for a_n in range(attempts_num):
                #         orig_window = text[number][maximum - window_size - a_n:maximum - a_n]
                #         version_window = version[v_w[0]:v_w[1]]
                #         if orig_window == version_window:
                #             if not orig_sync_idx:
                #                 orig_sync_idx = maximum - window_size - a_n
                #                 version_sync_idx = v_w[0]

                # finding the sync point if it is the last syllable
                if not orig_sync_idx:
                    # detects which of the two syls is the longest to check if both start the same way
                    if len(text[number][-1]) > len(version[0]):
                        long = text[number][-1]
                        #long = ''.join(text[number][index:])
                        short = version[0].rstrip('་')
                        #short = ''.join(version)
                    else:
                        long = version[0]
                        short = text[number][-1].rstrip('་')
                        # long = ''.join(version)
                        # short = ''.join(text[number][index:])
                    # finds if long is short with an addition. This deals with བདེའང་ being replaced by བདེ་བའང་.
                    # Todo: similar replacements may occur elsewhere than the last syllable. implementation needed.
                    # in case both syllables are identical, the condition is also met.
                    if short in long:
                        if short+'་' != long and (len(version)==1 or short == strip_particle(long.strip('་'))):
                            if modif_type == 'p':   # ,,9,4,《པེ་》《སྣར་》,pཔོ།,
                                orig_sync_idx = len(text[number])
                            else:
                                orig_sync_idx = len(text[number])-1
                        else:
                            orig_sync_idx = index
                        version_sync_idx = 0

                # 2
                # generating the versions of the different editions
                edition_text = [b for b in text[number]]

                # A.1 for subsequent addition, keep the last syllable if it is a punctuation to add it at the end
                edition_text_last_syl = False
                if is_punct(edition_text[-1]):
                    edition_text_last_syl = edition_text[-1]
                    #orig_sync_idx -= 1      # as note's conjuction are removed

                # remove the ending tsek in version if it was not there in the original
                if edition_text[-1].endswith('་'):
                    if not version[-1].endswith('་'):
                        version[-1] += '་'
                    if version[-1].endswith('ང'):
                        version[-1] += '་'
                else:
                    if version[-1].endswith('་') and not version[-1].endswith('ང་'):
                        version[-1] = version[-1].rstrip('་')

                # 2.1 if the operation is a deletion (m stands for minus)
                if modif_type == 'm':
                    # a if there is a synchronizing point between the original and the version
                    if orig_sync_idx:
                        del edition_text[orig_sync_idx:]
                    # b if there is no sync point
                    else:
                        del edition_text[len(edition_text)-len(version):]

                # 2.2 if the operation is an addition (p stands for plus)
                elif modif_type == 'p':
                    # a if there is a synchronizing point between the original and the version
                    if orig_sync_idx:
                        # replace the part that precedes the synchronising point
                        edition_text[orig_sync_idx - version_sync_idx:orig_sync_idx] = version[:version_sync_idx]
                        # replacing from the synchronising point onwards
                        edition_text[orig_sync_idx:orig_sync_idx] = version[version_sync_idx:]
                    # b if there is no sync point
                    else:
                        # add a tsek if there is none on the last syllable
                        if not edition_text[-1].endswith('་'):
                            edition_text[-1] += '་'
                            # remove the ending tsek of version
                            if version[-1].endswith('་'):
                                version[-1] = version[-1].rstrip('་')
                        edition_text.extend(version)

                # 2.3 if the operation is a replacement
                else:
                    if orig_sync_idx:
                        # replace the part that precedes the synchronising point
                        edition_text[orig_sync_idx - version_sync_idx:orig_sync_idx] = version[:version_sync_idx]
                        # replacing from the synchronising point onwards
                        edition_text[orig_sync_idx:] = version[version_sync_idx:]
                        # 2.b if there is no synchronising point
                    else:
                        ad = 0
                        prev_similarity = similar(edition_text[index-1].strip('་'), version[0].strip('་'))
                        diff = len(edition_text[index-1].strip('་'))-len(version[0].strip('་'))
                        if prev_similarity >= 0.5 and len(version)==1:
                            ad = 1
                            index -= 1
                        elif strip_particle(edition_text[index-1].strip('་')) == strip_particle(version[0].strip('་')):
                            ad = 1
                            index -= 1
                        # if len(version)>1:
                        #     if edition_text[index+1] in version:
                        #         index +=1
                        #         edition_text.append('')
                        for e in range(len(version)):
                            #print(e) # གཞུང་འདིའི་བསླབ་པ་ལ་ནི་བསླབ་པར་   དབུ་མ་རིན་པོ་ཆེའི་སྒྲོན་མ།.txt
                            #print(version[e])
                            edition_text[index + e] = version[e]
                        if ad:
                            del edition_text[-1]

                # A.2 add the punctuation to the end if needed
                # if a punctuation was saved in A.1 and if it is not the same as the last syllable of edition_text
                if edition_text_last_syl and len(edition_text) > 0:
                    if edition_text_last_syl != edition_text[-1]:
                        # if the last syllable ends with a tsek
                        if edition_text[-1].endswith('་'):
                            # if there is a ང་
                            if not edition_text[-1].endswith('ང་'):
                                edition_text[-1] = edition_text[-1][:-1]
                        elif edition_text[-len(version)] == version[-1]:
                            edition_text[-2] = edition_text[-1]
                            edition_text[-1] = ''
                        edition_text.append(edition_text_last_syl)


                # 2.4 if a sync point was found, i.e. if the size of version is longer than window_size,
                # add '%' to manually check the replacement has been correctly done
                #if orig_sync_idx:
                #    edition_text[-1] += '%'

                # 3 Add the text to the respective editions
                #
                edition_refs = re.findall(edition_regex, content[a])
                # 3.a add the versions of all the editions that require modifications from Derge and notify the edition is added
                for e in edition_refs:
                    chunk = ''.join(edition_text)
                    # remove the extra spaces inserted between the shad and the next verse
                    chunk = chunk.replace('_།_', '_།').replace('_', ' ')
                    editions[e].append((chunk, len(version), page_number, note))
                    generated_versions[e] = True

        # 3.b add the original version of the text to the remaining
        for g in generated_versions:
            if not generated_versions[g]:
                chunk = ''.join(text[number])
                # remove the extra spaces inserted between the shad and the next verse
                chunk = chunk.replace('_།_', '_།').replace('_', ' ')
                editions[g].append((chunk, '', page_number, note))

    # 4 add the last bit of the text that corresponds to no note
    for g in editions:
        chunk = ''.join(text[str(len(text))])
        chunk = chunk.replace('_།_', '_།').replace('_', ' ')
        editions[g].append((chunk, '', '', ''))
    return editions


def generate_editions(editions, out_dir, work_name):
    # writing all the editions in their respective folder
    for e in editions:
        path = out_dir / 'editions' / e.replace('་', '།') 
        file_name = work_name+'_'+e+'.txt'
        content = ''.join([e[0] for e in editions[e]]).replace('_', ' ')
        write_file(path / file_name, content)


def generate_unified_version(editions):
    '''
    :param editions:
    :return: a list with common syllables as separate elements, differing parts within a dict
    '''
    total = []
    # a. generate the list of editions’ names
    ed_names = [a for a in editions]
    for syl_num in range(1, len(editions['སྡེ་'])):
        pre_processed = {}
        common = []
        # b. segment in syllables and seperate on the punctuation for each version
        for ed in ed_names:
            chunk = editions[ed][syl_num][0].replace('_', ' ')
            pre_processed[ed] = pre_process(chunk, mode='syls')
        # c. add to common the syls that are the same in all editions and leave the others in pre_processed
        while len({pre_processed[ed][0] if pre_processed[ed] != [] else '' for ed in ed_names}) == 1:
            if pre_processed[ed_names[0]]:
                common.append(pre_processed[ed_names[0]][0])
                for ed in ed_names:
                    del pre_processed[ed][0]
            else:
                break

        total.extend(common)
        total.append(pre_processed)
    return total


def generate_context_versions(editions, file_name, out_dir, left=5, right=5, base_ed='སྡེ་'):
    def calculate_contexts(unified_version, left=5, right=5, base_ed='སྡེ་'):
        all_versions = []
        c = 0
        for num, syl in enumerate(unified_version):
            if type(syl) == dict:
                if c == 137:
                    print('ok')
                versions = {}
                for ed in syl:
                    # add left context
                    n_l = num-left
                    if n_l < 0:
                        n_l = 0
                    left_context = unified_version[n_l:num]
                    # add note
                    note = syl[ed]
                    # add right context
                    n_r = num+right+1
                    if n_r > len(unified_version)-1:
                        n_r = len(unified_version)-1
                    right_context = unified_version[num+1:n_r]
                    version = left_context + note + right_context
                    # if there is a note (if version[v] == dict), choose the base_ed version
                    no_note_version = []
                    for v in version:
                        if type(v) == dict:
                            for base_syl in v[base_ed]:
                                no_note_version.append(base_syl)
                        else:
                            no_note_version.append(v)
                    # add the versions in the versions
                    versions[ed] = ''.join(no_note_version).replace('_', ' ')
                c += 1
                versions[str(c)] = ''
                all_versions.append(versions)
        return all_versions

    unified = generate_unified_version(editions)
    with_context = calculate_contexts(unified, left=left, right=right, base_ed=base_ed)
    for i in range(len(with_context)):
        with_context[i] = [[a, with_context[i][a]] for a in sorted(with_context[i])]
    output = yaml.dump_all(with_context, allow_unicode=True, default_flow_style=False, width=float("inf"))
    # reformat the page number
    output = re.sub(r'\n- -([^\n]+)\n  -', r'\n\1: ', output)
    output = re.sub(r"---\n '([0-9]+)':  ''", r'-\1-', output)
    output = re.sub(r"- - '1'\n  - ''", r'-1-', output).replace(" '", '').replace("'", '')
    output = re.sub(r'\n', r',,,,,,,,,,,,,,,\n', output)  # Todo
    write_file(out_dir / f'/conc_yaml/{file_name}_conc.txt', output)


def export_unified_structure(editions, text_name, out_dir=outDir/'unified_structure'):
    unified = generate_unified_version(editions)
    out = yaml.dump(unified, allow_unicode=True, default_flow_style=False, width=float("inf"))
    write_file(out_dir / f'{text_name}_unified_structure.yaml', out)


def generate_outputs(text_name, notes_name, context, in_dir=inDir, out_dir=outDir):

    # extract text and reinsert notes
    editions = reinsert_notes(open_file(in_dir/text_name), open_file(in_dir/notes_name).replace(';', ','))

    work_name = text_name.split('.')[0].replace(' ', '_')
    print(work_name)


    generate_editions(editions, out_dir, work_name)
    
    export_unified_structure(editions, work_name)

    generate_context_versions(editions, work_name, out_dir, left=context, right=context)


excluded = [#'11-20_ཆོས་མངོན་པའི་འགྲེལ་པ་གནད་ཀྱི་སྒྲོན་མ།.txt',
            ]
vol_num = 0

works = []
for f in sorted(os.listdir(inDir)):
    if f.endswith('txt') and f not in excluded:
        csv = f.replace('.txt', '')+'.csv'
        works.append((f, csv))

def debug_files(vol_num):
    c = 0
    for w in works:
        c += 1
        print(c, w[0])
        if c >= vol_num:
            generate_outputs(w[0], w[1], 5)


note_num = 738
debug = 1
show_note = 0
if debug:
    debug_files(vol_num)
else:
    for w in works:
        if 'N5000' not in w[0]:
            continue
        print(w[0])
        generate_outputs(w[0], w[1], 5)
