import json
from pathlib import Path

portal = Path(r"C:\Users\labcl\Desktop\provas\portal")
provas_dir = portal / "provas"

pdfs = {}
for f in provas_dir.glob("*.pdf"):
    key = f.name.split("_")[0]
    pdfs[key] = f.name

alunos = json.loads((portal / "alunos.json").read_text(encoding="utf-8"))

for a in alunos:
    if a["prova"] is not None:
        key = f'{a["prova"]:02d}'
        a["arquivo"] = pdfs.get(key, "")
    else:
        a["arquivo"] = ""

(portal / "alunos.json").write_text(json.dumps(alunos, ensure_ascii=False, indent=2), encoding="utf-8")
print("Updated alunos.json with filenames")
for a in alunos[:3]:
    print(f'  {a["nome"]} -> {a["arquivo"]}')
