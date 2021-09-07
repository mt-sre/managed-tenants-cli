# JSON Schema


## Properties


- **`id`** *(string)*

- **`name`** *(string)*

- **`description`** *(string)*

- **`link`** *(string)*

- **`icon`** *(string)*

- **`label`** *(string)*

- **`enabled`** *(boolean)*

- **`hasExternalResources`** *(boolean)*

- **`addonOwner`** *(string)*

- **`addonNotifications`** *(array)*

  - **Items** *(string)*

- **`quayRepo`** *(string)*

- **`testHarness`** *(string)*

- **`installMode`** *(string)*: Must be one of: `['AllNamespaces', 'SingleNamespace', 'OwnNamespace']`.

- **`manualInstallPlanApproval`** *(boolean)*

- **`targetNamespace`** *(string)*

- **`namespaces`** *(array)*

  - **Items** *(string)*

- **`pullSecret`** *(string)*

- **`namespaceLabels`** *(object)*

  - **Items** *(string)*

- **`namespaceAnnotations`** *(object)*

  - **Items** *(string)*

- **`commonLabels`** *(object)*

  - **Items** *(string)*

- **`commonAnnotations`** *(object)*

  - **Items** *(string)*

- **`defaultChannel`** *(string)*: Must be one of: `['alpha', 'beta', 'stable', 'edge', 'rc']`.

- **`ocmQuotaName`** *(string)*

- **`ocmQuotaCost`** *(integer)*: Minimum: `0`.

- **`operatorName`** *(string)*

- **`bundleParameters`** *(object)*: Cannot contain additional properties.

  - **`useClusterStorage`** *(string)*

  - **`alertingEmailAddress`** *(string)*

  - **`buAlertingEmailAddress`** *(string)*

  - **`alertSMTPFrom`** *(string)*

  - **`addonParamsSecretName`** *(string)*

- **`channels`** *(array)*

  - **Items** *(object)*: Cannot contain additional properties.

    - **`name`** *(string)*

    - **`currentCSV`** *(string)*

- **`startingCSV`** *(string)*

- **`indexImage`** *(string)*

- **`pagerduty`** *(object)*: Cannot contain additional properties.

  - **`escalationPolicy`** *(string)*

  - **`acknowledgeTimeout`** *(integer)*: Minimum: `0`.

  - **`resolveTimeout`** *(integer)*: Minimum: `0`.

  - **`secretName`** *(string)*

  - **`secretNamespace`** *(string)*

- **`extraResources`** *(array)*

  - **Items** *(string)*

- **`addOnParameters`** *(array)*

  - **Items** *(object)*: Cannot contain additional properties.

    - **`id`** *(string)*

    - **`name`** *(string)*

    - **`description`** *(string)*

    - **`value_type`** *(string)*: Must be one of: `['string', 'number', 'boolean', 'cidr', 'resource']`.

    - **`validation`** *(string)*

    - **`required`** *(boolean)*

    - **`editable`** *(boolean)*

    - **`enabled`** *(boolean)*

    - **`default_value`** *(string)*

    - **`options`** *(array)*

      - **Items** *(object)*: Cannot contain additional properties.

        - **`name`** *(string)*

        - **`value`** *(string)*

    - **`conditions`** *(array)*

      - **Items** *(object)*: Cannot contain additional properties.

        - **`resource`** *(string)*: Must be one of: `['cluster']`.

        - **`data`** *(object)*: Cannot contain additional properties.

          - **`aws.sts.enabled`** *(boolean)*

          - **`ccs.enabled`** *(boolean)*

          - **`cloud_provider.id`** *(['array', 'string'])*

            - **Items** *(string)*

          - **`product.id`** *(['array', 'string'])*

            - **Items** *(string)*

          - **`version.raw_id`** *(string)*

- **`addOnRequirements`** *(array)*

  - **Items** *(object)*: Cannot contain additional properties.

    - **`id`** *(string)*

    - **`resource`** *(string)*: Must be one of: `['cluster', 'addon', 'machine_pool']`.

    - **`data`** *(object)*: Cannot contain additional properties.

      - **`id`** *(string)*

      - **`state`** *(string)*

      - **`aws.sts.enabled`** *(boolean)*

      - **`cloud_provider.id`** *(['array', 'string'])*

        - **Items** *(string)*

      - **`product.id`** *(['array', 'string'])*

        - **Items** *(string)*

      - **`compute.memory`** *(integer)*

      - **`compute.cpu`** *(integer)*

      - **`ccs.enabled`** *(boolean)*

      - **`nodes.compute`** *(integer)*

      - **`nodes.compute_machine_type.id`** *(string)*

      - **`version.raw_id`** *(string)*

      - **`instance_type`** *(string)*

      - **`replicas`** *(integer)*

    - **`enabled`** *(boolean)*

- **`subOperators`** *(array)*

  - **Items** *(object)*: Cannot contain additional properties.

    - **`operator_name`** *(string)*

    - **`operator_namespace`** *(string)*

    - **`enabled`** *(boolean)*
