# Databricks notebook source
# MAGIC %md
# MAGIC # Simulação de 5 Batches — AITrackingService
# MAGIC Simula o fluxo completo de 5 batches com 10 registros cada, sem chamadas reais à API.

# COMMAND ----------

import sys
sys.path.insert(0, "/Volumes/workspace/default/audios/modules")

from ai_tracking import (
    AITrackingService,
    BatchData,
    RegistroData,
    StatusBatch,
    StatusRegistro,
)

import uuid
import random
import json
import mlflow
from datetime import date

# COMMAND ----------
# MAGIC %md
# MAGIC ## Cell 2 — Inicializa o serviço

# COMMAND ----------

service = AITrackingService(
    experiment_name = "/Users/eduardosch26@gmail.com/teste_batch_llm",
    volume_path     = "/Volumes/workspace/default/audios"
)

# COMMAND ----------
# MAGIC %md
# MAGIC ## Cell 3 — Registra prompts

# COMMAND ----------

service.registrar_prompt(
    nome      = "classificacao_contrato",
    template  = "Classifique o contrato abaixo como inadimplente, em_dia ou encerrado.\nContrato: {{input}}",
    changelog = "versão inicial"
)

service.registrar_prompt(
    nome      = "classificacao_contrato",
    template  = """Você é especialista em análise de contratos financeiros.
Classifique o contrato abaixo em uma das categorias:
- inadimplente: possui parcelas em atraso
- em_dia: todas as parcelas pagas corretamente
- encerrado: contrato finalizado

Responda apenas com a categoria.
Contrato: {{input}}""",
    changelog = "adicionado contexto de especialista"
)

service.listar_versoes("classificacao_contrato")

# COMMAND ----------
# MAGIC %md
# MAGIC ## Cell 4 — Cria o DataFrame inicial (simula a tabela Delta)

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType

spark = SparkSession.builder.getOrCreate()

textos_contratos = [
    ("CTR_001", "Cliente João Silva, CPF 123.456.789-00, 3 parcelas em atraso desde março/2025.", "PF"),
    ("CTR_002", "Empresa XYZ Ltda, CNPJ 12.345.678/0001-99, todas as parcelas quitadas até dez/2025.", "PJ"),
    ("CTR_003", "Cliente Ana Costa, CPF 987.654.321-00, contrato encerrado em janeiro/2026.", "PF"),
    ("CTR_004", "Empresa ABC S.A., CNPJ 98.765.432/0001-11, 2 parcelas em atraso desde fev/2026.", "PJ"),
    ("CTR_005", "Cliente Pedro Lima, CPF 111.222.333-44, pagamentos em dia até março/2026.", "PF"),
    ("CTR_006", "Empresa Delta ME, CNPJ 55.444.333/0001-22, contrato encerrado em dez/2025.", "PJ"),
    ("CTR_007", "Cliente Maria Souza, CPF 222.333.444-55, 1 parcela em atraso desde jan/2026.", "PF"),
    ("CTR_008", "Empresa Omega Ltda, CNPJ 66.777.888/0001-33, pagamentos em dia até fev/2026.", "PJ"),
    ("CTR_009", "Cliente Carlos Rocha, CPF 333.444.555-66, contrato encerrado em nov/2025.", "PF"),
    ("CTR_010", "Empresa Sigma S.A., CNPJ 77.888.999/0001-44, 4 parcelas em atraso desde out/2025.", "PJ"),
    ("CTR_011", "Cliente Fernanda Lima, CPF 444.555.666-77, pagamentos em dia até mar/2026.", "PF"),
    ("CTR_012", "Empresa Beta ME, CNPJ 88.999.000/0001-55, contrato encerrado em out/2025.", "PJ"),
    ("CTR_013", "Cliente Ricardo Alves, CPF 555.666.777-88, 2 parcelas em atraso desde dez/2025.", "PF"),
    ("CTR_014", "Empresa Gama Ltda, CNPJ 99.000.111/0001-66, todas as parcelas pagas.", "PJ"),
    ("CTR_015", "Cliente Patricia Nunes, CPF 666.777.888-99, contrato encerrado em set/2025.", "PF"),
    ("CTR_016", "Empresa Epsilon S.A., CNPJ 11.222.333/0001-77, 1 parcela em atraso.", "PJ"),
    ("CTR_017", "Cliente Marcos Vieira, CPF 777.888.999-00, pagamentos em dia.", "PF"),
    ("CTR_018", "Empresa Zeta ME, CNPJ 22.333.444/0001-88, contrato encerrado em ago/2025.", "PJ"),
    ("CTR_019", "Cliente Juliana Castro, CPF 888.999.000-11, 3 parcelas em atraso.", "PF"),
    ("CTR_020", "Empresa Eta Ltda, CNPJ 33.444.555/0001-99, pagamentos em dia.", "PJ"),
    ("CTR_021", "Cliente Bruno Mendes, CPF 999.000.111-22, contrato encerrado em jul/2025.", "PF"),
    ("CTR_022", "Empresa Theta S.A., CNPJ 44.555.666/0001-00, 2 parcelas em atraso.", "PJ"),
    ("CTR_023", "Cliente Camila Torres, CPF 000.111.222-33, pagamentos em dia.", "PF"),
    ("CTR_024", "Empresa Iota ME, CNPJ 55.666.777/0001-11, contrato encerrado.", "PJ"),
    ("CTR_025", "Cliente Diego Barros, CPF 111.222.333-44, 1 parcela em atraso.", "PF"),
    ("CTR_026", "Empresa Kappa Ltda, CNPJ 66.777.888/0001-22, pagamentos em dia.", "PJ"),
    ("CTR_027", "Cliente Isabela Ramos, CPF 222.333.444-55, contrato encerrado em jun/2025.", "PF"),
    ("CTR_028", "Empresa Lambda S.A., CNPJ 77.888.999/0001-33, 3 parcelas em atraso.", "PJ"),
    ("CTR_029", "Cliente Gustavo Pinto, CPF 333.444.555-66, pagamentos em dia.", "PF"),
    ("CTR_030", "Empresa Mu ME, CNPJ 88.999.000/0001-44, contrato encerrado.", "PJ"),
    ("CTR_031", "Cliente Larissa Campos, CPF 444.555.666-77, 2 parcelas em atraso.", "PF"),
    ("CTR_032", "Empresa Nu Ltda, CNPJ 99.000.111/0001-55, pagamentos em dia.", "PJ"),
    ("CTR_033", "Cliente Thiago Martins, CPF 555.666.777-88, contrato encerrado.", "PF"),
    ("CTR_034", "Empresa Xi S.A., CNPJ 11.222.333/0001-66, 1 parcela em atraso.", "PJ"),
    ("CTR_035", "Cliente Aline Ferreira, CPF 666.777.888-99, pagamentos em dia.", "PF"),
    ("CTR_036", "Empresa Omicron ME, CNPJ 22.333.444/0001-77, contrato encerrado.", "PJ"),
    ("CTR_037", "Cliente Rafael Oliveira, CPF 777.888.999-00, 4 parcelas em atraso.", "PF"),
    ("CTR_038", "Empresa Pi Ltda, CNPJ 33.444.555/0001-88, pagamentos em dia.", "PJ"),
    ("CTR_039", "Cliente Natalia Costa, CPF 888.999.000-11, contrato encerrado.", "PF"),
    ("CTR_040", "Empresa Rho S.A., CNPJ 44.555.666/0001-99, 2 parcelas em atraso.", "PJ"),
    ("CTR_041", "Cliente Vinicius Lima, CPF 999.000.111-22, pagamentos em dia.", "PF"),
    ("CTR_042", "Empresa Sigma ME, CNPJ 55.666.777/0001-00, contrato encerrado.", "PJ"),
    ("CTR_043", "Cliente Beatriz Alves, CPF 000.111.222-33, 1 parcela em atraso.", "PF"),
    ("CTR_044", "Empresa Tau Ltda, CNPJ 66.777.888/0001-11, pagamentos em dia.", "PJ"),
    ("CTR_045", "Cliente Leonardo Santos, CPF 111.222.333-44, contrato encerrado.", "PF"),
    ("CTR_046", "Empresa Upsilon S.A., CNPJ 77.888.999/0001-22, 3 parcelas em atraso.", "PJ"),
    ("CTR_047", "Cliente Gabriela Rocha, CPF 222.333.444-55, pagamentos em dia.", "PF"),
    ("CTR_048", "Empresa Phi ME, CNPJ 88.999.000/0001-33, contrato encerrado.", "PJ"),
    ("CTR_049", "Cliente Lucas Nunes, CPF 333.444.555-66, 2 parcelas em atraso.", "PF"),
    ("CTR_050", "Empresa Chi Ltda, CNPJ 99.000.111/0001-44, pagamentos em dia.", "PJ"),
]

schema = StructType([
    StructField("id_contrato", StringType(), False),
    StructField("texto",       StringType(), False),
    StructField("tipo",        StringType(), False),
    StructField("status_ia",   StringType(), True),
    StructField("batch_id",    StringType(), True),
])

dados = [(id, texto, tipo, None, None) for id, texto, tipo in textos_contratos]
df_contratos = spark.createDataFrame(dados, schema)

display(df_contratos)
print(f"\nTotal de registros: {df_contratos.count()}")

# COMMAND ----------
# MAGIC %md
# MAGIC ## Cell 5 — Funções auxiliares de simulação

# COMMAND ----------

def simular_output(registro: RegistroData) -> RegistroData:
    """
    Simula o retorno da API.
    CTR_005, CTR_015, CTR_025, CTR_035, CTR_045 sempre geram erro (parcial).
    """
    random.seed(hash(registro.id))

    ids_com_erro = {"CTR_005", "CTR_015", "CTR_025", "CTR_035", "CTR_045"}

    if registro.id in ids_com_erro:
        registro.status        = StatusRegistro.ERROR
        registro.erro          = random.choice(["context_length_exceeded", "rate_limit_exceeded"])
        registro.tokens_input  = 0
        registro.tokens_output = 0
        return registro

    texto = registro.input.lower()
    if "atraso" in texto:
        classificacao = "inadimplente"
        confianca     = round(random.uniform(0.88, 0.98), 2)
    elif "encerrado" in texto:
        classificacao = "encerrado"
        confianca     = round(random.uniform(0.92, 0.99), 2)
    else:
        classificacao = "em_dia"
        confianca     = round(random.uniform(0.90, 0.99), 2)

    registro.output             = {"classificacao": classificacao, "confianca": confianca}
    registro.status             = StatusRegistro.SUCCESS
    registro.tokens_input       = random.randint(75, 110)
    registro.tokens_output      = random.randint(10, 20)
    registro.judge_relevance    = round(random.uniform(0.85, 0.99), 2)
    registro.judge_faithfulness = round(random.uniform(0.85, 0.99), 2)
    return registro


def preparar_registros(rows, prompt) -> list:
    return [
        RegistroData(id=row["id_contrato"], input=row["texto"], prompt=prompt)
        for row in rows
    ]

# COMMAND ----------
# MAGIC %md
# MAGIC ## Cell 6 — Processa os 5 batches

# COMMAND ----------

prompt_ativo       = service.carregar_prompt("classificacao_contrato")
todos_os_registros = df_contratos.collect()
tamanho_batch      = 10
batches_rows       = [todos_os_registros[i:i + tamanho_batch] for i in range(0, len(todos_os_registros), tamanho_batch)]
batch_ids          = []

for i, rows in enumerate(batches_rows, start=1):
    print(f"\n{'='*60}")
    print(f" BATCH {i}/5")
    print(f"{'='*60}")

    batch_id = f"batch_{i:03d}_{uuid.uuid4().hex[:6]}"
    batch_ids.append(batch_id)

    registros  = preparar_registros(rows, prompt_ativo)
    batch_data = BatchData(
        batch_id        = batch_id,
        modelo          = "gpt-4o",
        temperatura     = 0.2,
        max_tokens      = 500,
        total_registros = len(registros),
    )

    run_id = service.submeter_batch(batch_data, registros)
    service.atualizar_status(batch_id, StatusBatch.PROCESSING)

    resultados = [simular_output(r) for r in registros]
    sucesso    = sum(1 for r in resultados if r.sucesso)
    erro       = len(resultados) - sucesso
    print(f"\n   Resultados simulados: {sucesso} sucesso | {erro} erro")

    service.finalizar_batch(batch_id, resultados)

print(f"\n\n✅ Todos os 5 batches processados!")

# COMMAND ----------
# MAGIC %md
# MAGIC ## Cell 7 — Resumo do dia

# COMMAND ----------

service.resumo()

# COMMAND ----------
# MAGIC %md
# MAGIC ## Cell 8 — Consulta detalhada por batch

# COMMAND ----------

experiment = mlflow.get_experiment_by_name("/Users/eduardosch26@gmail.com/teste_batch_llm")

runs = mlflow.search_runs(
    experiment_ids=[experiment.experiment_id],
    filter_string=f"params.data_envio = '{date.today()}' AND params.batch_id != ''",
    order_by=["start_time ASC"]
)

colunas = [c for c in [
    "params.batch_id",
    "tags.status",
    "metrics.total_registros",
    "metrics.total_sucesso",
    "metrics.total_erro",
    "metrics.taxa_sucesso",
    "metrics.tokens_input_total",
    "metrics.tokens_input_media",
    "metrics.custo_estimado_usd",
    "metrics.judge_relevance_media",
] if c in runs.columns]

print("📊 Todos os batches de hoje:\n")
print(runs[colunas].to_string(index=False))

# COMMAND ----------
# MAGIC %md
# MAGIC ## Cell 9 — Estatísticas consolidadas

# COMMAND ----------

runs_completos = runs[runs["tags.status"].isin(["completed", "partial"])]

print("📈 Estatísticas consolidadas dos 5 batches\n")
print("─" * 50)
print(f"Total batches:         {len(runs_completos)}")
print(f"Total registros:       {runs_completos['metrics.total_registros'].sum():.0f}")
print(f"Total sucesso:         {runs_completos['metrics.total_sucesso'].sum():.0f}")
print(f"Total erro:            {runs_completos['metrics.total_erro'].sum():.0f}")
print(f"Taxa sucesso média:    {runs_completos['metrics.taxa_sucesso'].mean():.1%}")
print(f"Tokens input total:    {runs_completos['metrics.tokens_input_total'].sum():,.0f}")
print(f"Tokens input média:    {runs_completos['metrics.tokens_input_media'].mean():.1f} por requisição")
print(f"Custo total:           U$ {runs_completos['metrics.custo_estimado_usd'].sum():.4f}")
print(f"Judge relevance média: {runs_completos['metrics.judge_relevance_media'].mean():.2f}")

# COMMAND ----------
# MAGIC %md
# MAGIC ## Cell 10 — Registros com erro para reprocessamento

# COMMAND ----------

print("🔄 Registros com erro (candidatos a reprocessamento):\n")

for batch_id in batch_ids:
    try:
        output_path = f"/Volumes/workspace/default/audios/batches/output_{batch_id}.jsonl"
        with open(output_path) as f:
            linhas = [json.loads(l) for l in f]
        erros = [l for l in linhas if l["status"] == "error"]
        if erros:
            print(f"Batch: {batch_id}")
            for e in erros:
                print(f"  {e['id']} → {e['erro']}")
    except Exception as ex:
        print(f"  (não foi possível ler output de {batch_id}: {ex})")
