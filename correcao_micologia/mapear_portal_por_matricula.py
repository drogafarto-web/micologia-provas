"""Gera mapeamento_portal_correto.json cruzando alunos.json com provas_corrigidas/ por matrícula."""
import json, re
from pathlib import Path
from unicodedata import normalize

BASE = Path(r"C:\Users\labcl\Desktop\04_Provas")
SRC = BASE / "correcao_micologia" / "provas_corrigidas"
ALUNOS_JSON = BASE / "portal" / "alunos.json"
OUT = BASE / "portal" / "mapeamento_portal_correto.json"

# Correções manuais: matricula real no alunos.json -> matricula presente no filename PDF
CORRECOES_MATRICULA = {
    "221-001045": "231-001045",   # PETERSON — PDF tem matrícula errada
    "232-001212": "232-002121",   # MARIA EDUARDA LACERDA — PDF tem matrícula errada
}

alunos = json.load(open(ALUNOS_JSON, encoding="utf-8"))
alunos_por_mat = {a["matricula"]: a for a in alunos if a.get("matricula")}

corrigidos_por_mat = {}
nao_identificados_por_filename = []

for f in SRC.glob("prova_*_corrigida.pdf"):
    m = re.match(r"prova_\d+_(\d{3}-\d{6})_", f.name)
    if m:
        corrigidos_por_mat[m.group(1)] = f
    else:
        nao_identificados_por_filename.append(f)

# Fallback por nome normalizado — constrói índice
nome_para_mat = {}
for a in alunos_por_mat.values():
    nome_norm = normalize('NFKD', a["nome"]).encode('ascii', 'ignore').decode().upper()
    nome_norm = re.sub(r'[^A-Z0-9 ]', '', nome_norm)
    nome_para_mat[nome_norm] = a["matricula"]
    partes = nome_norm.split()
    if len(partes) > 1:
        nome_curto = " ".join(partes[:2])
        if nome_curto not in nome_para_mat:
            nome_para_mat[nome_curto] = a["matricula"]

# Função: extrair nome do PDF normalizado
def nome_do_pdf(f):
    m = re.match(r"^prova_\d+_(.+)_corrigida$", f.stem)
    if m:
        return re.sub(r'[^A-Z0-9 ]', '', m.group(1).replace("_", " ").upper())
    return ""

# Fallback 1: PDFs sem matrícula no nome
for f in nao_identificados_por_filename:
    nome_norm = nome_do_pdf(f)
    if nome_norm in nome_para_mat:
        corrigidos_por_mat[nome_para_mat[nome_norm]] = f
    else:
        print(f"WARNING: não mapeado por nome: {f.name}")

# Fallback 2: alunos ainda não mapeados — buscar por nome em TODOS os PDFs
ja_mapeados = set(corrigidos_por_mat.keys())
for mat, aluno in alunos_por_mat.items():
    if mat in ja_mapeados:
        continue
    nome_aluno = normalize('NFKD', aluno["nome"]).encode('ascii', 'ignore').decode().upper()
    nome_aluno = re.sub(r'[^A-Z0-9 ]', '', nome_aluno)
    for f in SRC.glob("prova_*_corrigida.pdf"):
        nome_pdf = nome_do_pdf(f)
        if nome_pdf == nome_aluno:
            corrigidos_por_mat[mat] = f
            print(f"  [FALLBACK NOME] {mat} <- {f.name}")
            break

# Fallback 3: aplica correções de matrícula
for mat_real, mat_pdf in CORRECOES_MATRICULA.items():
    if mat_pdf in corrigidos_por_mat and mat_real not in corrigidos_por_mat:
        corrigidos_por_mat[mat_real] = corrigidos_por_mat[mat_pdf]
        print(f"  [CORRECAO] {mat_real} (PDF tinha {mat_pdf}) <- {corrigidos_por_mat[mat_pdf].name}")

mapeamento = []
nao_encontrados = []
for mat, aluno in alunos_por_mat.items():
    if mat in corrigidos_por_mat:
        src = corrigidos_por_mat[mat]
        mapeamento.append({
            "matricula": mat,
            "nome": aluno["nome"],
            "arquivo_destino": aluno["arquivo"],
            "fonte": src.name,
            "tamanho_fonte_bytes": src.stat().st_size
        })
    else:
        nao_encontrados.append({"matricula": mat, "nome": aluno["nome"]})

output = {
    "total_alunos_json": len(alunos_por_mat),
    "mapeados": len(mapeamento),
    "nao_encontrados": nao_encontrados,
    "mapeamento": mapeamento
}

OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Mapeados: {len(mapeamento)} / {len(alunos_por_mat)}")
print(f"Não encontrados: {len(nao_encontrados)}")
for ne in nao_encontrados:
    print(f"  - {ne['matricula']} {ne['nome']}")
