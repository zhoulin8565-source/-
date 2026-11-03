#!/usr/bin/env python3
"""Rebuild positive AND negative DCML cadence event frames from original TSVs.
Alternative frames are score-index sensitivities, not independently verified cadences.
"""
import argparse,csv,json,re,hashlib
from fractions import Fraction
from pathlib import Path
from collections import Counter,defaultdict
ROOTS={'mozart_piano_sonatas','beethoven_piano_sonatas','cpe_bach_keyboard','jc_bach_sonatas'}

def rows(p):
    with p.open('r',encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
def num(s):
    try:return float(Fraction(str(s).strip()))
    except (ValueError,TypeError,ZeroDivisionError):return None
def tonic(x):return bool(re.match(r'^[Ii](?:$|[0-9#b(])',str(x or '').strip()))
def dominant(x):return bool(re.match(r'^V(?:$|[0-9#b(])',str(x or '').strip()))
def secondary(row):return dominant(row.get('numeral')) and (bool((row.get('relativeroot') or '').strip()) or '/' in (row.get('chord') or ''))
def primary(row):return dominant(row.get('numeral')) and not secondary(row)
def predom(x):return bool(re.match(r'^(ii|II|IV|iv)(?:$|[0-9#b(])',str(x or '').strip()))
def normalize_target(raw):
    x=str(raw or '').strip()
    match=re.match(r'^(#|b)?(i{1,3}|iv|v|vi{1,2}|vii|I{1,3}|IV|V|VI{1,2}|VII)(?=$|[0-9(#b])',x)
    return (match.group(1) or '')+match.group(2) if match else ''
def licensed_applied_target(curr,prev):
    if not secondary(prev):return False
    root=normalize_target(prev.get('relativeroot'));target=normalize_target(curr.get('numeral'))
    return bool(root and target and root==target)
COLUMNS=['corpus','composer','piece','work_group','year','event_qb','y','cadence_type',
'prev_is_dominant','prev_secondary_dominant','same_localkey','prev_is_predominant',
'two_back_is_predominant','tonic_inverted','local_minor','measure_downbeat',
'harmonic_gap_qb','score_bass_motion_semitones','score_top_motion_semitones',
'raw_numeral','previous_numeral','previous_chord','previous_relativeroot','tonic_localkey',
'frame','target_class']
def make_frame(root,scenario):
    time_field='quarterbeats_all_endings' if scenario.startswith('all_endings') else 'quarterbeats'
    allow_local=scenario.endswith('secondary_target')
    events=[];tally=Counter();bycorpus=defaultdict(Counter);file_manifest=[]
    for folder in sorted(root.iterdir()):
        if not folder.is_dir() or folder.name not in ROOTS:continue
        metadata={r['piece']:r for r in rows(folder/'metadata.tsv')}
        for hp in sorted((folder/'harmonies').glob('*.harmonies.tsv')):
            piece=hp.name.removesuffix('.harmonies.tsv');raw=rows(hp);md=metadata.get(piece,{})
            composer=(md.get('composer') or '').strip()
            title=(md.get('workTitle') or '').strip();work_num=(md.get('workNumber') or '').strip()
            work_id=' | '.join(x for x in (work_num,title) if x) or piece
            group=f'{folder.name}::{composer}::{work_id}'
            file_manifest.append({'corpus':folder.name,'piece':piece,'sha256':hashlib.sha256(hp.read_bytes()).hexdigest()})
            grouped=defaultdict(list)
            for r in raw:
                t=num(r.get(time_field))
                if t is None:
                    tally['missing_selected_timeline']+=1
                    if r.get('cadence') in ('PAC','IAC'):tally['positive_missing_selected_timeline']+=1
                    continue
                grouped[t].append(r)
            ordered=[]
            for t,arr in sorted(grouped.items()):
                variants={(r.get('numeral') or '',r.get('localkey') or '',r.get('cadence') or '') for r in arr}
                if len(variants)>1:
                    tally['ambiguous_onset_removed']+=len(arr)
                    tally['ambiguous_positive_removed']+=sum(r.get('cadence') in ('PAC','IAC') for r in arr)
                    continue
                ordered.append((t,arr[0]))
            for i,(t,curr) in enumerate(ordered):
                if i==0:tally['no_previous']+=1;continue
                prev_t,prev=ordered[i-1];is_main=tonic(curr.get('numeral'))
                is_other=(not is_main) and allow_local and licensed_applied_target(curr,prev)
                if not (is_main or is_other):
                    if curr.get('cadence') in ('PAC','IAC'):tally['excluded_positive_outside_target_class']+=1
                    continue
                label=(curr.get('cadence') or '').strip()
                if label not in ('PAC','IAC',''):tally['other_cadence_excluded']+=1;continue
                if not (prev.get('numeral') or '').strip() or not (curr.get('numeral') or '').strip():
                    tally['missing_numeral_context']+=1;continue
                local=(curr.get('localkey') or '').strip()
                if not local or not composer:tally['missing_local_key_or_composer']+=1;continue
                gap=t-prev_t
                if gap<0:tally['negative_onset_gap']+=1;continue
                met=num(curr.get('mc_onset'))
                if met is None:tally['missing_mc_onset']+=1;continue
                fb=(curr.get('figbass') or '').strip()
                r={'corpus':folder.name,'composer':composer,'piece':piece,'work_group':group,
                   'year':md.get('composed_start') or '', 'event_qb':t,'y':int(label in ('PAC','IAC')),
                   'cadence_type':label or 'NONE','prev_is_dominant':int(primary(prev)),
                   'prev_secondary_dominant':int(secondary(prev)),
                   'same_localkey':int((prev.get('localkey') or '').strip()==local),
                   'prev_is_predominant':int(predom(prev.get('numeral'))),
                   'two_back_is_predominant':int(predom(ordered[i-2][1].get('numeral'))) if i>=2 else 0,
                   'tonic_inverted':int(bool(fb) and fb!='7'),
                   'local_minor':int(local[0].islower()),
                   'measure_downbeat':int(met==0),'harmonic_gap_qb':gap,
                   'score_bass_motion_semitones':'','score_top_motion_semitones':'',
                   'raw_numeral':curr.get('numeral') or '',
                   'previous_numeral':prev.get('numeral') or '',
                   'previous_chord':prev.get('chord') or '',
                   'previous_relativeroot':prev.get('relativeroot') or '',
                   'tonic_localkey':local,'frame':scenario,
                   'target_class':'I_or_i' if is_main else 'secondary_target_proxy'}
                events.append(r);tally['included_positive' if r['y'] else 'included_negative']+=1
                bycorpus[folder.name]['positives']+=r['y'];bycorpus[folder.name]['events']+=1
    return events,tally,bycorpus,file_manifest
def main():
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--strict-reference',type=Path,default=None)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    scenarios=('written_strict','written_secondary_target','all_endings_strict','all_endings_secondary_target')
    summary={};manifest_all=[]
    for name in scenarios:
        ev,tally,by,manifest=make_frame(a.data.expanduser(),name)
        if not ev:raise RuntimeError(f'{name} yielded no events')
        file=a.out/f'events_{name}.csv'
        with file.open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=COLUMNS);w.writeheader();w.writerows(ev)
        keys=[(r['corpus'],r['piece'],r['event_qb']) for r in ev]
        if len(keys)!=len(set(keys)):raise RuntimeError(f'Duplicate event keys in {name}')
        summ={'n':len(ev),'positive':sum(r['y'] for r in ev),
              'noninverted':sum(r['tonic_inverted']==0 for r in ev),
              'works':len(set(r['work_group'] for r in ev)),
              'composers':len(set(r['composer'] for r in ev)),
              'secondary_target_proxy_n':sum(r['target_class']=='secondary_target_proxy' for r in ev),
              'excluded_source_counts':dict(tally),
              'bycorpus':{k:dict(v) for k,v in by.items()},'file':str(file)}
        summary[name]=summ
        if name=='written_strict':manifest_all=manifest
    if a.strict_reference:
        with a.strict_reference.open('r',encoding='utf-8-sig',newline='') as f:old=list(csv.DictReader(f))
        new=summary['written_strict'];new['reference_n']=len(old)
        new['reference_positive']=sum(int(x['y']) for x in old)
        new['reference_count_gate_passed']=new['n']==len(old) and new['positive']==sum(int(x['y']) for x in old)
    (a.out/'full_event_frame_comparison.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
    with (a.out/'source_harmonies_sha256.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=['corpus','piece','sha256']);w.writeheader();w.writerows(manifest_all)
    print(json.dumps(summary,indent=2,ensure_ascii=False))
    print('NOTE: alternative frames are exploratory, not independent cadence verification.')
if __name__=='__main__':main()
