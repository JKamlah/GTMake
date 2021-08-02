###################### INFORMATION #############################
#   Create gt line pairs
########## IMPORT ##########
import imghdr
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from textwrap import wrap

import click
from PIL import Image, ImageOps
from tesserocr import PyTessBaseAPI, RIL, iterate_level
from tqdm import tqdm


########## CUTTER FUNCTION ##########
@click.command()
@click.argument('fpaths', nargs=-1, type=click.Path(exists=True))
@click.option('-o', '--outputfolder', type=click.Path(),
              help='Per default the output is stored into a gt folder in the image folder')
@click.option('-e', '--image-extension', 'ext', default='jpg', help='Image extension (Input)')
@click.option('--autocontrast', default=False, is_flag=True, help='Apply autocontrast to lineimages (Output)')
@click.option('--psm', default=3, help='Pagesegmentationmode (please see tesseract --help-extra)')
@click.option('-l', '--lang', default="eng", help='Tesseract language model')
@click.option('--level', default="line", help='Level of cut (line, word, glyph)',
              type=click.Choice(['line', 'word', 'glyph']))
@click.option('--padval', default=0, help='Add more pixel to the cut by a fix value')
@click.option('--padprc', default=0.0, help='Add more pixel to the cut by percentage')
@click.option('-r', '--regex', default=".*", help='Filter the lines to output by a regular expression')
@click.option('--min-len', default=1, help='Filter the lines to output by min amount of characters')
@click.option('--max-len', default=0, help='Filter the lines to output by max amount of characters')
@click.option('--min-conf', default=0, help='Filter the lines to output by a min confidence level')
@click.option('--max-conf', default=100, help='Filter the lines to output by a max confidence level')
@click.option('--mod-line', default=0, help='Filter the lines to output if the modulus of the linenumber is 0')
@click.option('-n', '--num', default=0, help='Maximal ground truth lines to produce')
@click.option('--num-per-page', default=0, help='Maximal ground truth lines to produce per page')
@click.option('-g', '--gitrepo', default=False, is_flag=True,
              help='Create a git repository and add all images. Further processing can be done with GTCheck.')
@click.option('-t', '--empty-textfiles', default=False, is_flag=True,
              help='Add empty textfiles to gitrepo and then replace')
@click.option('-v', '--verbose', default=False, is_flag=True, help='Print more process information')
@click.pass_context
def make_gt_line_pairs(ctx, fpaths, outputfolder, psm, lang, ext,
                       autocontrast, level, padval, padprc,
                       regex, min_len, max_len,
                       min_conf, max_conf,
                       num, num_per_page, mod_line,
                       gitrepo, empty_textfiles, verbose):
    """
    Cuts areas (char, word, line) which contains user-specific expression
    :return:
    """
    fnames = get_fnames(fpaths, ext)
    if verbose:
        print(f"Start processing {len(fnames)} files: {fnames}")
    line_count = 1
    gtdirs = defaultdict(list)
    try:
        with PyTessBaseAPI(lang=lang, psm=psm) as api:
            for fname in tqdm(fnames):
                line_count_per_page = 1
                gtdir = Path(outputfolder) if outputfolder and Path(
                    outputfolder).parent.exists() else fname.parent.joinpath('gt/')
                gtdirs[str(gtdir.resolve())].append(fname)
                if num == line_count:
                    break
                # Set necessary information
                api.SetImageFile(str(fname.resolve()))
                # Set Variable
                api.Recognize()
                ri = api.GetIterator()
                # The char method is not quite correct,
                # it seems that charbboxes get calculated after recognition, which leads sometimes to false cutouts.
                level = {'glyph': RIL.SYMBOL, 'word': RIL.WORD, 'line': RIL.TEXTLINE}.get(level, RIL.TEXTLINE)
                img = Image.open(fname)
                count = 0
                for r in iterate_level(ri, level):
                    symbol = r.GetUTF8Text(level).strip()  # r == ri
                    conf = r.Confidence(level)
                    if len(symbol) < min_len:
                        continue
                    if max_len and len(symbol) > max_len:
                        continue
                    if not (min_conf < conf < max_conf):
                        continue
                    expr_result = re.search(fr"{regex}", symbol)
                    if expr_result:
                        if not gtdir.exists():
                            gtdir.mkdir()
                        origsymbol = symbol[:]
                        count += 1
                        if mod_line and count % mod_line == 0:
                            continue
                        bbox = r.BoundingBoxInternal(level)
                        if padval != 0:
                            bbox = (bbox[0] + padval, bbox[1] + padval, bbox[2] + padval, bbox[3] + padval)
                        elif padprc != 0.0:
                            bbox = (bbox[0] + padprc, bbox[1] + padprc, bbox[2] + padprc, bbox[3] + padprc)
                        cutarea = img.crop(bbox)
                        new_fname = fname.name.split('.', 1)[0] + '_{:04d}'.format(count)
                        if autocontrast:
                            cutarea = ImageOps.autocontrast(cutarea)
                        cutarea.save(gtdir.joinpath(new_fname + f".{ext}"))
                        origsymbol = '???' if origsymbol == '' else origsymbol
                        with open(gtdir.joinpath(new_fname + '.json'), 'w') as cutinfo:
                            # Information (Number of cut, Line/Word/Char Text, Confidence, BBOX)
                            bboxinfo = {'BBOX': bbox, 'Page': fname.name}
                            json.dump(bboxinfo, cutinfo, indent=4)
                        with open(gtdir.joinpath(new_fname + '.gt.txt'), 'w') as cutinfo:
                            # Information (Number of cut, Line/Word/Char Text, Confidence, BBOX)
                            cutinfo.write(origsymbol)
                        if verbose:
                            print(f"Write file: {new_fname}")
                            print(f"Content: {origsymbol}")
                        with open(gtdir.joinpath('cutinfo.txt'), 'a') as cutinfo:
                            # Information (Number of cut, Line/Word/Char Text, Confidence, BBOX)
                            cutinfo.write(
                                f"[{datetime.now().strftime('%d-%b-%Y (%H:%M)')}]\t{count:06d}\t{origsymbol}"
                                f"\t{conf:.3f}\t{bbox}\n")
                        if num == line_count:
                            break
                        if num_per_page == line_count_per_page:
                            break
                        line_count_per_page += 1
                        line_count += 1
        if gitrepo:
            from create_gitrepo import create_gitrepo
            for gtdir, filelist in gtdirs.items():
                fnames = '\n'.join(
                    wrap('; '.join([fname.parent.name + '/' + fname.name for fname in filelist]), width=80))
                readme_text = f"This repository contains gt files which were automatically generated with GTMake " \
                              f"(https://github.com/UB-Mannheim/GTMake).\n\n" \
                              f"Settings\n" \
                              f"--------\n" \
                              f"image-extension -> {ext} \n" \
                              f"autocontrast -> {autocontrast} \n" \
                              f"psm -> {psm} \n" \
                              f"lang -> {lang} \n" \
                              f"level -> {level} \n" \
                              f"padval -> {padval} \n" \
                              f"padprc -> {padprc} \n" \
                              f"regex -> {regex} \n" \
                              f"min-len -> {min_len} \n" \
                              f"max-len -> {max_len} \n" \
                              f"min-conf -> {min_conf} \n" \
                              f"max-conf -> {max_conf} \n" \
                              f"mod-line -> {mod_line} \n" \
                              f"num -> {num} \n\n" \
                              f"Processed files\n" \
                              f"---------------\n" \
                              f"{fnames}"
                ctx.invoke(create_gitrepo, repopath=gtdir, empty_textfiles=empty_textfiles, readme_text=readme_text,
                           verbose=verbose)
    except Exception as e:
        print("Some nasty things while cutting happens. Error:\n", e)
    return 0


def get_fnames(fpaths, ext):
    fnames = []
    for fpath in fpaths:
        fpath = Path(fpath)
        if fpath.is_dir():
            for next_fpath in fpath.rglob(f'*.{ext}'):
                if imghdr.what(next_fpath) is not None:
                    fnames.append(next_fpath)
        else:
            if imghdr.what(fpath) is not None:
                fnames.append(fpath)
    return fnames


def get_pad(bbox, padval: int = 0, padprc: float = 0.0) -> tuple:
    """
    Calculates the padding values for cutting
    :param bbox: boundingbox information
    :param padval: padding value (pixel)
    :param padprc: padding value (percentage)
    :return:
    """
    pad = [0, 0]
    try:
        if padval != 0:
            pad = [val+padval for val in pad]
        if padprc != 0.0:
            pad[0] = int((pad[0] + abs(bbox[3] - bbox[1])) * padprc)
            pad[1] = int((pad[1] + abs(bbox[2] - bbox[0])) * padprc)
    except AssertionError:
        print('Padding values are incorrect.')
    return tuple(pad)


if __name__ == '__main__':
    make_gt_line_pairs()
