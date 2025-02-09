# Copyright The PyTorch Lightning team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
from typing import Tuple

import numpy as np
import pytest
import torch

from flash import Trainer
from flash.core.data.data_pipeline import DataPipeline
from flash.core.data.data_source import DefaultDataKeys
from flash.core.utilities.imports import _IMAGE_AVAILABLE
from flash.image import SemanticSegmentation
from flash.image.segmentation.data import SemanticSegmentationPreprocess

# ======== Mock functions ========


class DummyDataset(torch.utils.data.Dataset):
    size: Tuple[int, int] = (224, 224)
    num_classes: int = 8

    def __getitem__(self, index):
        return {
            DefaultDataKeys.INPUT: torch.rand(3, *self.size),
            DefaultDataKeys.TARGET: torch.randint(self.num_classes - 1, self.size),
        }

    def __len__(self) -> int:
        return 10


# ==============================


@pytest.mark.skipif(not _IMAGE_AVAILABLE, reason="image libraries aren't installed.")
def test_smoke():
    model = SemanticSegmentation(num_classes=1)
    assert model is not None


@pytest.mark.skipif(not _IMAGE_AVAILABLE, reason="image libraries aren't installed.")
@pytest.mark.parametrize("num_classes", [8, 256])
@pytest.mark.parametrize("img_shape", [(1, 3, 224, 192), (2, 3, 127, 212)])
def test_forward(num_classes, img_shape):
    model = SemanticSegmentation(
        num_classes=num_classes,
        backbone='fcn_resnet50',
    )

    B, C, H, W = img_shape
    img = torch.rand(B, C, H, W)

    out = model(img)
    assert out.shape == (B, num_classes, H, W)


@pytest.mark.skipif(not _IMAGE_AVAILABLE, reason="image libraries aren't installed.")
def test_init_train(tmpdir):
    model = SemanticSegmentation(num_classes=10)
    train_dl = torch.utils.data.DataLoader(DummyDataset())
    trainer = Trainer(default_root_dir=tmpdir, fast_dev_run=True)
    trainer.finetune(model, train_dl, strategy="freeze_unfreeze")


@pytest.mark.skipif(not _IMAGE_AVAILABLE, reason="image libraries aren't installed.")
def test_non_existent_backbone():
    with pytest.raises(KeyError):
        SemanticSegmentation(2, "i am never going to implement this lol")


@pytest.mark.skipif(not _IMAGE_AVAILABLE, reason="image libraries aren't installed.")
def test_freeze():
    model = SemanticSegmentation(2)
    model.freeze()
    for p in model.backbone.parameters():
        assert p.requires_grad is False


@pytest.mark.skipif(not _IMAGE_AVAILABLE, reason="image libraries aren't installed.")
def test_unfreeze():
    model = SemanticSegmentation(2)
    model.unfreeze()
    for p in model.backbone.parameters():
        assert p.requires_grad is True


@pytest.mark.skipif(not _IMAGE_AVAILABLE, reason="image libraries aren't installed.")
def test_predict_tensor():
    img = torch.rand(1, 3, 10, 20)
    model = SemanticSegmentation(2)
    data_pipe = DataPipeline(preprocess=SemanticSegmentationPreprocess(num_classes=1))
    out = model.predict(img, data_source="tensors", data_pipeline=data_pipe)
    assert isinstance(out[0], torch.Tensor)
    assert out[0].shape == (10, 20)


@pytest.mark.skipif(not _IMAGE_AVAILABLE, reason="image libraries aren't installed.")
def test_predict_numpy():
    img = np.ones((1, 3, 10, 20))
    model = SemanticSegmentation(2)
    data_pipe = DataPipeline(preprocess=SemanticSegmentationPreprocess(num_classes=1))
    out = model.predict(img, data_source="numpy", data_pipeline=data_pipe)
    assert isinstance(out[0], torch.Tensor)
    assert out[0].shape == (10, 20)


@pytest.mark.skipif(not _IMAGE_AVAILABLE, reason="image libraries aren't installed.")
@pytest.mark.parametrize("jitter, args", [(torch.jit.script, ()), (torch.jit.trace, (torch.rand(1, 3, 32, 32), ))])
def test_jit(tmpdir, jitter, args):
    path = os.path.join(tmpdir, "test.pt")

    model = SemanticSegmentation(2)
    model.eval()

    model = jitter(model, *args)

    torch.jit.save(model, path)
    model = torch.jit.load(path)

    out = model(torch.rand(1, 3, 32, 32))
    assert isinstance(out, torch.Tensor)
    assert out.shape == torch.Size([1, 2, 32, 32])
