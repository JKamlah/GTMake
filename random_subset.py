import random
from pathlib import Path
import shutil
import click

@click.command()
@click.argument('fpath', nargs=1, type=click.Path(exists=True))
@click.option('-o', '--outputfolder', type=click.Path(), required=True, help='Outputfolder')
@click.option('--num', default=500, help='Sampleset size')
@click.option('-e', '--image-extension', default='png')
@click.option('--text-extension', default='gt.txt')
@click.option('-v', '--verbose', default=False, is_flag=True, help='Print more process information')
def get_random_selection(fpath, outputfolder, num, image_extenstion, text_extension, verbose):
    list_of_files = Path(fpath).rglob(f'*.{image_extenstion}')
    random.shuffle(list(list_of_files))
    outputfolder = Path(outputfolder)
    count = 0
    if not outputfolder.exists():
        outputfolder.mkdir()
    for fname in list_of_files[:num]:
        fname = Path(fname)
        shutil.copy(fname,outputfolder.joinpath(fname.name))
        shutil.copy(fname, outputfolder.joinpath(str(fname.name).rsplit(".",2)[0]+f".{text_extension}"))
        shutil.copy(fname, outputfolder.joinpath(str(fname.name).rsplit(".",2)[0]+".json"))
        count += 1
        if verbose:
            print(f"{count} file copied:")
            print(f"{fname.name},{str(fname.name).rsplit('.',2)[0]+f'.{text_extension}'},{str(fname.name).rsplit('.',2)[0]+'.json'}")






