"""Preserve the verified unshifted replay locally, with content hashes."""
from pathlib import Path
import hashlib
import json
import shutil
from inventory import ROOT

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()

def preserve():
    source=ROOT/'data/processed/original_showcase'
    dest=ROOT/'data/processed/baseline_unshifted_v1'
    if dest.exists():
        manifest=json.loads((dest/'baseline_manifest.json').read_text())
        for name,value in manifest['sha256'].items():
            if digest(dest/name)!=value: raise ValueError('Preserved baseline changed: '+name)
        return dest
    checks=json.loads((source/'input_checks.json').read_text())
    if not checks['expected_input_checks'] or not all(v['passed'] for v in checks['expected_input_checks'].values()):
        raise ValueError('A verified original showcase must exist before this milestone')
    results=json.loads((source/'showcase_results.json').read_text())
    for case in results['targets'].values():
        for name in ['home','shared']:
            if not case[name]['feasible'] or case[name]['max_cap_miss_kw']>1e-6:
                raise ValueError('Unshifted baseline is not verified feasible')
    shutil.copytree(source,dest)
    files={str(p.relative_to(dest)):digest(p) for p in sorted(dest.rglob('*')) if p.is_file()}
    manifest={'source':'data/processed/original_showcase','labels':results['labels'],'sha256':files}
    (dest/'baseline_manifest.json').write_text(json.dumps(manifest,indent=2))
    return dest

if __name__=='__main__': print(preserve())
