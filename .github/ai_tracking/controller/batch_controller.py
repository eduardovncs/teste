import os
import json
from typing import List, Optional

from ..models import RegistroData, PromptData, StatusRegistro


class BatchController:
    """
    Responsável pela geração, persistência e controle dos arquivos JSONL
    e pelo vínculo entre batch_id e run_id do MLflow.
    """

    def __init__(self, batches_path: str, control_path: str):
        """
        Parâmetros
        ----------
        batches_path : str — pasta para os arquivos JSONL
        control_path : str — pasta para os arquivos de controle (run_id)
        """
        self.batches_path = batches_path
        self.control_path = control_path

        os.makedirs(batches_path, exist_ok=True)
        os.makedirs(control_path, exist_ok=True)

    def gerar_input_jsonl(
        self,
        batch_id:  str,
        registros: List[RegistroData],
        modelo:    str,
        max_tokens: int,
    ) -> str:
        """
        Gera o arquivo JSONL de input para envio à API.
        Aplica o prompt de cada registro automaticamente.

        Parâmetros
        ----------
        batch_id   : str
        registros  : lista de RegistroData (cada um com seu prompt)
        modelo     : str  — ex: "gpt-4o"
        max_tokens : int

        Retorno
        -------
        path do arquivo gerado
        """
        path = f"{self.batches_path}/input_{batch_id}.jsonl"

        with open(path, "w", encoding="utf-8") as f:
            for registro in registros:
                payload = {
                    "custom_id": registro.id,
                    "body": {
                        "model":      modelo,
                        "max_tokens": max_tokens,
                        "messages": [
                            {
                                "role":    "user",
                                "content": registro.prompt.aplicar(registro.input)
                            }
                        ]
                    }
                }
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")

        print(f"✅ JSONL gerado: {path} | {len(registros)} registros")
        return path

    def salvar_output_jsonl(self, batch_id: str, registros: List[RegistroData]) -> str:
        """
        Persiste os resultados do batch no Volume.

        Retorno
        -------
        path do arquivo gerado
        """
        path = f"{self.batches_path}/output_{batch_id}.jsonl"

        with open(path, "w", encoding="utf-8") as f:
            for registro in registros:
                f.write(json.dumps(registro.to_dict(), ensure_ascii=False) + "\n")

        print(f"✅ Output salvo: {path}")
        return path

    def carregar_output_jsonl(
        self,
        batch_id: str,
        prompts_por_id: Optional[dict] = None
    ) -> List[RegistroData]:
        """
        Carrega o output de um batch do Volume e reconstrói a lista de RegistroData.

        Parâmetros
        ----------
        batch_id       : str
        prompts_por_id : dict opcional {id_registro: PromptData}
                         necessário para reconstruir o PromptData de cada linha

        Retorno
        -------
        lista de RegistroData
        """
        path = f"{self.batches_path}/output_{batch_id}.jsonl"

        if not os.path.exists(path):
            raise FileNotFoundError(f"Output não encontrado: {path}")

        registros = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                data    = json.loads(line)
                prompt  = prompts_por_id.get(data["id"]) if prompts_por_id else None

                registro = RegistroData(
                    id                 = data["id"],
                    input              = data["input"],
                    prompt             = prompt,
                    output             = data.get("output"),
                    status             = StatusRegistro(data["status"]),
                    erro               = data.get("erro"),
                    tokens_input       = data.get("tokens_input", 0),
                    tokens_output      = data.get("tokens_output", 0),
                    judge_relevance    = data.get("judge_relevance"),
                    judge_faithfulness = data.get("judge_faithfulness"),
                )
                registros.append(registro)

        return registros

    def salvar_run_id(self, batch_id: str, run_id: str):
        """Persiste o run_id no Volume para retomada assíncrona."""
        with open(f"{self.control_path}/{batch_id}.txt", "w") as f:
            f.write(run_id)

    def recuperar_run_id(self, batch_id: str) -> str:
        """Recupera o run_id de um batch pelo batch_id."""
        path = f"{self.control_path}/{batch_id}.txt"
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"run_id não encontrado para batch_id: {batch_id}. "
                f"Verifique se o batch foi iniciado corretamente."
            )
        with open(path) as f:
            return f.read().strip()
