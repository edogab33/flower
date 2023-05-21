# Copyright 2020 Adap GmbH. All Rights Reserved.
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
"""Bulyan tests."""


from typing import List, Tuple
from unittest.mock import MagicMock

from numpy import array, float32

from flwr.common import (
    Code,
    FitRes,
    NDArrays,
    Parameters,
    Status,
    ndarrays_to_parameters,
    parameters_to_ndarrays,
)
from flwr.server.client_proxy import ClientProxy
from flwr.server.fleet.grpc_bidi.grpc_client_proxy import GrpcClientProxy

from .bulyan import Bulyan


def test_krum_num_fit_clients_20_available() -> None:
    """Test num_fit_clients function."""
    # Prepare
    strategy = Bulyan()
    expected = 20

    # Execute
    actual, _ = strategy.num_fit_clients(num_available_clients=20)

    # Assert
    assert expected == actual


def test_krum_num_fit_clients_19_available() -> None:
    """Test num_fit_clients function."""
    # Prepare
    strategy = Bulyan()
    expected = 19

    # Execute
    actual, _ = strategy.num_fit_clients(num_available_clients=19)

    # Assert
    assert expected == actual


def test_krum_num_fit_clients_10_available() -> None:
    """Test num_fit_clients function."""
    # Prepare
    strategy = Bulyan()
    expected = 10

    # Execute
    actual, _ = strategy.num_fit_clients(num_available_clients=10)

    # Assert
    assert expected == actual


def test_krum_num_fit_clients_minimum() -> None:
    """Test num_fit_clients function."""
    # Prepare
    strategy = Bulyan()
    expected = 9

    # Execute
    actual, _ = strategy.num_fit_clients(num_available_clients=9)

    # Assert
    assert expected == actual


def test_krum_num_evaluation_clients_40_available() -> None:
    """Test num_evaluation_clients function."""
    # Prepare
    strategy = Bulyan(fraction_evaluate=0.05)
    expected = 2

    # Execute
    actual, _ = strategy.num_evaluation_clients(num_available_clients=40)

    # Assert
    assert expected == actual


def test_krum_num_evaluation_clients_39_available() -> None:
    """Test num_evaluation_clients function."""
    # Prepare
    strategy = Bulyan(fraction_evaluate=0.05)
    expected = 2

    # Execute
    actual, _ = strategy.num_evaluation_clients(num_available_clients=39)

    # Assert
    assert expected == actual


def test_krum_num_evaluation_clients_20_available() -> None:
    """Test num_evaluation_clients function."""
    # Prepare
    strategy = Bulyan(fraction_evaluate=0.05)
    expected = 2

    # Execute
    actual, _ = strategy.num_evaluation_clients(num_available_clients=20)

    # Assert
    assert expected == actual


def test_krum_num_evaluation_clients_minimum() -> None:
    """Test num_evaluation_clients function."""
    # Prepare
    strategy = Bulyan(fraction_evaluate=0.05)
    expected = 2

    # Execute
    actual, _ = strategy.num_evaluation_clients(num_available_clients=19)

    # Assert
    assert expected == actual


def test_aggregate_fit() -> None:
    """Tests if Bulyan is aggregating correctly."""
    # Prepare
    previous_weights: NDArrays = [array([0.1, 0.1, 0.1, 0.1], dtype=float32)]
    strategy = Bulyan(
        initial_parameters=ndarrays_to_parameters(previous_weights),
        num_malicious_clients=1,
    )
    param_0: Parameters = ndarrays_to_parameters(
        [array([0.2, 0.2, 0.2, 0.2], dtype=float32)]
    )
    param_1: Parameters = ndarrays_to_parameters(
        [array([0.5, 0.5, 0.5, 0.5], dtype=float32)]
    )
    param_2: Parameters = ndarrays_to_parameters(
        [array([0.7, 0.7, 0.7, 0.7], dtype=float32)]
    )
    param_3: Parameters = ndarrays_to_parameters(
        [array([12.0, 12.0, 12.0, 12.0], dtype=float32)]
    )
    bridge = MagicMock()
    client_0 = GrpcClientProxy(cid="0", bridge=bridge)
    client_1 = GrpcClientProxy(cid="1", bridge=bridge)
    client_2 = GrpcClientProxy(cid="2", bridge=bridge)
    client_3 = GrpcClientProxy(cid="3", bridge=bridge)
    results: List[Tuple[ClientProxy, FitRes]] = [
        (
            client_0,
            FitRes(
                status=Status(code=Code.OK, message="Success"),
                parameters=param_0,
                num_examples=5,
                metrics={},
            ),
        ),
        (
            client_1,
            FitRes(
                status=Status(code=Code.OK, message="Success"),
                parameters=param_1,
                num_examples=5,
                metrics={},
            ),
        ),
        (
            client_2,
            FitRes(
                status=Status(code=Code.OK, message="Success"),
                parameters=param_2,
                num_examples=5,
                metrics={},
            ),
        ),
        (
            client_3,
            FitRes(
                status=Status(code=Code.OK, message="Success"),
                parameters=param_3,
                num_examples=5,
                metrics={},
            ),
        ),
    ]
    expected: NDArrays = [array([0.2, 0.2, 0.2, 0.2], dtype=float32)]

    # Execute
    actual_aggregated, _ = strategy.aggregate_fit(
        server_round=1, results=results, failures=[]
    )
    if actual_aggregated:
        actual_list = parameters_to_ndarrays(actual_aggregated)
        actual = actual_list[0]
    print("actual: ", actual)
    assert (actual == expected[0]).all()

test_aggregate_fit()