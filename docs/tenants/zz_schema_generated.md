# JSON Schema


## Properties


- **`id`** *(string)*: Unique ID of the addon.

- **`name`** *(string)*: Friendly name for the addon, displayed in the UI.

- **`description`** *(string)*: Short description for the addon.

- **`link`** *(string)*: Link to the addon documentation.

- **`icon`** *(string)*: Icon to be shown in UI. Should be around 200px and base64 encoded.

- **`label`** *(string)*: Kubernetes label for the addon. Needs to match: 'api.openshift.com/<addon-id>'.

- **`enabled`** *(boolean)*: Set to true to allow installation of the addon.

- **`hasExternalResources`** *(boolean)*

- **`addonOwner`** *(string)*: Team or individual responsible for this addon. Needs to match: 'some name <some-email@redhat.com>'.

- **`addonNotifications`** *(array)*

  - **Items** *(string)*

- **`quayRepo`** *(string)*: Quay repository for the addon operator. Needs to match: 'quay.io/osd-addons/<my-addon-repo>'.

- **`testHarness`** *(string)*: Quay repository for the testHarness image. Needs to match: 'quay.io/<my-repo>/<my-test-harness>:<my-tag>'.

- **`installMode`** *(string)*: OLM InstallMode for the addon operator. Must be one of: `['AllNamespaces', 'SingleNamespace', 'OwnNamespace']`.

- **`manualInstallPlanApproval`** *(boolean)*

- **`targetNamespace`** *(string)*: Namespace where the addon operator should be installed.

- **`namespaces`** *(array)*: Namespaces managed by the addon-operator. Need to include the TargetNamespace.

  - **Items** *(string)*

- **`pullSecret`** *(string)*

- **`namespaceLabels`** *(object)*: Labels to be applied on all listed namespaces.

  - **Items** *(string)*

- **`namespaceAnnotations`** *(object)*: Annotations to be applied on all listed namespaces.

  - **Items** *(string)*

- **`commonLabels`** *(object)*: Labels to be applied to all objects created in the SelectorSyncSet.

  - **Items** *(string)*

- **`commonAnnotations`** *(object)*: Annotations to be applied to all objects created in the SelectorSyncSet.

  - **Items** *(string)*

- **`monitoring`** *(object)*: Configuration parameters to be injected in the ServiceMonitor used for federation. The target prometheus server found by matchLabels needs to serve service-ca signed TLS traffic (https://docs.openshift.com/container-platform/4.6/security/certificate_types_descriptions/service-ca-certificates.html), and it needs to be runing inside the monitoring.namespace, with the service name 'prometheus'. Cannot contain additional properties.

  - **`namespace`** *(string)*: Namespace where the prometheus server is running.

  - **`matchNames`** *(array)*: List of series names to federate from the prometheus server.

    - **Items** *(string)*

  - **`matchLabels`** *(object)*: List of labels used to discover the prometheus server(s) to be federated.

    - **Items** *(string)*

- **`defaultChannel`** *(string)*: OLM channel from which to install the addon-operator. Must be one of: `['alpha', 'beta', 'stable', 'edge', 'rc']`.

- **`ocmQuotaName`** *(string)*: Refers to the SKU name for the addon.

- **`ocmQuotaCost`** *(integer)*: Minimum: `0`.

- **`operatorName`** *(string)*: Name of the addon operator.

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

- **`addonImageSetVersion`** *(string)*: A string which specifies the imageset to use. Can either be 'latest' or a version string).

- **`pagerduty`** *(object)*: Cannot contain additional properties.

  - **`escalationPolicy`** *(string)*

  - **`acknowledgeTimeout`** *(integer)*: Minimum: `0`.

  - **`resolveTimeout`** *(integer)*: Minimum: `0`.

  - **`secretName`** *(string)*

  - **`secretNamespace`** *(string)*

- **`extraResources`** *(array)*: Extra Resources to be applied to the Hive cluster.

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

      - **`nodes.compute_machine_type.id`** *(['array', 'string'])*

      - **`version.raw_id`** *(string)*

      - **`instance_type`** *(['array', 'string'])*

      - **`replicas`** *(integer)*

    - **`enabled`** *(boolean)*

- **`subOperators`** *(array)*

  - **Items** *(object)*: Cannot contain additional properties.

    - **`operator_name`** *(string)*

    - **`operator_namespace`** *(string)*

    - **`enabled`** *(boolean)*

- **`config`** *(object)*: Configs to be passed to the subscription OLM object. Cannot contain additional properties.

  - **`env`** *(array)*: Array of environment variables (name, value pair) to be created as part of the subscription object.

    - **Items** *(object)*: Cannot contain additional properties.

      - **`name`** *(string)*

      - **`value`** *(string)*
