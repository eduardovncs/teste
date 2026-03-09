"""MCP Server para padronizacao de nomes de colunas.

Naturezas sao carregadas do CSV em memoria (max 20 registros).
Mnemonicos sao indexados no ChromaDB (escala para milhares).

Uso:
    uv run server.py
"""

import csv
import json
import logging
from pathlib import Path

from fastmcp import FastMCP
from gerenciador_chromadb import GerenciadorChromaDB

log = logging.getLogger(__name__)

# -- Configuracoes -----------------------------------------------------------

MODELO_EMBEDDING     = "intfloat/multilingual-e5-small"
DIR_BASE             = Path(__file__).parent
CAMINHO_CHROMA       = DIR_BASE / "chroma_db"
NATUREZAS_CSV        = DIR_BASE / "arquivos" / "naturezas.csv"
LIMIAR_SIMILARIDADE  = 0.90

# -- Inicializacao global ----------------------------------------------------

# Naturezas — carregadas do CSV em memoria (lista pequena, busca direta)
log.info("Carregando naturezas do CSV...")
with NATUREZAS_CSV.open(encoding="utf-8") as f:
    _naturezas = sorted(
        [
            {
                "nome": row["nome"].strip(),
                "codigo": row["codigo"].strip(),
            }
            for row in csv.DictReader(f)
        ],
        key=lambda x: x["nome"],
    )
log.info("%d naturezas carregadas.", len(_naturezas))

# Mnemonicos — ChromaDB (escala para milhares)
log.info("Inicializando gerenciador ChromaDB...")
gerenciador = GerenciadorChromaDB(
    caminho_db=CAMINHO_CHROMA,
    modelo_embedding=MODELO_EMBEDDING,
    limiar_similaridade=LIMIAR_SIMILARIDADE,
)
log.info("Pronto.")

mcp = FastMCP("column_standardizer_mcp")

# -- Tools -------------------------------------------------------------------

@mcp.tool()
async def list_naturezas() -> str:
    """Retorna todas as naturezas disponiveis carregadas do CSV.

    Use no inicio do processamento de cada coluna para decidir qual natureza
    melhor representa o tipo semantico da coluna (valor, data, codigo, etc).
    Como sao no maximo 20 registros, analise a lista completa e decida pelo
    contexto e descricao da coluna — sem necessidade de busca vetorial.

    Returns:
        JSON com total e lista de naturezas com nome e codigo.
    """
    return json.dumps(
        {"total": len(_naturezas), "naturezas": _naturezas},
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
async def search_mnemonico(tokens: list[str], n_results: int = 3) -> str:
    """Busca mnemônicos no ChromaDB para uma lista de tokens simultaneamente.

    Sempre envie uma lista — mesmo para um único token: ["empenho"].
    Para sinônimos, envie todos juntos: ["sigla", "abreviatura", "acronimo", "acrograma"].
    Retorna o melhor candidato geral entre todos os tokens fornecidos.

    Args:
        tokens: Lista de tokens a buscar, ex: ["sigla", "abreviatura", "acronimo"]
        n_results: Numero de candidatos por token (default: 3, max: 10)

    Returns:
        JSON com resultados por token e o melhor candidato geral.
    """
    todos_resultados = {}
    melhor_geral = None

    for token in tokens:
        resultado = gerenciador.buscar_mnemonico(
            token, n_resultados=n_results,
        )
        todos_resultados[token] = resultado
        rec = resultado["recommendation"]
        if rec and (
            melhor_geral is None
            or rec["score"] > melhor_geral["score"]
        ):
            melhor_geral = {
                **rec, "matched_token": token,
            }

    return json.dumps(
        {
            "tokens":       tokens,
            "results":      todos_resultados,
            "best_overall": melhor_geral,
        },
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
async def validate_column_name(
    column_name: str,
    natureza_codigo: str,
    mnemonicos_codigos: list[str],
) -> str:
    """Valida nome de coluna e codigos no dicionario.

    Formato esperado: {natureza}{mnemonico1}_{mnemonico2}...
    Natureza gruda no primeiro mnemonico, demais separados por _.
    Exemplos validos: 'vcanc_emp', 'nctrl_org', 'dtliq', 'pctexec_ctr'

    Args:
        column_name: Nome gerado a validar, ex: 'vcanc_emp'
        natureza_codigo: Codigo da natureza usada, ex: 'v'
        mnemonicos_codigos: Codigos dos mnemonicos usados, ex: ['canc', 'emp']

    Returns:
        JSON com resultado da validacao, erros encontrados e nome esperado.
    """
    nat   = natureza_codigo.strip()
    mnems = [m.strip() for m in mnemonicos_codigos]
    errors = []

    # -- Valida natureza contra o dicionario em memoria ----------------------
    natureza_valida = any(n["codigo"] == nat for n in _naturezas)
    if not natureza_valida:
        codigos = [n["codigo"] for n in _naturezas]
        errors.append(
            f"Natureza '{nat}' nao existe no dicionario."
            f" Codigos validos: {codigos}",
        )

    # -- Valida mnemonicos contra o ChromaDB ---------------------------------
    mnemonicos_invalidos = gerenciador.validar_mnemonicos(mnems)
    if mnemonicos_invalidos:
        errors.append(
            "Mnemonicos nao encontrados no dicionario:"
            f" {mnemonicos_invalidos}",
        )

    # -- Valida formato ------------------------------------------------------
    if natureza_valida and not mnemonicos_invalidos:
        expected = nat + mnems[0] + ("_" + "_".join(mnems[1:]) if len(mnems) > 1 else "")
        if not column_name.startswith(nat):
            errors.append(f"'{column_name}' nao comeca com a natureza '{nat}'.")
        if column_name != expected:
            errors.append(f"Nome esperado: '{expected}', recebido: '{column_name}'.")
    else:
        expected = None

    return json.dumps(
        {
            "valid":         len(errors) == 0,
            "column_name":   column_name,
            "expected_name": expected,
            "errors":        errors,
        },
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
async def validate_object_name(
    object_name: str,
    tipo: str,
    mnemonicos_codigos: list[str],
) -> str:
    """Valida nome de tabela ou view e codigos no dicionario.

    Formato esperado:
      Tabela: t{mnemonico1}_{mnemonico2}...
      View:   v{mnemonico1}_{mnemonico2}...

    Args:
        object_name: Nome gerado a validar, ex: 'texec_orc'
        tipo: 'tabela' ou 'view'
        mnemonicos_codigos: Codigos dos mnemonicos usados, ex: ['exec', 'orc']

    Returns:
        JSON com resultado da validacao, erros encontrados e nome esperado.
    """
    tipo  = tipo.strip().lower()
    mnems = [m.strip() for m in mnemonicos_codigos]
    errors = []

    # -- Valida tipo ---------------------------------------------------------
    prefixos = {"tabela": "t", "view": "v"}
    if tipo not in prefixos:
        msg = f"Tipo '{tipo}' invalido. Use 'tabela' ou 'view'."
        errors.append(msg)
        return json.dumps(
            {
                "valid": False,
                "object_name": object_name,
                "expected_name": None,
                "errors": errors,
            },
            ensure_ascii=False,
            indent=2,
        )

    prefixo = prefixos[tipo]

    # -- Valida mnemonicos contra o ChromaDB ---------------------------------
    invalidos = gerenciador.validar_mnemonicos(mnems)
    if invalidos:
        errors.append(
            "Mnemonicos nao encontrados no dicionario:"
            f" {invalidos}",
        )

    # -- Valida formato ------------------------------------------------------
    expected = prefixo + mnems[0] + ("_" + "_".join(mnems[1:]) if len(mnems) > 1 else "")
    if not object_name.startswith(prefixo):
        errors.append(
            f"'{object_name}' nao comeca com o"
            f" prefixo '{prefixo}' para {tipo}.",
        )
    if object_name != expected:
        errors.append(f"Nome esperado: '{expected}', recebido: '{object_name}'.")

    return json.dumps(
        {
            "valid":         len(errors) == 0,
            "object_name":   object_name,
            "expected_name": expected if not invalidos else None,
            "errors":        errors,
        },
        ensure_ascii=False,
        indent=2,
    )


# -- Entry point -------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
