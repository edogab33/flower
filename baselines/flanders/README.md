---
title: A Byzantine-Resilient Aggregation Scheme for Federated Learning via Matrix Autoregression on Client Updates
url: https://arxiv.org/abs/2303.16668
labels: [robustness, model poisoning, anomaly detection, autoregressive model, regression, classification]
dataset: [MNIST, Income, CIFAR-10, California Housing]
---

**Paper:** [arxiv.org/abs/2303.16668](https://arxiv.org/abs/2303.16668)

**Authors:** Gabriele Tolomei, Edoardo Gabrielli, Dimitri Belli, Vittorio Miori

**Abstract:** In this work, we propose FLANDERS, a novel federated learning (FL) aggregation scheme robust to Byzantine attacks. FLANDERS considers the local model updates sent by clients at each FL round as a matrix-valued time series. Then, it identifies malicious clients as outliers of this time series by comparing actual observations with those estimated by a matrix autoregressive forecasting model. Experiments conducted on several datasets under different FL settings demonstrate that FLANDERS matches the robustness of the most powerful baselines against Byzantine clients. Furthermore, FLANDERS remains highly effective even under extremely severe attack scenarios, as opposed to existing defense strategies. 


## About this baseline

**What’s implemented:** The code in this directory replicates the results on MNIST and Income datasets under all attack settings (Gaussian, LIE, OPT and AGR-MM), but I've also implemented the code for California Housing and CIFAR-10. More specifically, you can reproduce part of Fig. 3 (a) and (b), and part of Fig. 4 and Fig. 5 in Appendix G.2 (there's no division between $b\lt50%$, and $b\ge50%$.). Since here I do not compare FLANDERS with other defence baselines, all attacks are grouped into the same plot.

**Datasets:** MNIST, Income

**Hardware Setup:** Apple M2 Pro, 16gb RAM

**Estimated time to run:** For **Income**, 117 seconds. For **MNIST**, 24 minutes. This is the time estimated for a *single experiment* (i.e. 50 rounds, 10 clients sampled each round, 1 local epoch).

**Contributors:** Edoardo Gabrielli, University of Rome "La Sapienza" ([GitHub](https://github.com/edogab33), [LinkedIn](https://www.linkedin.com/in/edoardog/), [Scholar](https://scholar.google.com/citations?user=b3bePdYAAAAJ))


## Experimental Setup

**Task:** Image classification, logistic regression, linear regression

**Models:** Appendix C of the paper describes the models, but here's a summary.

Income (binary classification):
- cyclic coordinate descent (CCD)
- L1-regularized binary cross-entropy loss (LASSO)

MNIST (multilabel classification, fully connected, feed forward NN):
- Multilevel Perceptron (MLP)
- minimizing multiclass cross-entropy loss using Adam optimizer
- input: 784
- hidden layer 1: 128
- hidden layer 2: 256


**Dataset:** Every dataset is partitioned into two disjoint sets: 80% for training and 20% for testing. The training set is distributed uniformly across all clients (100), while the testing set is held by the server to evaluate the global model.

| Description | Default Value |
| ----------- | ----- |
| Partitions | 100 |
| Evaluation | centralized |
| Training set | 80% |
| Testing set | 20% |

**Training Hyperparameters:**

| Dataset | # of clients  | Clients per round | # of rounds | $L$ | Batch size | Learning rate | $\lambda_1$ | $\lambda_2$ | Optimizer | Dropout | Alpha | Beta | # of clients to keep | Sampling |
| -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- |
| Income | 10 | 100 | 50 | 30 | \ | \ | 1.0 | 0.0 | CCD | \ | 0.0 | 0.0 | 1 | \ |
| MNIST | 10 | 100 | 50 | 30 | 32 | $10^{-3}$ | \ | \ | Adam | 0.2 | 0.0 | 0.0 | 1 | \ |

Where $\lambda_1$ and $\lambda_2$ are Lasso and Ridge regularization terms, $L$ is the number of warmup rounds (rounds without any attack) and the number of malicious clients ranges from 0 to 9.


## Environment Setup

```bash  
# Use a version of Python >=3.9 and <3.12.0.
pyenv local 3.10.12
poetry env use 3.10.12

# Install everything from the toml
poetry install

# Activate the env
poetry shell
```


## Running the Experiments
Ensure that the environment is properly set up, then run:

```bash  
python -m flanders.main
```

To execute a single experiment with the default values in `conf/base.yaml`.

To run custom experiments, you can override the default values like that:

```bash
python -m flanders.main dataset=income server.attack_fn=lie server.num_malicious=1
```

Finally, to run multiple custom experiments:

```bash
python -m flanders.main --multirun dataset=income,mnist,house,cifar server.attack_fn=gaussian,lie,fang,minmax server.num_malicious=0,1,2,3,4,5
```


## Expected Results

By running;
```bash
python -m flanders.main --multirun dataset=income,mnist server.attack_fn=gaussian,lie,fang,minmax server.num_malicious=0,1,2,3,4,5,6,7,8,9
```

It will generate the results in `results/all_results.csv`. To generate the plots, use the notebook in `plotting/plots.ipynb`.

Expected maximum accuracy achieved across different numbers of malicious clients and different attacks:

![](_static/max_acc.jpg)

Expected distribution of accuracy from round $L$ to the final round across all the experiments:

![](_static/boxplot_Income.jpg)

![](_static/boxplot_MNIST.jpg)