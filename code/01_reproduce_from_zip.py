#!/usr/bin/env python3
"""Reproduce full four-frame results from a ZIP of the pinned DCML source repos."""
import argparse,subprocess,sys,zipfile,shutil
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--data-zip',type=Path,required=True)
p.add_argument('--out',type=Path,default=Path('./reproduction'))
a=p.parse_args()
out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
data=out/'source';data.mkdir(exist_ok=True)
with zipfile.ZipFile(a.data_zip) as z:
    for info in z.infolist():
        target=(data/info.filename).resolve()
        if not target.is_relative_to(data):raise RuntimeError('Unsafe ZIP path')
    z.extractall(data)
code=Path(__file__).resolve().parent
subprocess.run([sys.executable,str(code/'02_rebuild_alternative_frames.py'),'--data',str(data),'--out',str(out/'rebuild')],check=True)
fit_dir=out/'code';fit_dir.mkdir(exist_ok=True)
shutil.copy2(code/'03_fit_four_frames.py',fit_dir/'run_fit.py')
subprocess.run([sys.executable,str(fit_dir/'run_fit.py')],check=True)
subprocess.run([sys.executable,str(code/'04_freeze_source.py'),'--data',str(data),'--out',str(out/'provenance')],check=True)
print('Reproduced outputs:',out)
