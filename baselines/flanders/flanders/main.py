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
from flwr.server.client_manager import SimpleClientManager
import torch
import os
import random
import pandas as pd

from typing import Dict, Callable, Optional, Tuple, List

from .client import (
    CifarClient, 
    HouseClient, 
    IncomeClient, 
    set_params, 
    get_params, 
    MnistClient, 
    set_sklearn_model_params, 
    get_sklearn_model_params
)
from .attacks import (
    fang_attack,
    gaussian_attack,
    lie_attack,
    no_attack,
    minmax_attack
)
from .utils import (
    l2_norm,
    mnist_evaluate,
    cifar_evaluate,
    house_evaluate,
    income_evaluate
)
from .dataset import (
    get_partitioned_income,
    get_partitioned_house,
    get_cifar_10,
    do_fl_partitioning
)
from .server import EnhancedServer

from torch.utils.data import DataLoader
from torchvision import transforms
from torchvision.datasets import MNIST

from .strategy import Flanders

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

    print(cfg.dataset.name)
    print(cfg.server.pool_size)

    # Delete old client_params and clients_predicted_params
    if os.path.exists(cfg.server.history_dir):
        shutil.rmtree(cfg.server.history_dir)

    attacks = {
        "gaussian_attack": gaussian_attack,
        "lie_attack": lie_attack,
        "fang_attack": fang_attack,
        "minmax_attack": minmax_attack
    }

    clients = {
        "mnist": (MnistClient, mnist_evaluate),
        "cifar": (CifarClient, cifar_evaluate),
        "house": (HouseClient, house_evaluate),
        "income": (IncomeClient, income_evaluate)
    }

    evaluate_fn = clients[cfg.dataset.name][1]

    # 2. Prepare your dataset
    # here you should call a function in datasets.py that returns whatever is needed to:
    # (1) ensure the server can access the dataset used to evaluate your model after
    # aggregation
    # (2) tell each client what dataset partitions they should use (e.g. a this could
    # be a location in the file system, a list of dataloader, a list of ids to extract
    # from a dataset, it's up to you)
    if cfg.dataset.name == "cifar":
        train_path, testset = get_cifar_10()
        fed_dir = do_fl_partitioning(
            train_path, pool_size=cfg.server.pool_size, alpha=10000, num_classes=10, val_ratio=0.5, seed=1234
        )
    elif cfg.dataset.name == "income":
        X_train, X_test, y_train, y_test = get_partitioned_income("flanders/datasets_files/adult.csv", cfg.server.pool_size)
    elif cfg.dataset.name == "house":
        X_train, X_test, y_train, y_test = get_partitioned_house("flanders/datasets_files/houses_preprocessed.csv", cfg.server.pool_size)

    # 3. Define your clients
    # Define a function that returns another function that will be used during
    # simulation to instantiate each individual client
    # client_fn = client.<my_function_that_returns_a_function>()
    def client_fn(cid: str, pool_size: int = 10, dataset_name: str = cfg.dataset.name):
        client = clients[dataset_name][0]
        cid_idx = int(cid)
        if dataset_name == "cifar":
            return client(cid, fed_dir)
        elif dataset_name == "mnist":
            return client(cid, pool_size)
        elif dataset_name == "income":
            return client(cid, X_train[cid_idx], y_train[cid_idx], X_test[cid_idx], y_test[cid_idx])
        elif dataset_name == "house":
            return client(cid, X_train[cid_idx], y_train[cid_idx], X_test[cid_idx], y_test[cid_idx])
        else:
            raise ValueError("Dataset not supported")


    # 4. Define your strategy
    # pass all relevant argument (including the global dataset used after aggregation,
    # if needed by your method.)
    # strategy = instantiate(cfg.strategy, <additional arguments if desired>)
    strategy = instantiate(
        cfg.strategy,
        evaluate_fn=evaluate_fn,
        on_fit_config_fn=fit_config,
        fraction_fit=1,
        fraction_evaluate=0,
        min_fit_clients=2,
        min_evaluate_clients=0,
        warmup_rounds=2,
        to_keep=1,
        min_available_clients=2,
        window=2,
        sampling=1,
        distance_function=l2_norm
    )

    # 5. Start Simulation
    # history = fl.simulation.start_simulation(<arguments for simulation>)
    for dataset_name in cfg.dataset.name:
        for attack_fn in cfg.server.attack_fn:
            for num_malicious in cfg.server.num_malicious:
                # the experiment with num_malicious = 0 should be done only one time
                if num_malicious == 0 and attack_fn != "gaussian_attack":
                    continue
                history = fl.simulation.start_simulation(
                    client_fn=client_fn,
                    client_resources={"num_cpus": 10},
                    num_clients=cfg.server.pool_size,
                    server=EnhancedServer(
                        warmup_rounds=cfg.server.warmup_rounds,
                        num_malicious=num_malicious,
                        attack_fn=attacks[attack_fn],
                        magnitude=cfg.server.magnitude,
                        client_manager=SimpleClientManager(),
                        strategy=strategy,
                        sampling=cfg.server.sampling,
                        history_dir=cfg.server.history_dir,
                        dataset_name=dataset_name
                    ),
                    config=fl.server.ServerConfig(num_rounds=cfg.server.num_rounds),
                    strategy=strategy
                )

                print(f"history: {history}")

    # 6. Save your results
    # Here you can save the `history` returned by the simulation and include
    # also other buffers, statistics, info needed to be saved in order to later
    # on generate the plots you provide in the README.md. You can for instance
    # access elements that belong to the strategy for example:
    # data = strategy.get_my_custom_data() -- assuming you have such method defined.
    # Hydra will generate for you a directory each time you run the code. You
    # can retrieve the path to that directory with this:
    # save_path = HydraConfig.get().runtime.output_dir

def fit_config(server_round: int) -> Dict[str, Scalar]:
    """Return a configuration with static batch size and (local) epochs."""
    config = {
        "epochs": 1,  # number of local epochs
        "batch_size": 32,
    }
    return config

if __name__ == "__main__":
    main()