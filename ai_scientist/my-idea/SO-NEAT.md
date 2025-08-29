# Title: self-organizing NeuroEvolution of Augmenting Topologies (NEAT)

## Keywords
NeuroEvolution, NEAT, Genetic Algorithms, Evolutionary Computation, Neural Networks, Self-Organization, Plasticity, Topology Optimization

## TL;DR
Self-organization and plasticity can be powerful tools to improve NeuroEvolution algorithms like NEAT. It is worth exploring how these concepts can be integrated into NEAT to create more adaptive and efficient neural networks.


## Abstract
The goal of self-organizing NEAT is to enhance the traditional NEAT algorithm by incorporating principles of self-organization and plasticity. The traditional NEAT algorithm just randomly mutates and crosses over neural network topologies, which can lead to suboptimal solutions and slow convergence. A good idea is **SO-NEAT** (Self-Organizing NEAT), which augments NEAT with (i) within-lifetime synaptic plasticity governed by local rules and neuromodulators, (ii) structural self-organization via homeostatic activity targets, utility-driven node/synapse birth–death, and wiring-length minimization, and (iii) multi-objective selection that balances task fitness with parsimony, modularity, and stability. SON-NEAT keeps NEAT’s strengths—speciation, historical markings, incremental topology growth—while adding fast adaptation and topological priors that encourage sparse, modular computation. We hypothesize SON-NEAT will (1) learn with fewer evaluations, (2) generalize better under distribution shift, and (3) adapt online to task changes without catastrophic interference.

## Benchmarks
- XOR,
- Circles,
- Moons,
- Spiral