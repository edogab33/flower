# Copyright 2021 Adap GmbH. All Rights Reserved.
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
# ==============================================================================

# pylint: disable=invalid-name

from torch.utils.data import DataLoader, Dataset
from numpy import array, asarray, concatenate, int64
from flwr_experimental.baseline.dataset.dataset import XY


def convert_pytorch_dataset_to_xy(dataset: Dataset) -> XY:
    """Converts standard Pytorch datasets into XY.

    Args:
        dataset (torch.utils.data.Dataset): Original Pytorch dataset.
            Must contain the desired transformations such as ToTensor and Normalize.

    Returns:
        XY: Dataset in the usual Tuple[ndarray, ndarray] format.
    """
    samples = []
    target = []
    for img, label in dataset:
        samples.append([array(img)])
        target.append(label)

    return concatenate(samples), asarray(target, dtype=int64)
