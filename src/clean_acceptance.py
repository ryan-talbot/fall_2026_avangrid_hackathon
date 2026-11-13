"""Run the final acceptance with a separately installed isolated environment.

Create/install that environment using the README commands first. No package
installation, raw-data upload, or original checkpoint regeneration occurs here.
"""
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime,timezone
import hashlib

ROOT=Path(__file__).resolve().parents[1]

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def normalized(lines):
    return {s.strip().lower().replace('_','-') for s in lines if s.strip() and not s.startswith('#')}

def main():
    env=ROOT/'data/processed/clean_environment/venv';python=env/'Scripts/python.exe'
    cfg=(env/'pyvenv.cfg').read_text().lower()
    if 'include-system-site-packages = false' not in cfg:raise ValueError('Acceptance environment must exclude development/global site packages')
    freeze=subprocess.check_output([str(python),'-m','pip','freeze'],cwd=ROOT,text=True)
    if normalized(freeze.splitlines())!=normalized((ROOT/'requirements-lock.txt').read_text().splitlines()):raise ValueError('Isolated environment differs from complete requirements-lock.txt')
    result_path=ROOT/'data/processed/submission_package/clean_environment_acceptance.json'
    result_path.write_text(json.dumps({'passed':False,'state':'isolated acceptance running'},indent=2))
    completed=subprocess.run([str(python),str(ROOT/'src/finalize.py'),'--reuse-input-audit'],cwd=ROOT)
    report={'passed':completed.returncode==0,'completed_utc':datetime.now(timezone.utc).isoformat(),'python':str(python.relative_to(ROOT)),'isolated_site_packages':True,'lock_sha256':sha(ROOT/'requirements-lock.txt'),'installed_packages':sorted(normalized(freeze.splitlines())),'command':'data/processed/clean_environment/venv/Scripts/python.exe src/finalize.py --reuse-input-audit','exit_code':completed.returncode,'scope':'Full final acceptance in a separately created venv with independently installed locked packages. Uses authorized local audited caches and preserved checkpoints; not a second full raw ingestion or a different-machine test.'}
    if completed.returncode==0:report['release_acceptance_sha256']=sha(ROOT/'data/processed/submission_package/release_acceptance.json')
    result_path.write_text(json.dumps(report,indent=2))
    print('Isolated environment acceptance:',report['passed']);sys.exit(completed.returncode)

if __name__=='__main__':main()
