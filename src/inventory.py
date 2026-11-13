"""Local input audit; never sends source data outside this machine."""
from pathlib import Path
import json, zipfile
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def inventory(full_crc=True):
    out = []
    for p in sorted((ROOT / 'data/raw').iterdir()):
        item = {'file': p.name, 'bytes': p.stat().st_size}
        if p.suffix == '.zip':
            with zipfile.ZipFile(p) as z:
                item['members'] = []
                for n in z.namelist():
                    if n.lower().endswith('.csv'):
                        with z.open(n) as f:
                            head = pd.read_csv(f, nrows=3)
                        item['members'].append({'name': n, 'columns': list(head.columns), 'sample': head.to_dict('records')})
                item['crc_bad_member'] = z.testzip() if full_crc else 'not tested'
                if full_crc and item['crc_bad_member'] is not None:
                    raise ValueError(f"CRC failed: {p.name}: {item['crc_bad_member']}")
        else:
            sheets = pd.read_excel(p, sheet_name=None)
            item['sheets'] = {k: {'rows':len(v), 'columns':list(v.columns), 'sample':v.head(3).astype(str).to_dict('records')} for k,v in sheets.items()}
        out.append(item)
    dest = ROOT / 'data/processed'
    dest.mkdir(exist_ok=True)
    (dest / 'inventory.json').write_text(json.dumps(out, indent=2, default=str))
    for item in out:
        print(item['file'], item['bytes'], 'bytes',
              f"{len(item['members'])} CSVs; CRC bad member={item['crc_bad_member']}" if 'members' in item else
              {k: {'rows':v['rows'],'columns':v['columns']} for k,v in item['sheets'].items()}, flush=True)

def materials():
    from pypdf import PdfReader
    found=[]
    for p in sorted((ROOT/'data/materials').glob('*.pdf')):
        reader=PdfReader(p)
        content='\n'.join(page.extract_text() or '' for page in reader.pages)
        if 'Hackathon Rubric Criteria' in content: role='rubric'
        elif 'Hackathon Data Dictionary' in content: role='data_dictionary'
        elif 'Final Submission Guidelines' in content: role='kickoff'
        elif 'Part 1: Customer Classification' in content: role='challenge'
        else: raise ValueError(f'Unidentified material: {p.name}')
        found.append({'file':p.name,'role':role,'pages':len(reader.pages)})
    if {x['role'] for x in found}!={'rubric','data_dictionary','kickoff','challenge'}:
        raise ValueError('Required organizer materials missing')
    dest=ROOT/'data/processed'; dest.mkdir(exist_ok=True)
    (dest/'materials_inventory.json').write_text(json.dumps(found,indent=2))
    print('Materials:',found,flush=True)

if __name__ == '__main__':
    inventory()
