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
import urllib.error

import pytest
from pytorch_lightning.utilities import _BOLTS_AVAILABLE, _TORCHVISION_AVAILABLE

from flash.core.utilities.imports import _TIMM_AVAILABLE
from flash.image.backbones import catch_url_error, IMAGE_CLASSIFIER_BACKBONES


@pytest.mark.parametrize(["backbone", "expected_num_features"], [
    pytest.param("resnet34", 512, marks=pytest.mark.skipif(not _TORCHVISION_AVAILABLE, reason="No torchvision")),
    pytest.param("mobilenetv2_100", 1280, marks=pytest.mark.skipif(not _TIMM_AVAILABLE, reason="No timm")),
    pytest.param("simclr-imagenet", 2048, marks=pytest.mark.skipif(not _BOLTS_AVAILABLE, reason="No bolts")),
    pytest.param("swav-imagenet", 2048, marks=pytest.mark.skipif(not _BOLTS_AVAILABLE, reason="No bolts")),
    pytest.param("mobilenet_v2", 1280, marks=pytest.mark.skipif(not _TORCHVISION_AVAILABLE, reason="No torchvision")),
])
def test_image_classifier_backbones_registry(backbone, expected_num_features):
    backbone_fn = IMAGE_CLASSIFIER_BACKBONES.get(backbone)
    backbone_model, num_features = backbone_fn(pretrained=False)
    assert backbone_model
    assert num_features == expected_num_features


def test_pretrained_backbones_catch_url_error():

    def raise_error_if_pretrained(pretrained=False):
        if pretrained:
            raise urllib.error.URLError('Test error')

    with pytest.warns(UserWarning, match="Failed to download pretrained weights"):
        catch_url_error(raise_error_if_pretrained)(pretrained=True)
