#!/usr/bin/env python3
"""Verify the local five-corpus snapshot using pinned public Git-tree fingerprints."""
import argparse,hashlib,csv,json
from pathlib import Path
SHAS={
'beethoven_piano_sonatas':('ea7181bff88abc8713257234f7ec4033178c57a9','b6499d863ac9f81e'),
'cpe_bach_keyboard':('4b3511eab12b5fbfc7aa5c75819ee02225430da8','fb395b09b3c29301'),
'jc_bach_sonatas':('ac9fd07905eb62c3d8cfbd96811491170a216232','5713bbb1260b67d6'),
'kozeluh_sonatas':('23c1983a48809647af1a08d54b1fade39ec93995','cabbef3d048719c9'),
'mozart_piano_sonatas':('5337257a5318711e6302cfe85c3f1a6ade3c6271','0fcaadf799e5a0d4')}
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--data',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    rows=[];reports=[]
    for name,(commit,expected) in SHAS.items():
        root=a.data/name
        files=sorted([root/'metadata.tsv',*(root/'harmonies').glob('*.harmonies.tsv')])
        pairs=[]
        for f in files:
            b=f.read_bytes()
            git=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
            rel=f.relative_to(root).as_posix();pairs.append((rel,git))
            rows.append({'repo':name,'path':rel,'sha256':hashlib.sha256(b).hexdigest(),
                         'git_blob_sha1':git,'bytes':len(b),'pinned_commit':commit})
        text=''.join(x+'\t'+y+'\n' for x,y in sorted(pairs))
        h=0xcbf29ce484222325
        for ch in text:h=((h^ord(ch))*0x100000001b3)&((1<<64)-1)
        fp=f'{h:016x}'
        assert fp==expected,(name,fp,expected)
        reports.append({'repo':name,'count':len(files),'commit':commit,'fingerprint':fp,'verified':True})
    with (a.out/'file_hashes.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    (a.out/'provenance.json').write_text(json.dumps({'source_files':len(rows),'repos':reports},indent=2))
    print('Matched 267 source files against pinned Git-tree fingerprints.')
if __name__=='__main__':main()
