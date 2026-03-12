from dataclasses import dataclass, field
from typing import List
from .registro_data import RegistroData, StatusRegistro
from .batch_data import StatusBatch


@dataclass
class MetricasLote:
    """
    Calcula e armazena métricas agregadas de um batch.

    Tokens e custo:
    - SUCCESS        → tokens contabilizados normalmente
    - API_ERROR      → tokens = 0 (não foi processado)
    - BUSINESS_ERROR → tokens contabilizados (foi processado mas inválido — você pagou!)
    """
    total_registros:          int   = 0
    total_sucesso:            int   = 0
    total_erro:               int   = 0
    total_api_error:          int   = 0   # API não retornou
    total_business_error:     int   = 0   # API retornou mas inválido
    taxa_sucesso:             float = 0.0
    tokens_input_total:       int   = 0
    tokens_output_total:      int   = 0
    tokens_input_media:       float = 0.0
    tokens_output_media:      float = 0.0
    tokens_input_max:         int   = 0
    tokens_input_min:         int   = 0
    custo_estimado_usd:       float = 0.0
    judge_relevance_media:    float = 0.0
    judge_faithfulness_media: float = 0.0

    _preco_input_por_token:  float = field(default=0.000005, repr=False)
    _preco_output_por_token: float = field(default=0.000015, repr=False)

    @staticmethod
    def calcular(
        registros:    List[RegistroData],
        preco_input:  float = 0.000005,
        preco_output: float = 0.000015,
    ) -> "MetricasLote":

        sucesso         = [r for r in registros if r.status == StatusRegistro.SUCCESS]
        api_errors      = [r for r in registros if r.status == StatusRegistro.API_ERROR]
        business_errors = [r for r in registros if r.status == StatusRegistro.BUSINESS_ERROR]
        erro            = api_errors + business_errors

        # Tokens: sucesso + business_error (ambos consumiram tokens)
        # API_ERROR não conta — não foi processado
        com_tokens    = sucesso + business_errors
        tokens_input  = [r.tokens_input  for r in com_tokens]
        tokens_output = [r.tokens_output for r in com_tokens]

        juiz_relevance    = [r.judge_relevance    for r in sucesso if r.judge_relevance    is not None]
        juiz_faithfulness = [r.judge_faithfulness for r in sucesso if r.judge_faithfulness is not None]

        total_ti = sum(tokens_input)
        total_to = sum(tokens_output)

        return MetricasLote(
            total_registros          = len(registros),
            total_sucesso            = len(sucesso),
            total_erro               = len(erro),
            total_api_error          = len(api_errors),
            total_business_error     = len(business_errors),
            taxa_sucesso             = len(sucesso) / len(registros) if registros else 0.0,
            tokens_input_total       = total_ti,
            tokens_output_total      = total_to,
            tokens_input_media       = total_ti  / len(com_tokens) if com_tokens else 0.0,
            tokens_output_media      = total_to  / len(com_tokens) if com_tokens else 0.0,
            tokens_input_max         = max(tokens_input)  if com_tokens else 0,
            tokens_input_min         = min(tokens_input)  if com_tokens else 0,
            custo_estimado_usd       = round((total_ti * preco_input) + (total_to * preco_output), 6),
            judge_relevance_media    = sum(juiz_relevance)    / len(juiz_relevance)    if juiz_relevance    else 0.0,
            judge_faithfulness_media = sum(juiz_faithfulness) / len(juiz_faithfulness) if juiz_faithfulness else 0.0,
        )

    def definir_status_batch(self) -> StatusBatch:
        if self.total_sucesso == self.total_registros:
            return StatusBatch.COMPLETED
        elif self.total_sucesso == 0:
            return StatusBatch.FAILED
        else:
            return StatusBatch.PARTIAL

    def to_dict(self) -> dict:
        return {
            "total_registros":          self.total_registros,
            "total_sucesso":            self.total_sucesso,
            "total_erro":               self.total_erro,
            "total_api_error":          self.total_api_error,
            "total_business_error":     self.total_business_error,
            "taxa_sucesso":             self.taxa_sucesso,
            "tokens_input_total":       self.tokens_input_total,
            "tokens_output_total":      self.tokens_output_total,
            "tokens_input_media":       self.tokens_input_media,
            "tokens_output_media":      self.tokens_output_media,
            "tokens_input_max":         self.tokens_input_max,
            "tokens_input_min":         self.tokens_input_min,
            "custo_estimado_usd":       self.custo_estimado_usd,
            "judge_relevance_media":    self.judge_relevance_media,
            "judge_faithfulness_media": self.judge_faithfulness_media,
        }
