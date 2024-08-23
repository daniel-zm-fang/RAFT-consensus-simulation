# RAFT Consensus Algorithm Simulation

This project implements a simplified simulation of the RAFT consensus algorithm, demonstrating leader election and basic log replication in a distributed system.

## Project Overview

The simulation has two components:

1. `Node`: represents a server in the RAFT cluster.
2. `Cluster`: represents a collection of `Node`s and facilitates communication between them.

## Dependencies

None, it doesn't use any libraries outside of Python 3.

## Running the Simulation

```bash
python3 simulation.py
```

The simulation will run for 10 seconds by default. You can also change the number of nodes in the cluster (default is 5).
