from pathlib import Path
from shutil import move
from git import Repo
import click

@click.command()
@click.argument('repopath', nargs=1, type=click.Path(exists=True))
@click.option('-t', '--empty-textfiles', default=False, is_flag=True, help='Add empty textfiles to gitrepo and then replace')
@click.option('-r', '--readme-text', default='')
@click.option('-v', '--verbose', default=False, is_flag=True, help='Print more process information')
def create_gitrepo(repopath, empty_textfiles, readme_text, verbose):
    print(f"Create gitrepo for {repopath}")
    gt = Path(repopath)
    repo = Repo.init(gt)
    gtlines_path = gt.joinpath('gtlines')
    if not gtlines_path.exists():
        gtlines_path.mkdir(exist_ok=True, parents=True)
    for fname in gt.glob('*'):
        if 'cutinfo.txt' in fname.name:
            repo.index.add([str(fname.resolve())])
            repo.index.commit(f"ADD cutinfo.txt")
        elif fname.is_file():
            new_file = str(gtlines_path.joinpath(fname.name).resolve())
            if verbose:
                print(fname.name.rsplit('_',1)[0])
            if empty_textfiles and '.gt.txt' in new_file:
                Path(new_file).touch()
                repo.index.add([new_file])
                repo.index.commit(f"ADD {Path(new_file).name}")
            move(str(fname.absolute()), new_file)
            if '.gt.txt' not in new_file:
                repo.index.add([new_file])
                repo.index.commit(f"ADD {Path(new_file).name}")
    if not gt.joinpath('README.md').exists():
        with open(gt.joinpath('README.md'), 'w') as fout:
            fout.write(readme_text)
        repo.index.add([str(gt.joinpath('README.md').resolve())])
        repo.index.commit(f"ADD README")
