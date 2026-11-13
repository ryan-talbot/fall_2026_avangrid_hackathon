"""Chunked local AMI cache. Naive local meter-hour axis, no DST inference."""
from pathlib import Path
import zipfile, json
import numpy as np
import pandas as pd
from inventory import ROOT

def load():
    dest=ROOT/'data/processed'; dest.mkdir(exist_ok=True)
    path=dest/'ami.npy'
    if not (dest/'coverage.json').exists():
        a=np.lib.format.open_memmap(path, mode='w+', dtype='float32', shape=(35726,8760)); a[:]=np.nan
        stats={'rows':0,'excluded_rows':0,'duplicate_slots':0,'conflicting_slots':0}
        for p in sorted((ROOT/'data/raw').glob('*.zip')):
            with zipfile.ZipFile(p) as z:
                for name in z.namelist():
                    if not name.endswith('.csv'): continue
                    for c in pd.read_csv(z.open(name), chunksize=400000):
                        stats['rows']+=len(c)
                        c.columns=c.columns.str.lower()
                        h=(pd.to_datetime(c.usage_date)-pd.Timestamp('2025-09-01')).dt.days.to_numpy()*24+c.hour_ending.to_numpy()-1
                        ids=c.customer_number.to_numpy(); v=c.hourly_kwh.to_numpy(dtype='float32')
                        ok=(c.is_complete_hour.to_numpy()==1)&(c.interval_count.to_numpy()==4)&np.isfinite(v)&(h>=0)&(h<8760)&(ids>=1)&(ids<=35725)
                        stats['excluded_rows']+=int((~ok).sum())
                        ids,h,v=ids[ok],h[ok],v[ok]
                        keys=ids*8760+h
                        _,first=np.unique(keys,return_index=True)
                        stats['duplicate_slots']+=len(keys)-len(first)
                        ids,h,v=ids[first],h[first],v[first]
                        old=a[ids,h]; dup=np.isfinite(old)
                        stats['duplicate_slots']+=int(dup.sum()); stats['conflicting_slots']+=int((dup & (old!=v)).sum())
                        a[ids,h]=v
                    print('loaded',p.name,name,flush=True)
            a.flush()
        counts=np.array([np.isfinite(row).sum() for row in a])
        np.save(dest/'counts.npy',counts)
        stats.update(population_95=int((counts>=.95*8760).sum()),showcase_995=int((counts>=.995*8760).sum()))
        (dest/'coverage.json').write_text(json.dumps(stats,indent=2))
    return np.load(path,mmap_mode='r'), np.load(dest/'counts.npy')

if __name__=='__main__': load()
