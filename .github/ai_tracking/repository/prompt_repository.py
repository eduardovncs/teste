import os
import json
import hashlib
import mlflow
from datetime import datetime
from typing import Optional, List

from ..models import PromptData


class PromptRepository:
    """
    Gerencia o versionamento de prompts no Volume do Databricks.
    Persiste os prompts como arquivos JSON e loga cada versão no MLflow.
    """

    def __init__(self, prompts_path: str):
        """
        Parâmetros
        ----------
        prompts_path : str
            Caminho da pasta de prompts no Volume.
            Ex: "/Volumes/workspace/default/audios/prompts"
        """
        self.prompts_path = prompts_path
        os.makedirs(prompts_path, exist_ok=True)

    def registrar(self, nome: str, template: str, changelog: str) -> PromptData:
        """
        Registra uma nova versão do prompt.
        Desativa automaticamente a versão anterior.

        Parâmetros
        ----------
        nome      : str — identificador do prompt (ex: "classificacao_pf")
        template  : str — texto com {{input}} como variável
        changelog : str — descrição do que mudou

        Retorno
        -------
        PromptData com os dados da versão criada
        """
        versoes_existentes = self._listar_arquivos(nome)
        nova_versao        = f"v{len(versoes_existentes) + 1}"

        # Desativa versão anterior
        self._desativar_anterior(nome)

        prompt_data = PromptData(
            nome      = nome,
            versao    = nova_versao,
            hash      = hashlib.md5(template.encode()).hexdigest(),
            template  = template,
            changelog = changelog,
            criado_em = datetime.now().isoformat(),
            ativo     = True,
        )

        # Persiste no Volume
        path = f"{self.prompts_path}/{nome}_{nova_versao}.json"
        with open(path, "w") as f:
            json.dump(prompt_data.to_dict(), f, ensure_ascii=False, indent=2)

        # Loga no MLflow como run separado
        with mlflow.start_run(run_name=f"prompt_{nome}_{nova_versao}"):
            mlflow.set_tag("tipo",            "prompt_registry")
            mlflow.log_param("prompt_nome",   nome)
            mlflow.log_param("prompt_versao", nova_versao)
            mlflow.log_param("prompt_hash",   prompt_data.hash)
            mlflow.set_tag("changelog",       changelog)
            mlflow.log_text(template,         "prompt/template.txt")

        print(f"✅ Prompt registrado: {nome} {nova_versao} | hash: {prompt_data.hash[:8]}...")
        return prompt_data

    def carregar(self, nome: str, versao: Optional[str] = None) -> PromptData:
        """
        Carrega um prompt do Volume.

        Parâmetros
        ----------
        nome   : str           — identificador do prompt
        versao : str, opcional — ex: "v2". Se None, carrega a versão ativa.

        Retorno
        -------
        PromptData
        """
        if versao:
            path = f"{self.prompts_path}/{nome}_{versao}.json"
            if not os.path.exists(path):
                raise FileNotFoundError(f"Prompt não encontrado: {nome} {versao}")
        else:
            arquivos = self._listar_arquivos(nome)
            if not arquivos:
                raise ValueError(f"Nenhum prompt encontrado para: {nome}")
            path = f"{self.prompts_path}/{arquivos[-1]}"

        with open(path) as f:
            data = json.load(f)

        prompt = PromptData.from_dict(data)
        print(f"✅ Prompt carregado: {prompt.nome} {prompt.versao} | hash: {prompt.hash[:8]}...")
        return prompt

    def listar_versoes(self, nome: str) -> List[PromptData]:
        """Lista o histórico completo de versões de um prompt."""
        arquivos = self._listar_arquivos(nome)

        if not arquivos:
            print(f"Nenhuma versão encontrada para: {nome}")
            return []

        versoes = []
        print(f"\n📋 Histórico — {nome}")
        print("─" * 65)

        for arquivo in arquivos:
            with open(f"{self.prompts_path}/{arquivo}") as f:
                data    = json.load(f)
            prompt  = PromptData.from_dict(data)
            status  = "✅ ativo  " if prompt.ativo else "   inativo"
            print(f"{status} | {prompt.versao} | {prompt.criado_em[:10]} | {prompt.changelog}")
            versoes.append(prompt)

        return versoes

    # ── Privados ──────────────────────────────────────────────

    def _listar_arquivos(self, nome: str) -> List[str]:
        return sorted([
            f for f in os.listdir(self.prompts_path)
            if f.startswith(nome) and f.endswith(".json")
        ])

    def _desativar_anterior(self, nome: str):
        for arquivo in self._listar_arquivos(nome):
            path = f"{self.prompts_path}/{arquivo}"
            with open(path) as f:
                data = json.load(f)
            if data.get("ativo"):
                data["ativo"] = False
                with open(path, "w") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
