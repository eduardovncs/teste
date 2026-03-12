from dataclasses import dataclass
from datetime import datetime


@dataclass
class PromptData:
    """
    Representa uma versão de prompt armazenada no Volume.
    """
    nome:       str
    versao:     str
    hash:       str
    template:   str
    changelog:  str
    criado_em:  str
    ativo:      bool

    def aplicar(self, input: str) -> str:
        """Substitui {{input}} no template pelo texto fornecido."""
        return self.template.replace("{{input}}", input)

    @staticmethod
    def from_dict(data: dict) -> "PromptData":
        return PromptData(
            nome      = data["nome"],
            versao    = data["versao"],
            hash      = data["hash"],
            template  = data["template"],
            changelog = data["changelog"],
            criado_em = data["criado_em"],
            ativo     = data["ativo"],
        )

    def to_dict(self) -> dict:
        return {
            "nome":      self.nome,
            "versao":    self.versao,
            "hash":      self.hash,
            "template":  self.template,
            "changelog": self.changelog,
            "criado_em": self.criado_em,
            "ativo":     self.ativo,
        }
