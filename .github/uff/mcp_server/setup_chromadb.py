"""
setup_chromadb.py

Lê os CSVs de naturezas e mnemônicos e indexa no ChromaDB
usando embeddings multilíngues (suporte a português).

Uso:
    uv run setup_chromadb.py
    uv run setup_chromadb.py --naturezas outro_caminho.csv --mnemonicos outro_caminho.csv
"""

import argparse
from pathlib import Path
import pandas as pd
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

# ── Configurações ────────────────────────────────────────────────────────────

# Modelo multilíngue leve — bom para português
EMBEDDING_MODEL = "intfloat/multilingual-e5-small"

# Onde o ChromaDB vai persistir os dados (pasta local)
_SCRIPT_DIR = Path(__file__).parent
CHROMA_PATH = str(_SCRIPT_DIR / "chroma_db")

# Caminhos padrão dos CSVs
DEFAULT_NATUREZAS  = str(_SCRIPT_DIR / "arquivos" / "naturezas.csv")
DEFAULT_MNEMONICOS = str(_SCRIPT_DIR / "arquivos" / "mnemonicos.csv")

# Nomes das collections
COLLECTION_NATUREZAS  = "naturezas"
COLLECTION_MNEMONICOS = "mnemonicos"

# ── Setup ────────────────────────────────────────────────────────────────────

def build_embedding_fn():
    print(f"[setup] Carregando modelo de embeddings: {EMBEDDING_MODEL}")
    return SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)


def get_client():
    return chromadb.PersistentClient(path=CHROMA_PATH)


# ── Indexação ────────────────────────────────────────────────────────────────

def index_csv(
    client: chromadb.ClientAPI,
    embedding_fn,
    csv_path: str,
    collection_name: str,
    tipo: str,  # "natureza" | "mnemonico"
):
    print(f"\n[index] Processando '{csv_path}' → collection '{collection_name}'")

    df = pd.read_csv(csv_path)

    # Valida colunas esperadas
    assert "nome" in df.columns and "codigo" in df.columns, (
        f"CSV '{csv_path}' deve ter colunas 'nome' e 'codigo'"
    )

    # Recria a collection do zero (idempotente)
    try:
        client.delete_collection(collection_name)
        print(f"[index] Collection '{collection_name}' antiga removida.")
    except Exception:
        pass

    collection = client.create_collection(
        name=collection_name,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},  # similaridade por cosseno
    )

    # Monta os documentos
    # Indexa "nome codigo sinonimos" para enriquecer o espaço semântico
    # Ex: "vencimento prazo data limite data final expiracao validade"
    # Isso permite que buscas por sinônimos retornem score alto sem depender do agente
    if "sinonimos" in df.columns:
        documents = (
            df["nome"].str.lower().str.strip() + " " +
            df["codigo"].str.lower().str.strip() + " " +
            df["sinonimos"].fillna("").str.lower().str.strip()
        ).tolist()
    else:
        documents = (
            df["nome"].str.lower().str.strip() + " " +
            df["codigo"].str.lower().str.strip()
        ).tolist()
    ids       = [f"{tipo}_{i}" for i in range(len(df))]
    metadatas = [
        {
            "nome":   row["nome"].strip(),
            "codigo": row["codigo"].strip(),
            "tipo":   tipo,
        }
        for _, row in df.iterrows()
    ]

    collection.add(
        documents=documents,
        ids=ids,
        metadatas=metadatas,
    )

    print(f"[index] {len(documents)} registros indexados:")
    for doc, meta in zip(documents, metadatas):
        print(f"         '{doc}' → código: '{meta['codigo']}'")


# ── Smoke test ───────────────────────────────────────────────────────────────

def smoke_test(client: chromadb.ClientAPI, embedding_fn):
    """Testa algumas buscas para validar que a indexação funcionou."""
    print("\n[test] ── Smoke test ──────────────────────────────────────────")

    casos = [
        ("mnemonicos", "cancelamento"),   # match exato
        ("mnemonicos", "cancelar"),       # variação do verbo
        ("mnemonicos", "num_controle"),   # token composto
        ("mnemonicos", "liquidar"),       # variação
        ("naturezas",  "numero"),         # match exato
        ("naturezas",  "num"),            # abreviação
        ("naturezas",  "valor"),          # match exato
    ]

    for collection_name, query in casos:
        col = client.get_collection(
            name=collection_name,
            embedding_function=embedding_fn,
        )
        results = col.query(query_texts=[query], n_results=3)

        print(f"\n  query='{query}' em '{collection_name}':")
        for meta, dist in zip(
            results["metadatas"][0],
            results["distances"][0],
        ):
            score = 1 - dist  # cosine distance → similarity
            print(f"    → '{meta['nome']}' (codigo={meta['codigo']}) | score={score:.3f}")

    print("\n[test] ── Fim ─────────────────────────────────────────────────\n")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Indexa CSVs no ChromaDB")
    parser.add_argument("--naturezas",  default=DEFAULT_NATUREZAS)
    parser.add_argument("--mnemonicos", default=DEFAULT_MNEMONICOS)
    args = parser.parse_args()

    embedding_fn = build_embedding_fn()
    client       = get_client()

    index_csv(client, embedding_fn, args.naturezas,  COLLECTION_NATUREZAS,  "natureza")
    index_csv(client, embedding_fn, args.mnemonicos, COLLECTION_MNEMONICOS, "mnemonico")

    smoke_test(client, embedding_fn)

    print(f"[setup] ✅ ChromaDB pronto em '{CHROMA_PATH}'")
    print(f"[setup]    Collections: '{COLLECTION_NATUREZAS}', '{COLLECTION_MNEMONICOS}'")


if __name__ == "__main__":
    main()