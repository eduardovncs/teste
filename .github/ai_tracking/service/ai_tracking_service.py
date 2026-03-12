import os
import mlflow
from datetime import date
from typing import List, Optional

from ..models import PromptData, RegistroData, BatchData, MetricasLote, StatusBatch
from ..repository import PromptRepository
from ..controller import BatchController
from ..tracker import MLflowTracker, TraceLogger


class AITrackingService:
    """
    Orquestrador principal do sistema de tracking de IA.
    Coordena o fluxo completo: prompt → batch → traces → métricas.

    Uso
    ---
    service = AITrackingService(
        experiment_name="/Users/usuario@email.com/meu_experimento",
        volume_path="/Volumes/workspace/default/audios"
    )

    # Registra prompt
    service.registrar_prompt("classificacao_pf", template, "versão inicial")

    # Submete batch
    run_id = service.submeter_batch(batch_data, registros)

    # Atualiza status durante polling
    service.atualizar_status(batch_id, StatusBatch.PROCESSING)

    # Finaliza quando a API retornar
    service.finalizar_batch(batch_id, resultados)

    # Resumo do dia
    service.resumo()
    """

    def __init__(self, experiment_name: str, volume_path: str):
        """
        Parâmetros
        ----------
        experiment_name : str — path do experimento no Databricks
        volume_path     : str — caminho raiz do Volume
        """
        self.experiment_name = experiment_name
        self.volume_path     = volume_path

        # Instancia as dependências
        self._prompt_repo  = PromptRepository(
            prompts_path=f"{volume_path}/prompts"
        )
        self._batch_ctrl   = BatchController(
            batches_path=f"{volume_path}/batches",
            control_path=f"{volume_path}/control"
        )
        self._tracker      = MLflowTracker(experiment_name)
        self._trace_logger = TraceLogger(self._tracker)

        print(f"✅ AITrackingService iniciado")
        print(f"   experimento: {experiment_name}")
        print(f"   volume:      {volume_path}")

    # ── Gerenciamento de Prompts ──────────────────────────────

    def registrar_prompt(self, nome: str, template: str, changelog: str) -> PromptData:
        """Registra uma nova versão do prompt."""
        return self._prompt_repo.registrar(nome, template, changelog)

    def carregar_prompt(self, nome: str, versao: Optional[str] = None) -> PromptData:
        """Carrega a versão ativa (ou específica) de um prompt."""
        return self._prompt_repo.carregar(nome, versao)

    def listar_versoes(self, nome: str) -> List[PromptData]:
        """Lista o histórico de versões de um prompt."""
        return self._prompt_repo.listar_versoes(nome)

    # ── Controle de Batch ─────────────────────────────────────

    def submeter_batch(
        self,
        batch_data: BatchData,
        registros:  List[RegistroData],
    ) -> str:
        """
        Prepara e submete um batch para processamento.
        Gera o JSONL, abre o run no MLflow e persiste o run_id.

        Retorno
        -------
        run_id : str
        """
        # Gera o JSONL de input
        input_path = self._batch_ctrl.gerar_input_jsonl(
            batch_id   = batch_data.batch_id,
            registros  = registros,
            modelo     = batch_data.modelo,
            max_tokens = batch_data.max_tokens,
        )

        # Abre o run no MLflow
        run_id = self._tracker.iniciar_run(batch_data)
        batch_data.run_id = run_id

        # Loga o input como artefato
        self._tracker.logar_artefato(run_id, input_path, "inputs")

        # Persiste o run_id para retomada assíncrona
        self._batch_ctrl.salvar_run_id(batch_data.batch_id, run_id)

        print(f"✅ Batch submetido: {batch_data.batch_id} | run_id: {run_id}")
        return run_id

    def atualizar_status(self, batch_id: str, status: StatusBatch):
        """Atualiza o status de um batch em andamento."""
        run_id = self._batch_ctrl.recuperar_run_id(batch_id)
        self._tracker.atualizar_status(run_id, status)

    def finalizar_batch(self, batch_id: str, resultados: List[RegistroData]):
        """
        Finaliza o batch: persiste output, loga métricas e traces.

        Parâmetros
        ----------
        batch_id  : str
        resultados: lista de RegistroData com status, output e tokens preenchidos
        """
        run_id = self._batch_ctrl.recuperar_run_id(batch_id)

        # Persiste o output no Volume
        output_path = self._batch_ctrl.salvar_output_jsonl(batch_id, resultados)

        # Calcula métricas
        metricas       = MetricasLote.calcular(resultados)
        status_batch   = metricas.definir_status_batch()

        # Loga no MLflow
        self._tracker.logar_metricas(run_id, metricas)
        self._tracker.logar_artefato(run_id, output_path, "outputs")
        self._trace_logger.logar_batch_traces(run_id, resultados)
        self._tracker.finalizar_run(run_id, status_batch)

        # Exibe resumo
        print(f"\n📊 Resultado do batch: {batch_id}")
        print(f"   status:        {status_batch.value}")
        print(f"   sucesso:       {metricas.total_sucesso}/{metricas.total_registros}")
        print(f"   taxa sucesso:  {metricas.taxa_sucesso:.1%}")
        print(f"   tokens input:  {metricas.tokens_input_total:,}")
        print(f"   tokens output: {metricas.tokens_output_total:,}")
        print(f"   custo:         U$ {metricas.custo_estimado_usd:.4f}")

        return metricas

    # ── Consultas ─────────────────────────────────────────────

    def buscar_pendentes(self):
        """Retorna todos os batches com status submitted ou processing."""
        return self._tracker.buscar_pendentes()

    def resumo(self, data: Optional[str] = None):
        """
        Exibe o resumo dos batches de uma data (padrão: hoje).

        Parâmetros
        ----------
        data : str, opcional — ex: "2026-03-10". Se None, usa hoje.
        """
        data  = data or str(date.today())
        runs  = self._tracker.buscar_runs(
            filtro=f"params.data_envio = '{data}' AND tags.status != 'prompt_registry'"
        )

        if runs.empty:
            print(f"Nenhum batch encontrado em {data}")
            return

        print(f"\n📊 Resumo — {data}")
        print("─" * 65)
        print(f"Total de batches: {len(runs)}")

        col_custo  = "metrics.custo_estimado_usd"
        col_tokens = "metrics.tokens_input_total"
        col_judge  = "metrics.judge_relevance_media"

        if col_tokens in runs.columns:
            print(f"Tokens input:     {runs[col_tokens].sum():,.0f}")
        if col_custo in runs.columns:
            print(f"Custo total:      U$ {runs[col_custo].sum():.4f}")
        if col_judge in runs.columns:
            print(f"Judge relevance:  {runs[col_judge].mean():.2f}")

        colunas = [c for c in [
            "params.batch_id",
            "params.modelo",
            "tags.status",
            col_custo,
            "metrics.total_sucesso",
            "metrics.total_erro",
        ] if c in runs.columns]

        print()
        print(runs[colunas].to_string(index=False))
