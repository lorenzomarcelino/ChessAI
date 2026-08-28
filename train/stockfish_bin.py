"""Localiza ou baixa o binário do Stockfish (só para gerar rótulos de treino)."""

import os
import platform
import shutil
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / 'tools'
STOCKFISH_EXE = TOOLS / ('stockfish.exe' if os.name == 'nt' else 'stockfish')

RELEASE = 'sf_17.1'
ASSET = {
    'windows': 'stockfish-windows-x86-64-avx2.zip',
    'linux': 'stockfish-ubuntu-x86-64-avx2.tar',
    'darwin': 'stockfish-macos-x86-64.tar',
}


def _platform_key():
    system = platform.system().lower()
    if system.startswith('win'):
        return 'windows'
    if system == 'darwin':
        return 'darwin'
    return 'linux'


def _download_url():
    name = ASSET[_platform_key()]
    return f'https://github.com/official-stockfish/Stockfish/releases/download/{RELEASE}/{name}'


def find_stockfish(explicit=None):
    if explicit:
        path = Path(explicit)
        if path.is_file():
            return path
        raise FileNotFoundError(f'Stockfish não encontrado: {path}')
    env = os.environ.get('STOCKFISH_PATH')
    if env and Path(env).is_file():
        return Path(env)
    if STOCKFISH_EXE.is_file():
        return STOCKFISH_EXE
    which = shutil.which('stockfish')
    if which:
        return Path(which)
    return None


def ensure_stockfish(explicit=None):
    found = find_stockfish(explicit)
    if found is not None:
        return found
    print('Stockfish não encontrado. baixando binário oficial…', flush=True)
    return download_stockfish()


def download_stockfish():
    TOOLS.mkdir(parents=True, exist_ok=True)
    url = _download_url()
    print(f'baixando {url}', flush=True)
    suffix = '.zip' if url.endswith('.zip') else '.tar'
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / f'stockfish{suffix}'
        urllib.request.urlretrieve(url, archive)
        extract = Path(tmp) / 'out'
        extract.mkdir()
        if suffix == '.zip':
            with zipfile.ZipFile(archive) as zf:
                zf.extractall(extract)
        else:
            with tarfile.open(archive) as tf:
                tf.extractall(extract)
        exe = _find_extracted_binary(extract)
        if exe is None:
            raise RuntimeError('não achei o executável do Stockfish no arquivo baixado')
        dest = STOCKFISH_EXE
        shutil.copy2(exe, dest)
        dest.chmod(dest.stat().st_mode | 0o111)
    print(f'Stockfish em {dest}', flush=True)
    return dest


def _find_extracted_binary(root):
    exes = []
    for path in root.rglob('*'):
        if not path.is_file():
            continue
        name = path.name.lower()
        if 'stockfish' in name and path.suffix.lower() in ('', '.exe'):
            if name.endswith('.md') or name.endswith('.txt'):
                continue
            exes.append(path)
    if not exes:
        return None
    prefer = [p for p in exes if p.suffix.lower() == '.exe'] if os.name == 'nt' else exes
    return (prefer or exes)[0]


if __name__ == '__main__':
    path = ensure_stockfish(sys.argv[1] if len(sys.argv) > 1 else None)
    print(path)
