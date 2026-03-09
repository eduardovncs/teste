"""Gerenciador ChromaDB.

Classe de gerenciamento do ChromaDB para busca e validacao de mnemonicos.
Encapsula conexao, embeddings e operacoes de consulta.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import chromadb
from chromadb.utils.embedding_functions import (
    SentenceTransformerEmbeddingFunction,
)

if TYPE_CHECKING:
    from pathlib import Path


class GerenciadorChromaDB:
    """Gerencia a conexao e operacoes de busca no ChromaDB de mnemonicos."""

    def __init__(
        self,
        caminho_db: str | Path,
        modelo_embedding: str,
        nome_colecao: str = "mnemonicos",
        limiar_similaridade: float = 0.90,
    ) -> None:
        """Inicializa o gerenciador com conexao ao ChromaDB."""
        self._caminho_db = str(caminho_db)
        self._modelo_embedding = modelo_embedding
        self._nome_colecao = nome_colecao
        self._limiar = limiar_similaridade

        self._funcao_embedding = SentenceTransformerEmbeddingFunction(
            model_name=self._modelo_embedding,
        )
        self._cliente = chromadb.PersistentClient(path=self._caminho_db)
        self._colecao = self._cliente.get_collection(
            self._nome_colecao,
            embedding_function=self._funcao_embedding,
        )

    # -- Consultas -----------------------------------------------------------

    def buscar_mnemonico(self, token: str, n_resultados: int = 3) -> dict:
        """Busca semantica de um token, retornando candidatos ordenados por score."""
        resultado = self._colecao.query(query_texts=[token], n_results=n_resultados)
        candidatos = [
            {
                "nome": meta["nome"],
                "codigo": meta["codigo"],
                "score": round(1 - dist, 4),
            }
            for meta, dist in zip(
                resultado["metadatas"][0],
                resultado["distances"][0],
                strict=True,
            )
        ]
        candidatos.sort(key=lambda x: x["score"], reverse=True)

        # Match exato: promove para score 1.0
        token_lower = token.strip().lower()
        for c in candidatos:
            if c["codigo"].lower() == token_lower or c["nome"].lower() == token_lower:
                c["score"] = 1.0
                c["exact_match"] = True

        candidatos.sort(key=lambda x: x["score"], reverse=True)

        acima = [c for c in candidatos if c["score"] >= self._limiar]
        abaixo = [c for c in candidatos if c["score"] < self._limiar]

        return {
            "token": token,
            "threshold": self._limiar,
            "above_threshold": acima,
            "below_threshold": abaixo,
            "recommendation": acima[0] if acima else None,
        }

    def obter_codigos_validos(self) -> set[str]:
        """Retorna o conjunto de todos os codigos de mnemonicos cadastrados."""
        todos = self._colecao.get()
        return {m["codigo"] for m in todos["metadatas"]}

    def validar_mnemonicos(self, codigos: list[str]) -> list[str]:
        """Retorna lista de codigos que NAO existem no dicionario."""
        validos = self.obter_codigos_validos()
        return [c for c in codigos if c not in validos]
