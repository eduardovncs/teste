# =============================================================
# EXEMPLO DE USO — AITrackingService
# Copie este notebook para o Databricks e rode célula a célula
# =============================================================

# =============================================================
# CELL 1 — Importa o módulo do Volume
# %run /Volumes/workspace/default/audios/modules/ai_tracking/__init__
# =============================================================

# Ou instala localmente para testes:
import sys
sys.path.insert(0, "/Volumes/workspace/default/audios/modules")

from ai_tracking import (
    AITrackingService,
    BatchData,
    RegistroData,
    StatusBatch,
    StatusRegistro,
)

# =============================================================
# CELL 2 — Inicializa o serviço
# =============================================================

service = AITrackingService(
    experiment_name = "/Users/eduardosch26@gmail.com/teste_batch_llm",
    volume_path     = "/Volumes/workspace/default/audios"
)

# =============================================================
# CELL 3 — Registra prompts (só quando houver nova versão)
# =============================================================

service.registrar_prompt(
    nome      = "classificacao_pf",
    template  = "Classifique o contrato do cliente PF como inadimplente, em_dia ou encerrado.\nContrato: {{input}}",
    changelog = "versão inicial"
)

service.registrar_prompt(
    nome      = "classificacao_pj",
    template  = "Classifique o contrato da empresa PJ como inadimplente, em_dia ou encerrado.\nContrato: {{input}}",
    changelog = "versão inicial"
)

service.listar_versoes("classificacao_pf")
service.listar_versoes("classificacao_pj")

# =============================================================
# CELL 4 — Lê registros da Delta e prepara o batch
# =============================================================

# Simula leitura da Delta
# Na prática seria:
# df = spark.read.table("contratos").filter("status_ia IS NULL AND ativo = true")
# registros_delta = df.collect()

registros_delta = [
    {"id": "CTR_001", "texto": "Cliente João Silva, 3 parcelas em atraso.",     "tipo": "PF"},
    {"id": "CTR_002", "texto": "Empresa XYZ Ltda, pagamentos em dia.",          "tipo": "PJ"},
    {"id": "CTR_003", "texto": "Cliente Ana Costa, contrato encerrado jan/26.", "tipo": "PF"},
    {"id": "CTR_004", "texto": "Empresa ABC S.A., 2 parcelas em atraso.",       "tipo": "PJ"},
    {"id": "CTR_005", "texto": "Cliente Pedro Lima, " + "x" * 5000,            "tipo": "PF"},  # texto longo → vai gerar erro
]

# Carrega prompts ativos
prompt_pf = service.carregar_prompt("classificacao_pf")
prompt_pj = service.carregar_prompt("classificacao_pj")

# Monta lista de RegistroData com prompt correto por tipo
registros = [
    RegistroData(
        id     = r["id"],
        input  = r["texto"],
        prompt = prompt_pf if r["tipo"] == "PF" else prompt_pj,
    )
    for r in registros_delta
]

print(f"\n✅ {len(registros)} registros preparados")

# =============================================================
# CELL 5 — Submete o batch
# =============================================================

import uuid

batch_data = BatchData(
    batch_id        = f"batch_{uuid.uuid4().hex[:8]}",
    modelo          = "gpt-4o",
    temperatura     = 0.2,
    max_tokens      = 500,
    total_registros = len(registros),
)

run_id = service.submeter_batch(batch_data, registros)

# Salva batch_id para as próximas células
BATCH_ID = batch_data.batch_id
print(f"\nBATCH_ID = {BATCH_ID}")

# =============================================================
# CELL 6 — Simula polling (Job agendado na prática)
# =============================================================

# Na prática seria:
# status_api = api_client.get_status(BATCH_ID)

service.atualizar_status(BATCH_ID, StatusBatch.PROCESSING)

# =============================================================
# CELL 7 — Simula retorno da API com resultado parcial
# =============================================================

# Na prática o output viria da API:
# output_path = api_client.download_resultado(BATCH_ID)
# resultados  = service._batch_ctrl.carregar_output_jsonl(BATCH_ID)

resultados = [
    RegistroData(
        id                 = "CTR_001",
        input              = registros_delta[0]["texto"],
        prompt             = prompt_pf,
        output             = {"classificacao": "inadimplente", "confianca": 0.97},
        status             = StatusRegistro.SUCCESS,
        tokens_input       = 89,
        tokens_output      = 15,
        judge_relevance    = 0.95,
        judge_faithfulness = 0.92,
    ),
    RegistroData(
        id                 = "CTR_002",
        input              = registros_delta[1]["texto"],
        prompt             = prompt_pj,
        output             = {"classificacao": "em_dia", "confianca": 0.99},
        status             = StatusRegistro.SUCCESS,
        tokens_input       = 91,
        tokens_output      = 14,
        judge_relevance    = 0.98,
        judge_faithfulness = 0.97,
    ),
    RegistroData(
        id                 = "CTR_003",
        input              = registros_delta[2]["texto"],
        prompt             = prompt_pf,
        output             = {"classificacao": "encerrado", "confianca": 0.98},
        status             = StatusRegistro.SUCCESS,
        tokens_input       = 87,
        tokens_output      = 16,
        judge_relevance    = 0.96,
        judge_faithfulness = 0.94,
    ),
    RegistroData(
        id     = "CTR_004",
        input  = registros_delta[3]["texto"],
        prompt = prompt_pj,
        output = None,
        status = StatusRegistro.ERROR,  # ← erro parcial
        erro   = "context_length_exceeded",
        tokens_input  = 0,
        tokens_output = 0,
    ),
    RegistroData(
        id     = "CTR_005",
        input  = registros_delta[4]["texto"],
        prompt = prompt_pf,
        output = None,
        status = StatusRegistro.ERROR,  # ← erro parcial
        erro   = "rate_limit_exceeded",
        tokens_input  = 0,
        tokens_output = 0,
    ),
]

# =============================================================
# CELL 8 — Finaliza o batch
# =============================================================

metricas = service.finalizar_batch(BATCH_ID, resultados)

# =============================================================
# CELL 9 — Persiste na Delta (sucesso e erro separados)
# =============================================================

sucesso = [r for r in resultados if r.sucesso]
erro    = [r for r in resultados if not r.sucesso]

print(f"\n💾 Persistindo na Delta:")
print(f"   {len(sucesso)} registros → upsert com resultado")
print(f"   {len(erro)}    registros → marcados para reprocessamento")

# Na prática seria:
# df_sucesso = spark.createDataFrame([{
#     "id_contrato":    r.id,
#     "classificacao":  r.output["classificacao"],
#     "confianca":      r.output["confianca"],
#     "run_id":         run_id,
#     "prompt_versao":  r.prompt.versao,
#     "status_ia":      "processado"
# } for r in sucesso])
# delta_table.merge(...).whenMatchedUpdate(...).execute()
#
# df_erro = spark.createDataFrame([{
#     "id_contrato": r.id,
#     "status_ia":   "erro",
#     "motivo_erro": r.erro,
# } for r in erro])
# delta_table.merge(...).whenMatchedUpdate(...).execute()

# =============================================================
# CELL 10 — Resumo do dia
# =============================================================

service.resumo()
