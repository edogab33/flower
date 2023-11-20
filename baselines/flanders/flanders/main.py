"""Create and connect the building blocks for your experiments; start the simulation.

It includes processioning the dataset, instantiate strategy, specify how the global
model is going to be evaluated, etc. At the end, this script saves the results.
"""
# these are the basic packages you'll need here
# feel free to remove some if aren't needed
import hydra
from hydra.utils import instantiate
from omegaconf import DictConfig, OmegaConf


import argparse
import shutil
import numpy as np
import flwr as fl
from flwr.common.typing import Scalar
import torch
import os
import random
import pandas as pd

from typing import Dict, Callable, Optional, Tuple, List
from neural_networks.dataset_utils import (
    get_mnist, 
    do_fl_partitioning, 
    get_dataloader, 
    get_circles, 
    get_cifar_10, 
    get_partitioned_house, 
    get_partitioned_income
)
from neural_networks.neural_networks import (
    MnistNet, 
    ToyNN, 
    roc_auc_multiclass, 
    test_toy, 
    train_mnist, 
    test_mnist, 
    train_toy
)
from clients import (
    CifarClient, 
    HouseClient, 
    IncomeClient, 
    ToyClient, 
    set_params, 
    get_params, 
    MnistClient, 
    set_sklearn_model_params, 
    get_sklearn_model_params
)
from neural_networks.neural_networks import CifarNet, test_cifar
from strategy.utilities import save_results

from torch.utils.data import DataLoader
from torchvision import transforms
from torchvision.datasets import MNIST

from strategy.flanders import Flanders


from attacks import (
    fang_attack, 
    gaussian_attack, 
    lie_attack, 
    no_attack, 
    minmax_attack
)

from flwr.server.strategy.fedavg import FedAvg
from flwr.common import (
    ndarrays_to_parameters,
    parameters_to_ndarrays,
)

from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.metrics import accuracy_score, log_loss, roc_auc_score, mean_squared_error, mean_absolute_percentage_error, r2_score


@hydra.main(config_path="conf", config_name="base", version_base=None)
def main(cfg: DictConfig) -> None:
    """Run the baseline.

    Parameters
    ----------
    cfg : DictConfig
        An omegaconf object that stores the hydra config.
    """
    # 1. Print parsed config
    print(OmegaConf.to_yaml(cfg))

    print(cfg.dataset)

    evaluate_fn = mnist_evaluate

    # 2. Prepare your dataset
    # here you should call a function in datasets.py that returns whatever is needed to:
    # (1) ensure the server can access the dataset used to evaluate your model after
    # aggregation
    # (2) tell each client what dataset partitions they should use (e.g. a this could
    # be a location in the file system, a list of dataloader, a list of ids to extract
    # from a dataset, it's up to you)

    # 3. Define your clients
    # Define a function that returns another function that will be used during
    # simulation to instantiate each individual client
    # client_fn = client.<my_function_that_returns_a_function>()
    client = MnistClient
    def client_fn(cid: int, pool_size: int):
        return client(cid, pool_size)

    # 4. Define your strategy
    # pass all relevant argument (including the global dataset used after aggregation,
    # if needed by your method.)
    # strategy = instantiate(cfg.strategy, <additional arguments if desired>)
    strategy = instantiate(cfg.strategy)


    # 5. Start Simulation
    # history = fl.simulation.start_simulation(<arguments for simulation>)
    fl.simulation.start_simulation(
        client_fn=client_fn,
        num_clients=cfg.pool_size,
        config=fl.server.ServerConfig(num_rounds=cfg.num_rounds),
        strategy=strategy
    )

    # 6. Save your results
    # Here you can save the `history` returned by the simulation and include
    # also other buffers, statistics, info needed to be saved in order to later
    # on generate the plots you provide in the README.md. You can for instance
    # access elements that belong to the strategy for example:
    # data = strategy.get_my_custom_data() -- assuming you have such method defined.
    # Hydra will generate for you a directory each time you run the code. You
    # can retrieve the path to that directory with this:
    # save_path = HydraConfig.get().runtime.output_dir

def mnist_evaluate(
    server_round: int, parameters: fl.common.NDArrays, config: Dict[str, Scalar]
):
    # determine device
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    model = MnistNet()
    set_params(model, parameters)
    model.to(device)

    testset = MNIST("", train=False, download=True, transform=transforms.ToTensor())
    testloader = DataLoader(testset, batch_size=32, shuffle=False, num_workers=1)
    loss, accuracy, auc = test_mnist(model, testloader, device=device)

    config["id"] = args.exp_num
    config["round"] = server_round
    config["auc"] = auc
    save_results(loss, accuracy, config=config)

    # return statistics
    return loss, {"accuracy": accuracy, "auc": auc}

main()