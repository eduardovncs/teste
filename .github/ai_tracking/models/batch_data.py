from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional


class StatusBatch(Enum):
    SUBMITTED  = "submitted"
    PROCESSING = "processing"
    COMPLETED  = "completed"
    PARTIAL    = "partial"
    FAILED     = "failed"


@dataclass
class BatchData:
    """
    Representa os metadados de um batch de processamento.
    """
    batch_id:         str
    modelo:           str
    temperatura:      float
    max_tokens:       int
    total_registros:  int
    data_envio:       str             = str(date.today())
    status:           StatusBatch     = StatusBatch.SUBMITTED
    prompt_modo:      str             = "dinamico"
    run_id:           Optional[str]   = None

    def to_dict(self) -> dict:
        return {
            "batch_id":        self.batch_id,
            "modelo":          self.modelo,
            "temperatura":     self.temperatura,
            "max_tokens":      self.max_tokens,
            "total_registros": self.total_registros,
            "data_envio":      self.data_envio,
            "status":          self.status.value,
            "prompt_modo":     self.prompt_modo,
        }
