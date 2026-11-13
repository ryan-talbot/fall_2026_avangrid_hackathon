r"""Create local code-only and deck-asset handoff ZIPs from explicit allowlists.

Never adds organizer data, meter lists or model caches to the code archive.
"""
import json
import zipfile
from pathlib import Path
from baseline import digest
from inventory import ROOT

DEST=ROOT/'data/processed/submission_package'

def source_files():
    root_names=['.gitignore','README.md','requirements.txt','requirements-analysis.txt','AGENTS.md','PROJECT_BRIEF.md','CHECKPOINT.md','MILESTONE.md','FINAL_VALIDATION.md','SUBMISSION_HANDOFF.md']
    config_names=['screening_rules.json','business_stress_plan.json','original_showcase.template.json','original_historical_fleet.template.json']
    files=[ROOT/n for n in root_names]+sorted((ROOT/'src').glob('*.py'))+[ROOT/'config'/n for n in config_names]
    return files

def main():
    verification=json.loads((DEST/'verification_report.json').read_text())
    if not verification['passed']:raise ValueError('Verify the handoff first')
    code=source_files()
    for p in code:
        if not p.is_file() or 'data' in p.relative_to(ROOT).parts:raise ValueError('Unsafe/missing code archive member: '+str(p))
    code_zip=DEST/'ClearGrid_code_submission.zip'
    with zipfile.ZipFile(code_zip,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for p in code:z.write(p,p.relative_to(ROOT).as_posix())
    assets=sorted((DEST/'figures').glob('*.png'))+sorted((DEST/'figures').glob('*.svg'))
    historic=ROOT/'data/processed/final_validation/figures'
    assets+=sorted(historic.glob('*.png'))+sorted(historic.glob('*.svg'))
    # Only anonymized/aggregate figures and the slide guide go into this LOCAL
    # asset ZIP. No original AMI files, raw IDs, reference lists or arrays.
    assets.append(ROOT/'SUBMISSION_HANDOFF.md')
    asset_zip=DEST/'ClearGrid_deck_evidence.zip'
    with zipfile.ZipFile(asset_zip,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for p in assets:
            prefix='verified_historical' if p.parent==historic else 'new_evidence'
            z.write(p,('SUBMISSION_HANDOFF.md' if p.name=='SUBMISSION_HANDOFF.md' else prefix+'/'+p.name))
    with zipfile.ZipFile(code_zip) as z:
        if z.testzip() is not None:raise ValueError('Code ZIP CRC failed')
        assert not any(n.startswith('data/') or n.endswith(('.npy','.npz','.xlsx','.csv','.pdf')) for n in z.namelist())
    with zipfile.ZipFile(asset_zip) as z:
        if z.testzip() is not None:raise ValueError('Asset ZIP CRC failed')
    manifest={'code_zip':str(code_zip.relative_to(ROOT)),'code_sha256':digest(code_zip),'code_members':[str(p.relative_to(ROOT)) for p in code],'deck_assets_zip':str(asset_zip.relative_to(ROOT)),'deck_assets_sha256':digest(asset_zip),'scope':'Both archives remain local and Git-ignored. Code ZIP contains no organizer inputs, meter lists or customer-level outputs. Asset ZIP contains the requested anonymized slide figures for the hackathon handoff only.','powerpoint':'Not assembled here; slide teammate must produce and submit the self-contained PowerPoint.'}
    (DEST/'package_manifest.json').write_text(json.dumps(manifest,indent=2))
    print('Code archive:',code_zip,'\nDeck assets:',asset_zip)

if __name__=='__main__':main()
