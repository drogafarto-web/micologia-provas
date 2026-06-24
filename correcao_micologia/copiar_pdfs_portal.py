"""Copia PDFs corrigidos para portal/provas/ usando matrícula. Remove Luiza, ALUNO TESTE, Mariah do JSON."""

import json, shutil
from pathlib import Path

BASE = Path(r"C:\Users\labcl\Desktop\04_Provas")
SRC = BASE / "correcao_micologia" / "provas_corrigidas"
DST = BASE / "portal" / "provas"
MAP_PATH = BASE / "portal" / "mapeamento_portal_correto.json"
ALUNOS_PATH = BASE / "portal" / "alunos.json"

DRY_RUN = False  # Mude para False para executar de verdade

# 1. Filtrar alunos.json (remover Luiza, TESTE, Mariah)
alunos = json.load(open(ALUNOS_PATH, encoding="utf-8"))
removidos = []
filtrados = []
for a in alunos:
    mat = a.get("matricula", "")
    if mat in ("221-000703", "000-000001"):  # Luiza, ALUNO TESTE
        removidos.append((mat, a.get("nome")))
        continue
    if not a.get("prova"):  # Mariah ou outros sem prova
        removidos.append((mat, a.get("nome")))
        continue
    filtrados.append(a)

print(f"Alunos.json: {len(alunos)} -> {len(filtrados)} (removidos: {len(removidos)})")
for r in removidos:
    print(f"  - {r[0]} {r[1]}")

if not DRY_RUN:
    ALUNOS_PATH.write_text(
        json.dumps(filtrados, ensure_ascii=False, indent=2), encoding="utf-8"
    )

# 2. Limpar portal/provas/ (contaminados)
DST.mkdir(parents=True, exist_ok=True)
removidos_pdfs = list(DST.glob("*.pdf"))
for f in removidos_pdfs:
    if not DRY_RUN:
        f.unlink()
print(f"PDFs antigos removidos: {len(removidos_pdfs)}")

# 3. Copiar via mapeamento
mapa = json.load(open(MAP_PATH, encoding="utf-8"))
copiados = 0
erros = []
for entry in mapa["mapeamento"]:
    src = SRC / entry["fonte"]
    dst = DST / entry["arquivo_destino"]
    if not src.exists():
        erros.append(f"FONTE NAO EXISTE: {entry['fonte']}")
        continue
    # Verifica se o aluno (por matrícula) está nos filtrados
    mat = entry["matricula"]
    if not any(a["matricula"] == mat for a in filtrados):
        continue  # Aluno removido (Luiza, etc)
    if not DRY_RUN:
        shutil.copy2(src, dst)
    copiados += 1
    print(
        f"  {'[DRY]' if DRY_RUN else '[OK]'} {entry['fonte']} -> {entry['arquivo_destino']} ({entry['tamanho_fonte_bytes'] // 1024} KB)"
    )

print(f"\nCopiados: {copiados}, Erros: {len(erros)}")
for e in erros:
    print(f"  ERRO: {e}")
