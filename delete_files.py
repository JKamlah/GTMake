import glob
import os
from pathlib import Path

import click
from tqdm import tqdm


@click.command()
@click.argument('list-of-files', nargs=1, type=click.Path(exists=True))
@click.option('-v', '--verbose', default=False, is_flag=True, help='Print more process information')
def delete_files_with_list(list_of_files, verbose):
    """ Deletes files provided by an list."""
    with open(list_of_files, "r") as fin:
        for fname in tqdm(fin.readlines()):
            if fname.strip() == "":
                continue
            if verbose:
                print(fname)
            for delfname in glob.glob(f"./{fname.strip().split('.')[0]}*"):
                if verbose:
                    print(delfname)
                os.remove(delfname)


@click.command()
@click.option('-e', '--image-extension', default='png')
@click.option('--text-extension', default='gt.txt')
@click.option('-v', '--verbose', default=False, is_flag=True, help='Print more process information')
def delete_files_without_textfiles(image_extension, text_extentsion, verbose):
    """ Deletes image and json files if no equivalent textfile is in the path."""
    images = set([img.split(".")[0] for img in glob.glob(f"*.{image_extension}")])
    txt = set([txt.split(".")[0] for txt in glob.glob(f"*.{text_extentsion}")])
    for delname in tqdm(txt.difference(images)):
        fname = Path(delname)
        if verbose:
            print(f"All files starting with {str(fname.absolute()).split('.', 1)[0]} will be removed:")
        for delfname in glob.glob(f"{str(fname.absolute()).split('.', 1)[0]}*"):
            if verbose:
                print(delfname)
            os.remove(delfname)


@click.command()
@click.argument('gtpath', nargs=1, type=click.Path(exists=True))
@click.option('-e', '--image-extension', default='png')
@click.option('--text-extension', default='gt.txt')
@click.option('-v', '--verbose', default=False, is_flag=True, help='Print more process information')
def delete_gitrepo_files_without_textfiles(gtpath, image_extension, text_extentsion, verbose):
    """ Deletes image and json files if no equivalent textfile is in the repo."""
    from git import Repo
    repo = Repo(gtpath, search_parent_directories=True)
    images = set([img.split(".")[0] for img in glob.glob(f"*.{image_extension}")])
    txt = set([txt.split(".")[0] for txt in glob.glob(f"*.{text_extentsion}")])
    for delname in tqdm(txt.difference(images)):
        fname = Path(delname)
        if verbose:
            print(f"All files starting with {str(fname.absolute()).split('.', 1)[0]} will be removed:")
        for delfname in glob.glob(f"{str(fname.absolute()).split('.', 1)[0]}*"):
            if verbose:
                print(delfname)
            os.remove(delfname)
            repo.index.add([delfname.resolve()])
            repo.index.commit(f"DELETE {delname}")


@click.command()
@click.argument('gtpath', nargs=1, type=click.Path(exists=True))
@click.option('--text-extension', default='gt.txt')
@click.option('-v', '--verbose', default=False, is_flag=True, help='Print more process information')
def delete_gitrepo_files_with_empty_textfiles(gtpath, text_extentsion, verbose):
    """ Deletes image and json files if the equivalent textfile is empty."""
    from git import Repo
    repo = Repo(gtpath, search_parent_directories=True)
    txtfiles = set([txt.split(".")[0] for txt in glob.glob(f"*.{text_extentsion}")])
    for delname in tqdm(txtfiles):
        if os.stat("file").st_size != 0:
            continue
        fname = Path(delname)
        if verbose:
            print(f"All files starting with {str(fname.absolute()).split('.', 1)[0]} will be removed:")
        for delfname in glob.glob(f"{str(fname.absolute()).split('.', 1)[0]}*"):
            if verbose:
                print(delfname)
            os.remove(delfname)
            repo.index.add([delfname.resolve()])
            repo.index.commit(f"DELETE {delname}")
