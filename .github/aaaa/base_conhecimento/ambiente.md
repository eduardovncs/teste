# Ambiente

> Configuração e caraterísticas do ambiente de execução

## Overview

O projeto utiliza **Databricks** como plataforma de dados e **Databricks Asset Bundles** (DAB) para gerenciar workflows, jobs e recursos.

---

## Ambiente Exploratório

| Configuração | Valor |
|--------------|-------|
| **Plataforma** | Databricks |
| **Schema** | `workspace` |
| **Database** | `default` |
| **Volume de Dados** | `/Volumes/workspace/default/audios` |

---

## Armazenamento

### Banco de Dados

```
workspace.default
```

- Schema padrão para tabelas e dados do projeto
- Todas as tabelas devem ser salvas nesse database

### Volume de Dados

```
/Volumes/workspace/default/audios
```

- Pasta central para armazenar arquivos
- Montagem no DBFS (Databricks File System)
- Utilizar para entrada/saída de pipelines

---

## Estrutura do Projeto

```
pga/
├── jobs/                # Entrypoints de todos os jobs
├── src/
│   └── core/           # Lógica dos módulos utilizados pelos jobs
├── resources/          # Arquivos .yml com as definições dos pipelines
├── docs/               # Páginas do MkDocs
├── dist/               # Arquivos .whl dos builds do projeto
├── databricks.yml      # Configurações do Asset Bundle
├── pyproject.toml      # Regras de lint, typing, docstring do projeto
└── mkdocs.yml          # Configuração do MkDocs
```

### Descrição das Pastas

| Pasta/Arquivo | Descrição |
|---------------|-----------|
| `jobs/` | Contém os entrypoints (pontos de entrada) de todos os jobs do Databricks |
| `src/core/` | Lógica central e módulos reutilizáveis utilizados pelos jobs |
| `resources/` | Arquivos YAML com definições de pipelines e workflows do Databricks |
| `docs/` | Documentação do projeto em formato Markdown para o MkDocs |
| `dist/` | Arquivos wheel (.whl) gerados durante o build do projeto |
| `databricks.yml` | Configuração do Databricks Asset Bundle (DAB) |
| `pyproject.toml` | Configurações de linting (Ruff), type checking (Pyright), docstring (Pydoclint) |
| `mkdocs.yml` | Configuração do site de documentação MkDocs |

---

## Databricks Asset Bundles (DAB)

O projeto usa **DAB** para:
- Definir workflows e dashboards
- Gerenciar jobs e tasks
- Deploy automático de recursos

### Configuração do databricks.yml

```yaml
bundle:
  name: pga

workspace:
  host: https://<workspace-url>
  root_path: /Workspace/.bundle/${bundle.name}/${bundle.environment}


include:
  - resources/*.yml
  - resources/**/*.yml

sync:
  exclude:
    - .venv/**
    - .vscode/**
    - .git/**
    - __pycache__/**
    - .pytest_cache/**
    - .ruff_cache/**
    - site/**
    - docs/**

targets:
  dev:
    mode: development
    default: true
    workspace:
      host: https://<dev-workspace-url>
```

---

## Configurações do Projeto

### mkdocs.yml

Configuração atual do site de documentação:

```yaml
site_name: 'My Documentation'
docs_dir: docs
```

**Principais campos:**
- `site_name`: Nome do site de documentação
- `docs_dir`: Diretório onde ficam os arquivos Markdown

### pyproject.toml

Configurações de qualidade de código e build:

#### Tasks (Taskipy)

**Comandos disponíveis:**
- `uv run task lint` - Executa linting com Ruff
- `uv run task doclint` - Valida docstrings
- `uv run task typing` - Verifica tipos com Pyright
- `uv run task complexity` - Analisa complexidade de código
- `uv run task docs` - Inicia servidor local da documentação
- `uv run task check` - Executa todas as validações

---

## Restrições e Considerações

- **Ambiente Exploratório**: Não é para produção — use para desenvolvimento e testes
- **Volume de Audios**: Caminho específico para arquivos de áudio — não misturar com outros tipos de dados
- **DAB**: Usar para versionamento e deploy — evitar mudanças manuais fora do bundle

