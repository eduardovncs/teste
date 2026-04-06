"""
MCP Databricks SQL.

Ferramentas para executar SQL e obter metadados de tabelas no Databricks.
"""
import os
import time
from typing import Any

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
from fastmcp import FastMCP

# ============================================================
# CONFIGURAÇÃO
# ============================================================

POLL_INTERVAL = 1

# ============================================================
# CLIENTE DATABRICKS
# ============================================================


class DatabricksClient:
    """Cliente para interagir com Databricks (metadados e queries SQL)."""

    def __init__(self):
        self.client = WorkspaceClient()
        self.warehouse_id = self._get_warehouse_id()

    def _get_warehouse_id(self) -> str:
        warehouse_id = os.environ.get("DATABRICKS_WAREHOUSE_ID")
        if warehouse_id:
            return warehouse_id
        warehouses = list(self.client.warehouses.list())
        if not warehouses:
            raise RuntimeError(
                "Nenhum SQL Warehouse encontrado. "
                "Configure DATABRICKS_WAREHOUSE_ID no ambiente."
            )
        return warehouses[0].id

    def execute_sql(self, statement: str) -> tuple[list[str], list[list[Any]]]:
        """
        Executa SQL com polling e retorna (colunas, linhas).
        Levanta RuntimeError se a query falhar.
        """
        response = self.client.statement_execution.execute_statement(
            warehouse_id=self.warehouse_id,
            statement=statement,
        )

        statement_id = response.statement_id
        while True:
            response = self.client.statement_execution.get_statement(statement_id)
            state = response.status.state
            if state in (StatementState.SUCCEEDED, StatementState.FAILED, StatementState.CANCELED):
                break
            time.sleep(POLL_INTERVAL)

        if state != StatementState.SUCCEEDED:
            raise RuntimeError(f"Query falhou: {response.status.error}")

        columns = []
        if response.manifest and response.manifest.schema and response.manifest.schema.columns:
            columns = [col.name for col in response.manifest.schema.columns]

        rows = response.result.data_array or []
        return columns, rows

    def get_table_info(self, table_full_name: str):
        """Obtém metadados da tabela via Unity Catalog."""
        return self.client.tables.get(table_full_name)


# ============================================================
# MCP
# ============================================================

mcp = FastMCP("databricks-sql")
db = DatabricksClient()


@mcp.tool()
def executar_sql(sql: str) -> dict:
    """
    Executa um comando SQL no Databricks e retorna o resultado.

    Use para qualquer SQL: SELECT, DROP, CREATE, INSERT, queries complexas, etc.
    O resultado vem como lista de dicionários — cada item é uma linha.

    Args:
        sql: Comando SQL a executar.
             Ex: "SELECT COUNT(*) FROM catalogo.schema.tabela"
             Ex: "DROP TABLE IF EXISTS catalogo.schema.tabela"

    Returns:
        {
            "status": "ok" | "erro",
            "linhas": int,           # Quantidade de linhas retornadas
            "resultado": [           # Lista de linhas como dicionários
                {"coluna": "valor"}
            ],
            "mensagem": str          # Presente em caso de erro ou sem retorno
        }
    """
    try:
        columns, rows = db.execute_sql(sql)

        if not rows:
            return {"status": "ok", "mensagem": "Comando executado com sucesso.", "linhas": 0}

        resultado = [dict(zip(columns, row)) for row in rows]
        return {"status": "ok", "linhas": len(resultado), "resultado": resultado}

    except Exception as e:
        return {"status": "erro", "tipo": type(e).__name__, "mensagem": str(e)}


@mcp.tool()
def obter_metadados(tabela: str) -> dict:
    """
    Retorna metadados completos de uma tabela via Unity Catalog.

    Inclui colunas, tipos, comentários, formato, localização e owner.
    Use antes de escrever qualquer transformação para entender o schema real.

    Args:
        tabela: Nome completo no formato catalogo.schema.tabela.
                Ex: "meu_catalogo.vendas.fato_contratos"

    Returns:
        {
            "status": "ok" | "erro",
            "tabela": str,
            "descricao": str,
            "tipo": str,          # MANAGED, EXTERNAL, VIEW, etc.
            "formato": str,       # DELTA, PARQUET, etc.
            "localizacao": str,
            "owner": str,
            "colunas": [
                {
                    "coluna": str,
                    "tipo": str,
                    "comentario": str,
                    "nullable": bool
                }
            ]
        }
    """
    try:
        info = db.get_table_info(tabela)

        colunas = [
            {
                "coluna": col.name,
                "tipo": col.type_text or str(col.type_name),
                "comentario": col.comment or "",
                "nullable": col.nullable,
            }
            for col in (info.columns or [])
        ]

        return {
            "status": "ok",
            "tabela": tabela,
            "descricao": info.comment or "",
            "tipo": info.table_type.value if info.table_type else None,
            "formato": info.data_source_format.value if info.data_source_format else None,
            "localizacao": info.storage_location,
            "owner": info.owner,
            "colunas": colunas,
        }

    except Exception as e:
        return {"status": "erro", "tipo": type(e).__name__, "mensagem": str(e)}


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    mcp.run(transport="stdio")