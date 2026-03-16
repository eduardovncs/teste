# Architecture Document
**Async Batch Processing Pipeline — Databricks**
Versão 1.0 · C4 Model

---

## C1 — Context

Visão de mais alto nível do sistema. Mostra o pipeline como uma unidade, os atores externos que interagem com ele e os sistemas de terceiros envolvidos.

```mermaid
C4Context
  title C1 — Context: Async Batch Processing Pipeline

  Person(fonte, "Fonte de dados", "Origem dos registros a serem processados")

  System(pipeline, "Processing Pipeline", "Sistema principal rodando no Databricks. Prepara, envia, monitora e coleta resultados via API externa.")

  System_Ext(azure_storage, "Azure Storage", "Armazenamento temporário dos arquivos .xz")
  System_Ext(api, "Azure/GCP API", "Executa processamento assíncrono e retorna resultados")
  System_Ext(mlflow, "MLflow", "Tracking de métricas por batch")

  Rel(fonte, pipeline, "Entrega registros", "Delta Table")
  Rel(pipeline, azure_storage, "Upload do .xz")
  Rel(pipeline, api, "Envia · processa · coleta")
  Rel(pipeline, mlflow, "Registra métricas")
```

---

## C2 — Container

Decompõe o sistema principal em containers — os processos e estruturas de dados que o compõem.

```mermaid
C4Container
  title C2 — Container: Processing Pipeline

  Person(fonte, "Fonte de dados", "Origem dos registros")

  System_Boundary(pipeline, "Processing Pipeline — Databricks") {
    Container(ingestion, "Ingestion Module", "Python / PySpark", "Recebe dados e identifica registros novos")
    ContainerDb(control, "Control Table", "Delta Lake", "Centraliza o estado de cada registro. Genérica — campos de negócio definidos por quem usa o módulo")
    Container(processing, "Processing Module", "Python / PySpark", "Orquestra preparação, compressão, upload, polling e coleta de resultados")
  }

  System_Ext(azure_storage, "Azure Storage", "Armazena .xz")
  System_Ext(api, "Azure/GCP API", "Processa · retorna resultados")
  System_Ext(mlflow, "MLflow", "Tracking")

  Rel(fonte, ingestion, "Entrega registros", "Delta Table")
  Rel(ingestion, control, "Insere com status PENDING")
  Rel(processing, control, "Lê e atualiza por batch_id")
  Rel(processing, azure_storage, "Upload do .xz")
  Rel(processing, api, "Envia · processa · coleta")
  Rel(processing, mlflow, "Métricas por batch")
```
