# JSON Schema


*managed-tenants-bundles configuration schema for the 'config.yaml' file.*


## Properties


- **`environments`** *(array)*: List of all environments in managed-tenants to be upgraded by automated MRs. Production has to be upgraded manually.

  - **Items** *(string)*: Must be one of: `['integration', 'stage']`.

- **`ocm`** *(object)*: Required OCM data for valid imagesets to be constructed by automated MRs to managed-tenants. Cannot contain additional properties.

  - **`addOnParameters`**: Refer to *shared/addon_parameters.yaml*.

  - **`addOnRequirements`**: Refer to *shared/addon_requirements.yaml*.

  - **`subOperators`**: Refer to *shared/sub_operators.yaml*.

  - **`subscriptionConfig`**: Refer to *shared/subscription_config.json*.
