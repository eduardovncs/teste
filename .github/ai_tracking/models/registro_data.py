from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from .prompt_data import PromptData


class StatusRegistro(Enum):
    SUCCESS        = "success"         # processou e resultado válido
    API_ERROR      = "api_error"       # API não retornou — output = None, tokens = 0
    BUSINESS_ERROR = "business_error"  # API retornou mas resultado inválido — tokens consumidos


@dataclass
class RegistroData:
    """
    Representa uma linha do batch — input, output, status e métricas.

    Status possíveis:
    - SUCCESS        → input enviado, output recebido e válido
    - API_ERROR      → input enviado, output NÃO recebido (falha na API)
    - BUSINESS_ERROR → input enviado, output recebido mas inválido (guardrail)
    """
    id:                  str
    input:               str
    prompt:              PromptData
    output:              Optional[dict]  = None
    status:              StatusRegistro  = StatusRegistro.SUCCESS
    erro:                Optional[str]   = None
    tokens_input:        int             = 0
    tokens_output:       int             = 0
    judge_relevance:     Optional[float] = None
    judge_faithfulness:  Optional[float] = None
    tentativas:          int             = 1    # controle de retry futuro

    @property
    def sucesso(self) -> bool:
        return self.status == StatusRegistro.SUCCESS

    @property
    def falhou(self) -> bool:
        return self.status in (StatusRegistro.API_ERROR, StatusRegistro.BUSINESS_ERROR)

    def to_dict(self) -> dict:
        return {
            "id":                 self.id,
            "input":              self.input,
            "output":             self.output,
            "status":             self.status.value,
            "erro":               self.erro,
            "tokens_input":       self.tokens_input,
            "tokens_output":      self.tokens_output,
            "judge_relevance":    self.judge_relevance,
            "judge_faithfulness": self.judge_faithfulness,
            "prompt_nome":        self.prompt.nome,
            "prompt_versao":      self.prompt.versao,
            "prompt_hash":        self.prompt.hash,
        }
