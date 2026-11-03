#!/usr/bin/env python3
"""V3.5 additional checks: full-sample model and additive scale uncertainty.
Usage: python code/06_v35_public_additional_models.py --strict-events reproduction/rebuild/events_written_strict.csv --out reproduction/v35_extra_public
All outputs concern expert DCML labels, not human perception or causal effects.
"""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
ap=argparse.ArgumentParser()
ap.add_argument('--strict-events',required=True,type=Path)
ap.add_argument('--out',required=True,type=Path)
a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
df=pd.read_csv(a.strict_events)
assert len(df)==14740 and df.y.sum()==2084 and df.work_group.nunique()==85
df['log_gap']=np.log1p(df.harmonic_gap_qb.clip(lower=0))
formula=('y ~ prev_is_dominant * measure_downbeat + prev_secondary_dominant + '
         'prev_is_predominant + two_back_is_predominant + local_minor + '
         'same_localkey + log_gap + C(composer)')
def write_model(frame,formula,path):
    m=smf.glm(formula,data=frame,family=sm.families.Binomial()).fit(
        cov_type='cluster',cov_kwds={'groups':frame.work_group},maxiter=200)
    b=m.params;se=m.bse
    pd.DataFrame({'parameter':b.index,'log_odds_beta':b.values,'cluster_SE':se.values,
      'OR':np.exp(b.values),'OR_low_95':np.exp(b.values-1.96*se.values),
      'OR_high_95':np.exp(b.values+1.96*se.values),'p_value':m.pvalues.values,
      'n_events':len(frame),'work_clusters':frame.work_group.nunique(),
      'deviance':m.deviance,'null_deviance':m.null_deviance,
      'AIC':m.aic,'log_likelihood':m.llf,'residual_df':m.df_resid}).to_csv(path,index=False)
    k='prev_is_dominant:measure_downbeat'
    print(path.name,'n',len(frame),'OR',np.exp(m.params[k]))
sub=df[df.tonic_inverted==0].copy()
write_model(sub,formula,a.out/'S1_main_GLM.csv')
write_model(df,formula+' + tonic_inverted',a.out/'S8_full_sample_GLM.csv')
cell=sub.groupby(['prev_is_dominant','measure_downbeat']).y.agg(['size','sum','mean'])
cell.to_csv(a.out/'S6_observed_cells.csv')
p={(i,j):float(cell.loc[(i,j),'mean']) for i in (0,1) for j in (0,1)}
obs=(p[1,1]-p[1,0])-(p[0,1]-p[0,0])
byworks=[g[['prev_is_dominant','measure_downbeat','y']].to_numpy(dtype=int)
         for _,g in sub.groupby('work_group')]
rng=np.random.default_rng(20261102);draws=[]
for _ in range(3000):
    idx=rng.choice(len(byworks),len(byworks),replace=True)
    array=np.vstack([byworks[i] for i in idx]);rates={}
    for i in (0,1):
      for j in (0,1):
        z=array[(array[:,0]==i)&(array[:,1]==j),2]
        rates[i,j]=z.mean() if len(z) else np.nan
    value=(rates[1,1]-rates[1,0])-(rates[0,1]-rates[0,0])
    if np.isfinite(value):draws.append(value)
lo,hi=np.quantile(draws,[.025,.975])
pd.DataFrame([{'estimate_percentage_points':obs*100,
 'CI_lower_percentage_points':lo*100,'CI_upper_percentage_points':hi*100,
 'work_clusters':len(byworks),'bootstrap_draws':3000,'valid_draws':len(draws)}]).to_csv(
 a.out/'S9_additive_interaction.csv',index=False)
print('S9 estimate pp',obs*100,'95%CI',lo*100,hi*100)
