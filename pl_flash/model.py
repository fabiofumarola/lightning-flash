from typing import Callable, Mapping, Sequence, Union, Type

import torch
from torch import nn
import torch.nn.functional as F

import pytorch_lightning as pl

from pl_flash.utils import get_callable_dict


class Model(pl.LightningModule):
    def __init__(
        self,
        model: nn.Module,
        loss_fn: Union[Callable, Mapping, Sequence],
        optimizer: Type[torch.optim.Optimizer] = torch.optim.Adam,
        metrics: Union[Callable, Mapping, Sequence, None] = None,
        learning_rate: float = 1e-3,
    ):
        super().__init__()
        self.model = model
        self.loss_fn = loss_fn
        self.optimizer_cls = optimizer
        self.metrics = get_callable_dict(metrics) if metrics is not None else {}
        self.loss_fn = get_callable_dict(loss_fn)
        self.learning_rate = learning_rate
        # TODO: should we save more? Bug on some regarding yaml if we save metrics
        self.save_hyperparameters("learning_rate", "optimizer")

    def step(self, batch, batch_idx):
        x, y = batch
        y_hat = self.forward(x)
        losses = {name: l_fn(y_hat, y) for name, l_fn in self.loss_fn.items()}
        logs = {name: metric(y_hat, y) for name, metric in self.metrics.items()}
        logs.update(losses)
        logs["total_loss"] = sum(losses.values())
        return logs["total_loss"], logs

    def forward(self, x):
        return self.model(x)

    def training_step(self, batch, batch_idx):
        loss, logs = self.step(batch, batch_idx)
        result = pl.TrainResult(minimize=loss)
        result.log_dict({f"train_{k}": v for k, v in logs.items()}, on_step=True, on_epoch=False)
        return result

    def validation_step(self, batch, batch_idx):
        loss, logs = self.step(batch, batch_idx)
        result = pl.EvalResult(checkpoint_on=loss)
        result.log_dict({f"val_{k}": v for k, v in logs.items()})
        return result

    def test_step(self, batch, batch_idx):
        _, logs = self.step(batch, batch_idx)
        result = pl.EvalResult()
        result.log_dict({f"test_{k}": v for k, v in logs.items()})
        return result

    def configure_optimizers(self):
        return self.optimizer_cls(self.parameters(), lr=self.learning_rate)
