import mlflow
import mlflow.entities
from mlflow.entities import SpanStatus, SpanStatusCode
from typing import List

from ..models import RegistroData, PromptData, StatusRegistro
from .mlflow_tracker import MLflowTracker


class TraceLogger:
    """
    Responsável por logar traces individuais por linha do batch.

    Trata três cenários:
    - SUCCESS        → input + output + tokens + judge
    - API_ERROR      → input + erro (sem output, sem tokens — API não retornou)
    - BUSINESS_ERROR → input + output inválido + tokens (API retornou mas inválido)
    """

    def __init__(self, tracker: MLflowTracker):
        self._tracker = tracker

    def logar_batch_traces(self, run_id: str, registros: List[RegistroData]):
        """
        Loga um trace para cada registro do batch dentro do run ativo.

        Parâmetros
        ----------
        run_id    : str
        registros : lista de RegistroData
        """
        sucesso         = sum(1 for r in registros if r.status == StatusRegistro.SUCCESS)
        api_errors      = sum(1 for r in registros if r.status == StatusRegistro.API_ERROR)
        business_errors = sum(1 for r in registros if r.status == StatusRegistro.BUSINESS_ERROR)

        with mlflow.start_run(run_id=run_id):
            for registro in registros:
                if registro.status == StatusRegistro.SUCCESS:
                    self._logar_sucesso(registro)
                elif registro.status == StatusRegistro.API_ERROR:
                    self._logar_api_error(registro)
                else:
                    self._logar_business_error(registro)

        print(f"✅ Traces logados: {sucesso} sucesso | {api_errors} api_error | {business_errors} business_error")

    # ── Privados ──────────────────────────────────────────────

    def _logar_sucesso(self, registro: RegistroData):
        """Input enviado, output recebido e válido."""
        with mlflow.start_span(
            name=f"registro_{registro.id}",
            span_type=mlflow.entities.SpanType.LLM
        ) as span:
            span.set_inputs({
                "id":             registro.id,
                "texto":          registro.input,
                "prompt_nome":    registro.prompt.nome,
                "prompt_versao":  registro.prompt.versao,
                "prompt_hash":    registro.prompt.hash,
                "prompt_applied": registro.prompt.aplicar(registro.input),
            })

            span.set_outputs(registro.output)

            atributos = {
                "status":        registro.status.value,
                "tokens_input":  registro.tokens_input,
                "tokens_output": registro.tokens_output,
                "prompt_versao": registro.prompt.versao,
            }

            if registro.judge_relevance is not None:
                atributos["judge_relevance"] = registro.judge_relevance
            if registro.judge_faithfulness is not None:
                atributos["judge_faithfulness"] = registro.judge_faithfulness

            span.set_attributes(atributos)
            span.set_status(SpanStatus(SpanStatusCode.OK))

    def _logar_api_error(self, registro: RegistroData):
        """
        Input enviado mas output NÃO recebido — API falhou.
        tokens = 0 pois não foi processado.
        """
        with mlflow.start_span(
            name=f"registro_{registro.id}",
            span_type=mlflow.entities.SpanType.LLM
        ) as span:
            span.set_inputs({
                "id":            registro.id,
                "texto":         registro.input,
                "prompt_nome":   registro.prompt.nome,
                "prompt_versao": registro.prompt.versao,
            })

            span.set_outputs({
                "output": None,
                "erro":   registro.erro,
            })

            span.set_attributes({
                "status":        registro.status.value,
                "erro":          registro.erro,
                "tokens_input":  0,
                "tokens_output": 0,
            })

            span.set_status(SpanStatus(SpanStatusCode.ERROR, registro.erro))

    def _logar_business_error(self, registro: RegistroData):
        """
        Input enviado, output recebido mas inválido — erro de negócio.
        tokens são logados pois foram consumidos mesmo com resultado inválido.
        """
        with mlflow.start_span(
            name=f"registro_{registro.id}",
            span_type=mlflow.entities.SpanType.LLM
        ) as span:
            span.set_inputs({
                "id":            registro.id,
                "texto":         registro.input,
                "prompt_nome":   registro.prompt.nome,
                "prompt_versao": registro.prompt.versao,
            })

            span.set_outputs({
                "output_raw": registro.output,
                "erro":       registro.erro,
            })

            span.set_attributes({
                "status":        registro.status.value,
                "erro":          registro.erro,
                "tokens_input":  registro.tokens_input,
                "tokens_output": registro.tokens_output,
            })

            span.set_status(SpanStatus(SpanStatusCode.ERROR, registro.erro))
