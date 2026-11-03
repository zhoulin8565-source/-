#!/usr/bin/env python3
"""Four-frame sensitivity estimates for expert-annotated DCML tonal arrivals."""
import sys,json,platform
from pathlib import Path
from importlib.metadata import version
import numpy as np,pandas as pd,statsmodels.api as sm,statsmodels.formula.api as smf
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score,log_loss,brier_score_loss,roc_auc_score

root=Path(__file__).resolve().parent.parent
inp=root/'rebuild';out=root/'results';out.mkdir(exist_ok=True)
names=['written_strict','written_secondary_target','all_endings_strict','all_endings_secondary_target']
formula=('y ~ prev_is_dominant * measure_downbeat + prev_secondary_dominant + prev_is_predominant + two_back_is_predominant + local_minor + same_localkey + log_gap + C(composer)')
cols=['prev_is_dominant','prev_secondary_dominant','prev_is_predominant','two_back_is_predominant','local_minor','same_localkey']
coef_rows=[];metric_rows=[];boots=[];pred_rows=[]
for name in names:
    df=pd.read_csv(inp/f'events_{name}.csv')
    df['log_gap']=np.log1p(df.harmonic_gap_qb.clip(lower=0))
    df['interaction']=df.prev_is_dominant*df.measure_downbeat
    assert len(df)>10000 and df['y'].isin([0,1]).all() and not df.duplicated(['corpus','piece','event_qb']).any()
    subset=df[df.tonic_inverted==0].copy()
    m=smf.glm(formula,data=subset,family=sm.families.Binomial()).fit(cov_type='cluster',cov_kwds={'groups':subset.work_group},maxiter=200)
    key='prev_is_dominant:measure_downbeat'
    b=float(m.params[key]);s=float(m.bse[key]);p=float(m.pvalues[key])
    coef_rows.append({'scenario':name,'n_all':len(df),'n_positive':int(df.y.sum()),
        'n_noninverted':len(subset),'work_groups':int(df.work_group.nunique()),
        'n_local_proxy':int((df.target_class=='secondary_target_proxy').sum()),
        'coef':b,'se':s,'interaction_OR':float(np.exp(b)),
        'OR_CI_low':float(np.exp(b-1.96*s)),'OR_CI_high':float(np.exp(b+1.96*s)),'p':p})
    feats={'F0_harmony_only':cols,'F3_both_context':cols+['measure_downbeat','log_gap'],
           'F4_explicit_interaction':cols+['measure_downbeat','log_gap','interaction']}
    for composer in sorted(df.composer.unique()):
        tr=df[df.composer!=composer];te=df[df.composer==composer]
        for label,features in feats.items():
            model=Pipeline([('imp',SimpleImputer(strategy='median')),
                ('scale',StandardScaler()),
                ('lr',LogisticRegression(C=1.,max_iter=3000,random_state=20261102))])
            model.fit(tr[features],tr.y)
            prob=model.predict_proba(te[features])[:,1]
            metric_rows.append({'scenario':name,'composer':composer,'model':label,
                'n':len(te),'positive':int(te.y.sum()),'works':int(te.work_group.nunique()),
                'AP':average_precision_score(te.y,prob),'log_loss':log_loss(te.y,prob),
                'Brier':brier_score_loss(te.y,prob),'ROC_AUC':roc_auc_score(te.y,prob)})
            pred_rows.append(pd.DataFrame({'scenario':name,'composer':composer,'model':label,
                'work_group':te.work_group.to_numpy(),'piece':te.piece.to_numpy(),
                'event_qb':te.event_qb.to_numpy(),'y':te.y.to_numpy(),'pred':prob}))
    print(name,len(df),int(df.y.sum()),'OR=',round(float(np.exp(b)),4),'p=',round(p,7),flush=True)

coef=pd.DataFrame(coef_rows);coef.to_csv(out/'adjusted_interaction_across_definitions.csv',index=False)
metrics=pd.DataFrame(metric_rows);metrics.to_csv(out/'LOCO_metrics_across_definitions.csv',index=False)
pred=pd.concat(pred_rows,ignore_index=True)
pred.to_csv(out/'LOCO_predictions_across_definitions.csv',index=False)
for name in names:
    for composer in sorted(pred.composer.unique()):
        rows=pred[(pred.scenario==name)&(pred.composer==composer)]
        a=rows[rows.model=='F0_harmony_only'][['work_group','piece','event_qb','y','pred']].rename(columns={'pred':'p0'})
        b=rows[rows.model=='F3_both_context'][['piece','event_qb','pred']].rename(columns={'pred':'p1'})
        m=a.merge(b,on=['piece','event_qb'],validate='one_to_one')
        assert len(m)==len(a)
        rng=np.random.default_rng(20261102);works=m.work_group.unique()
        bi={w:m.index[m.work_group==w].to_numpy() for w in works};boot=[]
        for _ in range(500):
            sampled=rng.choice(works,size=len(works),replace=True)
            idx=np.concatenate([bi[w] for w in sampled]);take=m.loc[idx]
            if take.y.nunique()<2:continue
            boot.append(average_precision_score(take.y,take.p1)-average_precision_score(take.y,take.p0))
        obs=average_precision_score(m.y,m.p1)-average_precision_score(m.y,m.p0)
        boots.append({'scenario':name,'composer':composer,'n_works':len(works),
            'AP_delta_F3_minus_F0':obs,'CI_025':float(np.quantile(boot,.025)),
            'CI_975':float(np.quantile(boot,.975)),'valid_boot':len(boot)})
pd.DataFrame(boots).to_csv(out/'work_cluster_AP_bootstrap_500.csv',index=False)
report={'status':'COMPLETED computational sensitivity analysis; not independent cadence validation',
        'source':'Pinned DCML composer-specific harmonies TSV ZIP','four_scenarios':names,
        'python':platform.python_version(),
        'package_versions':{x:version(x) for x in ['pandas','numpy','statsmodels','scikit-learn','patsy']},
        'notes':['Model tests concern expert annotations, not listener perception.',
                 'The secondary-target is a narrow automatic proxy, not independently adjudicated cadence.',
                 'All-endings coordinate is score indexing, not a reconstructed performance timeline.',
                 'Four composers cannot establish a population of musical styles.',
                 'Sensitivity models were explored after the original sample definition.'],
        'adjusted_interaction':coef_rows,'bootstrap_results':boots}
(out/'run_summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('DONE ->',out)
