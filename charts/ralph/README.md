
# ralph

## Installation

1. Edit `values.yaml` as desired.

1. Install the chart on the cluster.
  ```console
  $ helm helm dependency update  
  $ helm package .
  $ helm install -n [NAMESPACE] [RELEASE_NAME] ralph-*.tgz
  ```
1. Follow the [Installation guide](https://ralph-ng.readthedocs.io/en/stable/installation/installation/) to complete your installation.

  ```console
  $ kubectl exec -it -n [NAMESPACE] [RALPH-POD-NAME] -- /bin/bash
  ```

## LDAP Authentication

1. Follow the [Configuration guide](https://ralph-ng.readthedocs.io/en/stable/installation/configuration/#ldap-authentication).

1. Create a configmap with the proper configuration in the same namespace.

1. Edit `useCustomProdPy` in the values file.
