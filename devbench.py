import os
import shutil
import stat
import statistics
import contextlib
import time
import pathlib
import subprocess
from collections import defaultdict
import zipfile

# down load archives and place in same folder as this script
# https://github.com/facebook/react/archive/refs/tags/v19.1.1.zip
# https://github.com/vuejs/vue/archive/refs/tags/v2.7.16.zip
# reference_archive = "./vue-2.7.16.zip"
reference_archive = "./react-19.1.1.zip"
target_dir = "testrun"

runs=10

extra_content="""
.^)>=................     .   . ..    .......=^)]^
~{####<-.............       .      .   ...*}%#{{{#
:{{[[#%@}~...........      .   .     ...(@@%%{[]}#
.>{[}}{%@@#-..........               .(%%%#})>()}}
.:}]))(]{%%%#*...... .  .          .>%##{}]<*+^({*
..){])]}{#%@%%{#[-........     ..>{{%@@{{}](<<)[}.
..-{}[[}{##%@@}#%%[>**=:..-*>^+[%@%%@@%##}]((}{%>.
...<}}}{#%@@@@%@@%%}}[[())]}{#%%%@@@@%%%##{[(]}#:.
...-{}{%%%@@@@@@%%%#{{{#}[{###%%%@%@%@%%{{[[[[{^..
...-}}[}%%%@@@%%#{#%%%%%%%%%@%%%%%%#%@@%#{#}[}[~..
...^{[]#%%%%####%%%%@@@@@@@@@@@@@%##{{#%%###[[}:..
+==)@@{}#%%#][##%%@@@@@@@@@@@@@@%##{{#}[{{{}}##:..
+^<}@@@#}{[<>]}{##%@@@@@@@@@@@@%#####}((([]#%@)...
<]}#%@#}]<]<^)}##%%@@@@@@@@@@@@%%@%%{[)^())#%%}:..
]{{##{()]}}(]}#%@@@@@@@@@@@@@@@@@@@%%{}((}[]}%#*..
}{###[}}{#%{(}{#}%{@@@@@@@@@@@@@}%#][{^}#%#{}}#-..
######{(]{%#(>{{{)<#%@@@@@@@@@%{<]}}}*)}{]([###-..
#%#%%%#}{%%@#]<<>]{##@@@@%%@@@%{#}](]}##{}([#%{:..
@%%%%%%##%%@@%%%%#%%%@@%}}}#%@@%%%%%%%%{}{{{%%]...
@@@%%%%%%%%@@@%@%%%@@@@[>^><#@@}}#%%##%%%%%#%#+...
@@@%%%%%%%%%%%%%%#%####)>^^*(}[]](]}}{%%%#%%#>....
@@@@@%%%%%%%%%@%%#%%##}}}}}}{[}#{}##%%%%#%%#+.....
@@@@@@@@@%%%%%%##%%@%#%@%##%@%{%%%%%@@%%%%#>......
@@@@@@@@@@@@@#%%@@@@@%%%####%%%@@@@@%##%%#+.......
@@@@@@@@@@@@%%##%%@@@@%%{#%{%%%%@@@{%%%%%~........
@@@@@@@@@@@@@@@%%#######{](}#%#####%#}#%=.........
@@@@@@@@@@@@@@@@@@@@%%%%%##%#%%%%@@%#>-...........
@@@@@@@@@@@@@@@@@@@@@@@%%%%%%%@@@@%%#=............
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%%%~............
"""


class Stopwatch:
    def __init__(self):
        self._stats = defaultdict(list)

    @contextlib.contextmanager
    def measure(self, label : str):
        start = time.perf_counter()
        try:
            yield start
        finally:
            self._stats[label].append(time.perf_counter() - start)

    def __str__(self):
        lines = []
        lines.append(f"label,min(seconds),max(seconds),mean(seconds),std deviation,median(seconds)")
        for k, v in self._stats.items():
            lines.append(f"{k},{min(v)},{max(v)},{statistics.mean(v)},{statistics.stdev(v)},{statistics.median(v)}")

        return "\n".join(lines)


def retry_delete(func, path, exc_info):
    if isinstance(exc_info[1], PermissionError):
        os.chmod(path, stat.S_IWRITE)
        func(path)
    else:
        raise exc_info[1]

def do_run(stopwatch : Stopwatch):

    # remove target dir if exists
    if pathlib.Path(target_dir).exists():
        shutil.rmtree(target_dir, onerror=retry_delete)

    with stopwatch.measure("unzip"):
        # # unzip reference_archive inside target_dir
        with zipfile.ZipFile(reference_archive, 'r') as zip_ref:
            zip_ref.extractall(target_dir)
     #   subprocess.run(["unzip", reference_archive, "-d", target_dir], capture_output=True, stdout=None, stderr=None)

    with stopwatch.measure("git init"):
        # git init target_dir
        subprocess.run(["git", "init", target_dir], capture_output=True)
        subprocess.run(["git", "config", "core.autocrlf", "false"], cwd=target_dir, capture_output=True)


    with stopwatch.measure("git add"):
        # git add in target_dir
        subprocess.run(["git", "add", "."], capture_output=True, cwd=target_dir)

    with stopwatch.measure("git initial commit"):
        # initial git commit in target_dir
        subprocess.run(["git", "commit", "-m", "initial commit"], capture_output=True, cwd=target_dir)

    with stopwatch.measure("modify all files"):
        # recursively go through target_dir excluding dirs starting with a '.' and add extra content to all files
        r = pathlib.Path(target_dir)
        dirs = [ target_dir ]
        i = 0
        for d in dirs:
            for f in pathlib.Path(d).iterdir():
                if f.name.startswith("."):
                    continue
                if f.is_file():
                    with f.open("a") as fa:
                        fa.write(extra_content)
                        i+=1
                elif f.is_dir():
                    dirs.append(f.absolute())
        print(f"modified {i} files")

    with stopwatch.measure("git stash"):
        # git stash in target_dir
        subprocess.run(["git", "stash"], cwd=target_dir, capture_output=True)

    with stopwatch.measure("git stash pop"):
        # git stash pop in target_dir
        subprocess.run(["git", "stash", "pop"], cwd=target_dir, capture_output=True)

    with stopwatch.measure("git add modified"):
        # git add modified in target_dir
        subprocess.run(["git", "add", "-u"], cwd=target_dir, capture_output=True)

    with stopwatch.measure("git status"):
        # git status in target_dir
        subprocess.run(["git", "status"], cwd=target_dir, capture_output=True)

    with stopwatch.measure("git second commit"):
        # initial git commit in target_dir
        subprocess.run(["git", "commit", "-m", "cats!"], cwd=target_dir, capture_output=True)

    with stopwatch.measure("recursive remove"):
        shutil.rmtree(target_dir, onerror=retry_delete)


def run_bench():

    stopwatch = Stopwatch()
    do_run(stopwatch)

    stopwatch = Stopwatch()
    for i in range(runs):
        do_run(stopwatch)

    print(stopwatch)

if __name__ == "__main__":
    run_bench()
