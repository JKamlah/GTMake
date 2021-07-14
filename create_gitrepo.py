from pathlib import Path
from shutil import move

import click
from git import Repo


@click.command()
@click.argument('repopath', nargs=1, type=click.Path(exists=True))
@click.option('--text-extension', default='gt.txt')
@click.option('-t', '--empty-textfiles', default=False, is_flag=True,
              help='Add empty textfiles to gitrepo and then replace')
@click.option('-r', '--readme-text', default='')
@click.option('-v', '--verbose', default=False, is_flag=True, help='Print more process information')
def create_gitrepo(repopath, text_extension, empty_textfiles, readme_text, verbose):
    """ Creates a gitrepo for the Ground Truth and adds a Readme file additional information.
        That repo can be used with GTCheck to manually check the Ground Truth results."""
    print(f"Create gitrepo for {repopath}")
    gt = Path(repopath)
    repo = Repo.init(gt)
    gtlines_path = gt.joinpath('gtlines')
    if not gtlines_path.exists():
        gtlines_path.mkdir(exist_ok=True, parents=True)
    add_readme(repo, gt.joinpath('README.md'), readme_text)
    for fname in gt.glob('*'):
        if fname.name.endswith('.md'):
            continue
        if 'cutinfo.txt' in fname.name:
            repo.index.add([str(fname.resolve())])
            repo.index.commit('ADD cutinfo.txt')
        elif fname.is_file():
            new_file = str(gtlines_path.joinpath(fname.name).resolve())
            if verbose:
                print(fname.name.rsplit('_', 1)[0])
            if empty_textfiles and f".{text_extension}" in new_file:
                Path(new_file).touch()
                repo.index.add([new_file])
                repo.index.commit(f"ADD {Path(new_file).name}")
            move(str(fname.absolute()), new_file)
            if f'.{text_extension}' not in new_file:
                repo.index.add([new_file])
                repo.index.commit(f"ADD {Path(new_file).name}")


def add_readme(repo, readme_path, readme_text):
    with open(readme_path, 'w') as fout:
        fout.write(readme_text)
    repo.index.add([str(readme_path.resolve())])
    repo.index.commit('ADD README')