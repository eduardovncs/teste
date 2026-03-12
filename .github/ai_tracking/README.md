# ai_tracking

Módulo para rastreamento de pipelines de IA no Databricks via MLflow.

## Estrutura

```
ai_tracking/
├── models/
│   ├── prompt_data.py       — dados de um prompt versionado
│   ├── registro_data.py     — dados de uma linha do batch (input/output/status)
│   ├── batch_data.py        — metadados do batch
│   └── metricas_lote.py     — métricas agregadas + definição de status
├── repository/
│   └── prompt_repository.py — versiona e carrega prompts no Volume
├── controller/
│   └── batch_controller.py  — gera/salva JSONL e controla run_id
├── tracker/
│   ├── mlflow_tracker.py    — toda comunicação com o MLflow
│   └── trace_logger.py      — loga traces por linha (sucesso e erro)
├── service/
│   └── ai_tracking_service.py — orquestrador principal
└── exemplo_uso.py           — notebook de exemplo completo
```

## Como usar no Databricks

### 1. Copie a pasta para o Volume
```
/Volumes/workspace/default/audios/modules/ai_tracking/
```

### 2. Importe no notebook ou Job
```python
import sys
sys.path.insert(0, "/Volumes/workspace/default/audios/modules")

from ai_tracking import AITrackingService, BatchData, RegistroData, StatusBatch, StatusRegistro
```

### 3. Inicializa o serviço
```python
service = AITrackingService(
    experiment_name = "/Users/usuario@email.com/meu_experimento",
    volume_path     = "/Volumes/workspace/default/audios"
)
```

### 4. Fluxo completo

```python
# Registra prompt (só quando houver nova versão)
service.registrar_prompt("classificacao_pf", template, "versão inicial")

# Carrega prompt ativo
prompt = service.carregar_prompt("classificacao_pf")

# Monta registros
registros = [
    RegistroData(id="CTR_001", input="texto...", prompt=prompt)
]

# Submete batch
import uuid
batch_data = BatchData(
    batch_id        = f"batch_{uuid.uuid4().hex[:8]}",
    modelo          = "gpt-4o",
    temperatura     = 0.2,
    max_tokens      = 500,
    total_registros = len(registros),
)
run_id = service.submeter_batch(batch_data, registros)

# Polling (Job agendado)
service.atualizar_status(batch_id, StatusBatch.PROCESSING)

# Finaliza quando API retornar
service.finalizar_batch(batch_id, resultados)

# Resumo do dia
service.resumo()
```

## Status possíveis

### StatusBatch
| Status     | Descrição                        |
|------------|----------------------------------|
| SUBMITTED  | batch enviado para a API         |
| PROCESSING | batch sendo processado           |
| COMPLETED  | todos os registros com sucesso   |
| PARTIAL    | alguns registros falharam        |
| FAILED     | todos os registros falharam      |

### StatusRegistro
| Status  | Descrição              |
|---------|------------------------|
| SUCCESS | registro processado    |
| ERROR   | registro com falha     |

## O que fica salvo e onde

```
Volume (persistente)
├── prompts/
│   ├── classificacao_pf_v1.json
│   └── classificacao_pj_v1.json
├── batches/
│   ├── input_{batch_id}.jsonl
│   └── output_{batch_id}.jsonl
└── control/
    └── {batch_id}.txt   ← run_id para retomada assíncrona

MLflow Experiment
└── Run: batch_{data}_{batch_id}
    ├── params:  modelo, temperatura, prompt_modo, batch_id
    ├── metrics: tokens (total/media/max/min), custo, taxa_sucesso, judge
    └── traces:  1 por linha — input, output, prompt_versao, tokens, judge
```
