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

from .meamed import MeaMed


def test_meamed_num_fit_clients_20_available() -> None:
    """Test num_fit_clients function."""
    # Prepare
    strategy = MeaMed()
    expected = 20

    # Execute
    actual, _ = strategy.num_fit_clients(num_available_clients=20)

    # Assert
    assert expected == actual


def test_meamed_num_fit_clients_19_available() -> None:
    """Test num_fit_clients function."""
    # Prepare
    strategy = MeaMed()
    expected = 19

    # Execute
    actual, _ = strategy.num_fit_clients(num_available_clients=19)

    # Assert
    assert expected == actual


def test_meamed_num_fit_clients_10_available() -> None:
    """Test num_fit_clients function."""
    # Prepare
    strategy = MeaMed()
    expected = 10

    # Execute
    actual, _ = strategy.num_fit_clients(num_available_clients=10)

    # Assert
    assert expected == actual


def test_meamed_num_fit_clients_minimum() -> None:
    """Test num_fit_clients function."""
    # Prepare
    strategy = MeaMed()
    expected = 9

    # Execute
    actual, _ = strategy.num_fit_clients(num_available_clients=9)

    # Assert
    assert expected == actual


def test_meamed_num_evaluation_clients_40_available() -> None:
    """Test num_evaluation_clients function."""
    # Prepare
    strategy = MeaMed(fraction_evaluate=0.05)
    expected = 2

    # Execute
    actual, _ = strategy.num_evaluation_clients(num_available_clients=40)

    # Assert
    assert expected == actual


def test_meamed_num_evaluation_clients_39_available() -> None:
    """Test num_evaluation_clients function."""
    # Prepare
    strategy = MeaMed(fraction_evaluate=0.05)
    expected = 2

    # Execute
    actual, _ = strategy.num_evaluation_clients(num_available_clients=39)

    # Assert
    assert expected == actual


def test_meamed_num_evaluation_clients_20_available() -> None:
    """Test num_evaluation_clients function."""
    # Prepare
    strategy = MeaMed(fraction_evaluate=0.05)
    expected = 2

    # Execute
    actual, _ = strategy.num_evaluation_clients(num_available_clients=20)

    # Assert
    assert expected == actual


def test_meamed_num_evaluation_clients_minimum() -> None:
    """Test num_evaluation_clients function."""
    # Prepare
    strategy = MeaMed(fraction_evaluate=0.05)
    expected = 2

    # Execute
    actual, _ = strategy.num_evaluation_clients(num_available_clients=19)

    # Assert
    assert expected == actual


def test_aggregate_fit() -> None:
    """Tests if MeaMed is aggregating correctly."""
    # Prepare
    previous_weights: NDArrays = [array([0.1, 0.1, 0.1, 0.1], dtype=float32)]
    strategy = MeaMed(
        initial_parameters=ndarrays_to_parameters(previous_weights),
        num_clients_to_exclude=1,
    )
    param_0: Parameters = ndarrays_to_parameters(
        [array([0.2, 0.2, 0.2, 0.2], dtype=float32)]
    )
    param_1: Parameters = ndarrays_to_parameters(
        [array([1.0, 1.0, 1.0, 1.0], dtype=float32)]
    )
    param_2: Parameters = ndarrays_to_parameters(
        [array([0.5, 0.5, 0.5, 0.5], dtype=float32)]
    )
    bridge = MagicMock()
    client_0 = GrpcClientProxy(cid="0", bridge=bridge)
    client_1 = GrpcClientProxy(cid="1", bridge=bridge)
    client_2 = GrpcClientProxy(cid="2", bridge=bridge)
    results: List[Tuple[ClientProxy, FitRes]] = [
        (
            client_0,
            FitRes(
                status=Status(code=Code.OK, message="Success"),
                parameters=param_0,
                num_examples=1,
                metrics={},
            ),
        ),
        (
            client_1,
            FitRes(
                status=Status(code=Code.OK, message="Success"),
                parameters=param_1,
                num_examples=1,
                metrics={},
            ),
        ),
        (
            client_2,
            FitRes(
                status=Status(code=Code.OK, message="Success"),
                parameters=param_2,
                num_examples=1,
                metrics={},
            ),
        ),
    ]
    expected: NDArrays = [array([0.35, 0.35, 0.35, 0.35], dtype=float32)]

    # Execute
    actual_aggregated, _ = strategy.aggregate_fit(
        server_round=1, results=results, failures=[]
    )
    if actual_aggregated:
        actual_list = parameters_to_ndarrays(actual_aggregated)
        actual = actual_list[0]

    assert (actual == expected[0]).all()