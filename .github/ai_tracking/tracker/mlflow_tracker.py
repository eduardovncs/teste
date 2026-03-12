import mlflow
from mlflow import MlflowClient
from datetime import datetime
from typing import Optional

from ..models import BatchData, StatusBatch, MetricasLote


class MLflowTracker:
    """
    Responsável por toda a comunicação com o MLflow.
    Abre, atualiza e finaliza runs. Loga métricas, parâmetros e artefatos.
    """

    def __init__(self, experiment_name: str):
        """
        Parâmetros
        ----------
        experiment_name : str
            Path do experimento no Databricks.
            Ex: "/Users/usuario@email.com/meu_experimento"
        """
        self.experiment_name = experiment_name
        self.client          = MlflowClient()
        mlflow.set_experiment(experiment_name)

    def iniciar_run(self, batch_data: BatchData) -> str:
        """
        Abre um run no MLflow e loga os parâmetros do batch.

        Retorno
        -------
        run_id : str
        """
        with mlflow.start_run(
            run_name=f"batch_{batch_data.data_envio}_{batch_data.batch_id}"
        ) as run:
            run_id = run.info.run_id

            for chave, valor in batch_data.to_dict().items():
                mlflow.log_param(chave, valor)

            mlflow.set_tag("status",       StatusBatch.SUBMITTED.value)
            mlflow.set_tag("ultimo_check", datetime.now().isoformat())

        print(f"✅ Run iniciado: {run_id}")
        return run_id

    def atualizar_status(self, run_id: str, status: StatusBatch):
        """Atualiza a tag de status de um run existente."""
        with mlflow.start_run(run_id=run_id):
            mlflow.set_tag("status",       status.value)
            mlflow.set_tag("ultimo_check", datetime.now().isoformat())

        print(f"✅ Status atualizado → {status.value}")

    def logar_metricas(self, run_id: str, metricas: MetricasLote):
        """Loga as métricas agregadas do lote em um run existente."""
        with mlflow.start_run(run_id=run_id):
            for chave, valor in metricas.to_dict().items():
                mlflow.log_metric(chave, valor)

    def logar_artefato(self, run_id: str, path: str, destino: str):
        """Loga um arquivo como artefato em um run existente."""
        with mlflow.start_run(run_id=run_id):
            mlflow.log_artifact(path, destino)

    def finalizar_run(self, run_id: str, status: StatusBatch):
        """Fecha o run com o status final."""
        with mlflow.start_run(run_id=run_id):
            mlflow.set_tag("status",       status.value)
            mlflow.set_tag("ultimo_check", datetime.now().isoformat())

        print(f"✅ Run finalizado → {status.value}")

    def buscar_runs(self, filtro: str = "", order_by: str = "start_time DESC"):
        """
        Busca runs do experimento.

        Parâmetros
        ----------
        filtro   : str — ex: "tags.status = 'completed'"
        order_by : str — coluna de ordenação

        Retorno
        -------
        pandas.DataFrame
        """
        experiment = mlflow.get_experiment_by_name(self.experiment_name)
        return mlflow.search_runs(
            experiment_ids=[experiment.experiment_id],
            filter_string=filtro,
            order_by=[order_by]
        )

    def buscar_pendentes(self):
        """Retorna todos os runs com status submitted ou processing."""
        return self.buscar_runs(
            filtro="tags.status = 'submitted' OR tags.status = 'processing'"
        )
