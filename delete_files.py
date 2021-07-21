import glob
import os
from pathlib import Path

import click
from tqdm import tqdm


@click.group()
def cli():
    pass

@cli.command()
@click.argument('gtpath', nargs=1, type=click.Path(exists=True))
@click.argument('list-of-files', nargs=1, type=click.Path(exists=True))
@click.option('-v', '--verbose', default=False, is_flag=True, help='Print more process information')
def files_via_list(gtpath, list_of_files, verbose):
    """ Deletes files provided by an list."""
    with open(list_of_files, "r") as fin:
        for fname in tqdm(fin.readlines()):
            if fname.strip() == "":
                continue
            if verbose:
                print(fname)
            for delfname in glob.glob(os.path.join(gtpath,fname.strip().split('.')[0]+"*")):
                if verbose:
                    print(delfname)
                os.remove(delfname)


@cli.command()
@click.argument('gtpath', nargs=1, type=click.Path(exists=True))
@click.option('-e', '--image-extension', default='png')
@click.option('--text-extension', default='gt.txt')
@click.option('-v', '--verbose', default=False, is_flag=True, help='Print more process information')
def files_without_textfiles(gtpath, image_extension, text_extension, verbose):
    """ Deletes image and json files if no equivalent textfile is in the path."""
    images = set([str(img.resolve()).rsplit(".", len(img.suffixes))[0] for img in gtpath.rglob(f"*.{image_extension}")])
    txt = set([str(txt.resolve()).rsplit(".", len(txt.suffixes))[0] for txt in gtpath.rglob(f"*.{text_extension}")])
    for delname in tqdm(txt.difference(images)):
        fname = Path(delname)
        if verbose:
            print(f"All files starting with {str(fname.absolute()).split('.', 1)[0]} will be removed:")
        for delfname in glob.glob(f"{str(fname.absolute()).split('.', 1)[0]}*"):
            if verbose:
                print(delfname)
            os.remove(delfname)


@cli.command()
@click.argument('gtpath', nargs=1, type=click.Path(exists=True))
@click.option('-e', '--image-extension', default='png')
@click.option('--text-extension', default='gt.txt')
@click.option('-v', '--verbose', default=False, is_flag=True, help='Print more process information')
def gitrepo_without_textfiles(gtpath, image_extension, text_extension, verbose):
    """ Deletes image and json files if no equivalent textfile is in the repo."""
    from git import Repo
    gtpath = Path(gtpath)
    repo = Repo(str(gtpath.resolve()), search_parent_directories=True)
    images = set([str(img.resolve()).rsplit(".", len(img.suffixes))[0] for img in gtpath.rglob(f"*.{image_extension}")])
    txt = set([str(txt.resolve()).rsplit(".", len(txt.suffixes))[0] for txt in gtpath.rglob(f"*.{text_extension}")])
    for fnames in tqdm(txt.difference(images)):
        if verbose:
            print(f"All files starting with {fnames.split('.', 1)[0]} will be removed:")
        for del_fname in glob.glob(f"{fnames.split('.', 1)[0]}*"):
            if verbose:
                print(del_fname)
            os.remove(del_fname)
            repo.index.remove(del_fname)
            repo.index.commit(f"DELETE {del_fname}")


@cli.command()
@click.argument('gtpath', nargs=1, type=click.Path(exists=True))
@click.option('--text-extension', default='gt.txt')
@click.option('-v', '--verbose', default=False, is_flag=True, help='Print more process information')
def gitrepo_with_empty_textfiles(gtpath, text_extension, verbose):
    """ Deletes image and json files if the equivalent textfile is empty."""
    from git import Repo
    repo = Repo(gtpath, search_parent_directories=True)
    txt = set([str(txt.resolve()).rsplit(".", len(txt.suffixes))[0] for txt in gtpath.rglob(f"*.{text_extension}")])
    for fnames in tqdm(txt):
        if os.stat("file").st_size != 0:
            continue
        if verbose:
            print(f"All files starting with {fnames.split('.', 1)[0]} will be removed:")
        for del_fname in glob.glob(f"{fnames.split('.', 1)[0]}*"):
            if verbose:
                print(del_fname)
            os.remove(del_fname)
            repo.index.remove(del_fname)
            repo.index.commit(f"DELETE {del_fname}")

if __name__=='__main__':
    cli()
