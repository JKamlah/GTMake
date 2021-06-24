###################### INFORMATION #############################
#   Create gt line pairs 

########## IMPORT ##########
from tesserocr import PyTessBaseAPI, RIL, iterate_level
from PIL import Image
import re
import json
from pathlib import Path
import imghdr
import click
from tqdm import tqdm

########## CUTTER FUNCTION ##########
@click.command()
@click.argument('fpaths', nargs=-1, type=click.Path(exists=True))
@click.option('-o', '--outputfolder', type=click.Path(), help='Per default the output is stored into a gt folder in the image folder')
@click.option('--ext', default="jpg", help='Image extension')
@click.option('--psm', default=3, help='Pagesegmentationmode (please see tesseract --help-extra)')
@click.option('-l', '--lang', default="eng", help='Tesseract language model')
@click.option('--level', default="line", help='Level of cut (line, word, char)', type=click.Choice(['line','word','char']))
@click.option('--padval', default=0, help='Add more pixel to the cut by a fix value')
@click.option('--padprc', default=0.0, help='Add more pixel to the cut by percantage')
@click.option('-r', '--regex', default=".*", help='Filter the lines to output by a regular expression')
@click.option('--min_len', default=1, help='Filter the lines to output by min amount of characters')
@click.option('--max_len', default=0, help='Filter the lines to output by max amount of characters')
@click.option('--min_conf', default=0, help='Filter the lines to output by a min confidence level')
@click.option('--max_conf', default=100, help='Filter the lines to output by a max confidence level')
@click.option('--mod_line', default=0, help='Filter the lines to output if the modulus of the linenumber is 0')
@click.option('-n','--num', default=0, help='Maximal ground truth lines to produce')
@click.option('-g', '--gitrepo', default=False, is_flag=True, help='Create a git repository and add all images. Further processing can be done with GTCheck.')
@click.option('-t', '--empty_textfiles', default=False, is_flag=True, help='Add empty textfiles to gitrepo and then replace')
@click.option('-v', '--verbose', default=False, is_flag=True, help='Print more process information')
@click.pass_context
def make_gt_line_pairs(ctx, fpaths, outputfolder, psm, lang, ext,
                       level, padval, padprc,
                       regex, min_len, max_len,
                       min_conf, max_conf,
                       num, mod_line,
                       gitrepo, empty_textfiles, verbose):
    """
    Cuts areas (char, word, line) which contains user-specific expression
    :param file: inputfile
    :param fileout: output filename
    :param tess_profile: profile containing user-specific informations and options
    :return:
    """
    fnames = get_fnames(fpaths, ext)
    if verbose:
        print(f"Start processing {len(fnames)} files: {fnames}")
    line_count = 1
    gtdirs = []
    try:
        with PyTessBaseAPI(lang=lang,psm=psm) as api:
            for fname in tqdm(fnames):
                if num == line_count: break
                # Set necessary information
                api.SetImageFile(str(fname.resolve()))
                # Set Variable
                api.Recognize()
                ri = api.GetIterator()
                # The char method is not quite correct,
                # it seems that charbboxes get calculated after recognition, which leads sometimes to false cutouts.
                level = {"char":RIL.SYMBOL, "word":RIL.WORD, "line":RIL.TEXTLINE}.get(level, RIL.TEXTLINE)
                img = Image.open(fname)
                count = 0
                for r in iterate_level(ri, level):
                    symbol = r.GetUTF8Text(level).strip()  # r == ri
                    conf = r.Confidence(level)
                    if len(symbol) < min_len: continue
                    if max_len and len(symbol) > max_len: continue
                    if not (min_conf < conf < max_conf): continue
                    expr_result = re.search(fr"{regex}", symbol)
                    if expr_result:
                        origsymbol = symbol[:]
                        count += 1
                        if mod_line and count%mod_line == 0 : continue
                        bbox = r.BoundingBoxInternal(level)
                        if padval != 0:
                            bbox = (bbox[0]+padval,bbox[1]+padval,bbox[2]+padval,bbox[3]+padval)
                        elif padprc != 0.0:
                            bbox = (bbox[0] + padprc, bbox[1] + padprc, bbox[2] + padprc, bbox[3] + padprc)
                        cutarea = img.crop(bbox)
                        gtdir = Path(outputfolder) if outputfolder and Path(outputfolder).parent.exists() else fname.parent.joinpath("gt/")
                        if str(gtdir.resolve()) not in gtdirs:
                            gtdirs.append(str(gtdir.resolve()))
                        if not gtdir.exists():
                            gtdir.mkdir()
                        new_fname = fname.name.split(".",1)[0]+'_{:04d}'.format(count)
                        cutarea.save(gtdir.joinpath(new_fname+".png"))
                        origsymbol = "???" if origsymbol == "" else origsymbol
                        with open(gtdir.joinpath(new_fname+".json"), "w") as cutinfo:
                            # Information (Number of cut, Line/Word/Char Text, Confidence, BBOX)
                            bboxinfo = {"BBOX":bbox,"Page":fname.name}
                            json.dump(bboxinfo, cutinfo, indent=4)
                        with open(gtdir.joinpath(new_fname+".gt.txt"), "w") as cutinfo:
                            # Information (Number of cut, Line/Word/Char Text, Confidence, BBOX)
                            cutinfo.write(origsymbol)
                        if verbose:
                            print(f"Write file: {new_fname}")
                            print(f"Content: {origsymbol}")
                        with open(gtdir.joinpath("cutinfo.txt"),"a") as cutinfo:
                            # Information (Number of cut, Line/Word/Char Text, Confidence, BBOX)
                            cutinfo.write('{:06d}'.format(count)
                                          +"\t"+origsymbol
                                          +"\t"+'{:.3f}'.format(conf)
                                          +"\t"+str(bbox)+"\n")
                        if num == line_count: break
                        line_count += 1
        if gitrepo:
            from create_gitrepo import create_gitrepo
            for gtdir in gtdirs:
                ctx.invoke(create_gitrepo, repopath=gtdir, empty_textfiles=empty_textfiles,verbose=verbose)
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

def get_pad(bbox,padval:int=0, padprc:float=0.0)->tuple:
    """
    Calculates the padding values for cutting
    :param bbox: boundingbox information
    :param padval: padding value (pixel)
    :param padprc: padding value (percantage)
    :return:
    """
    pad = [0,0]
    try:
        if padval != 0:
            pad = pad+padval
        if padprc != 0.0:
            pad[0] = int((pad[0]+abs(bbox[3]-bbox[1]))*padprc)
            pad[1] = int((pad[0]+abs(bbox[2]-bbox[0]))*padprc)
    except:
        print("Padding values are incorrect.")
    return tuple(pad)

if __name__ == "__main__":
    make_gt_line_pairs()
