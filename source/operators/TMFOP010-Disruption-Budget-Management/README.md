# TMFOP010 Disruption Budget Management Operators

Protects ODA Component availability during planned maintenance, upgrades, and cluster operations by automatically enforcing minimum availability guarantees. It ensures that business-critical services remain operational even as the underlying infrastructure is updated or rebalanced, applying the appropriate level of protection based on each component's business importance.

At present, there is one implementation:

* [PDB Management](./pdb-management/): Kubernetes operator for Pod Disruption Budget management.
