# JSON Schema


*Addon metadata schema for the 'addon.yaml' file.*


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

- **`installMode`** *(string)*: OLM InstallMode for the addon operator. Must be one of: `['AllNamespaces', 'OwnNamespace']`.

- **`syncsetMigration`** *(string)*: The step currently in consideration in the process of migrating the addon to SyncSet. Must be one of: `['step 1 - block installations', 'step 2 - orphan SSS objects', 'step 3 - change SSS label', 'step 4 - enable syncset', 'step 5 - migration complete', 'rollback step 1 - ocm', 'rollback step 2 - selectorsyncset', 'rollback step 3 - reset addon migration']`.

- **`manualInstallPlanApproval`** *(boolean)*

- **`targetNamespace`** *(string)*: Namespace where the addon operator should be installed.

- **`namespaces`** *(array)*: Namespaces managed by the addon-operator. Need to include the TargetNamespace.

  - **Items** *(string)*

- **`pullSecret`** *(string)*: 'pullSecret' is deprecated for now. Please use the 'secrets' and 'pullSecretName' fields instead.

- **`secrets`** *(array)*: List of secrets that are required by the addon.

  - **Items** *(object)*: Cannot contain additional properties.

    - **`name`** *(string)*: Name of the secret present in app-interface's `deploy.yaml`.

    - **`type`** *(string)*: Kubernetes's type of the secret. Ref https://kubernetes.io/docs/concepts/configuration/secret/#secret-types. Must be one of: `['Opaque', 'kubernetes.io/dockercfg', 'kubernetes.io/dockerconfigjson', 'kubernetes.io/service-account-token', 'kubernetes.io/basic-auth', 'kubernetes.io/ssh-auth', 'kubernetes.io/tls', 'bootstrap.kubernetes.io/token']`.

    - **`vaultPath`** *(string)*: Vault path of the secret.

    - **`destinationSecretName`** *(string)*: Name of the `Secret` resource that will be applied.

- **`pullSecretName`** *(string)*: Name of the secret under `secrets` which is supposed to be used for pulling Catalog Image under CatalogSource.

- **`additionalCatalogSources`** *(array)*: List of additional catalog sources to be created.

  - **Items** *(object)*: Cannot contain additional properties.

    - **`name`** *(string)*: Name of the additional catalog source.

    - **`image`** *(string)*: Url of the additional catalog source image.

- **`namespaceLabels`** *(object)*: Labels to be applied on all listed namespaces.

  - **Items** *(string)*

- **`namespaceAnnotations`** *(object)*: Annotations to be applied on all listed namespaces.

  - **Items** *(string)*

- **`commonLabels`** *(object)*: Labels to be applied to all objects created in the SelectorSyncSet.

  - **Items** *(string)*

- **`commonAnnotations`** *(object)*: Annotations to be applied to all objects created in the SelectorSyncSet.

  - **Items** *(string)*

- **`monitoring`** *(object)*: Configuration parameters to be injected in the ServiceMonitor used for federation. The target prometheus server found by matchLabels needs to serve service-ca signed TLS traffic (https://docs.openshift.com/container-platform/4.6/security/certificate_types_descriptions/service-ca-certificates.html), and it needs to be runing inside the monitoring.namespace, with the service name 'prometheus'. Cannot contain additional properties.

  - **`portName`** *(string)*: The name of the service port fronting the prometheus server. Default: `https`.

  - **`namespace`** *(string)*: Namespace where the prometheus server is running.

  - **`matchNames`** *(array)*: List of series names to federate from the prometheus server.

    - **Items** *(string)*

  - **`matchLabels`** *(object)*: List of labels used to discover the prometheus server(s) to be federated.

    - **Items** *(string)*

- **`defaultChannel`** *(string)*: OLM channel from which to install the addon-operator. Must be one of: `['alpha', 'beta', 'stable', 'edge', 'rc', 'fast', 'candidate']`.

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

- **`deadmanssnitch`** *(object)*: Denotes the Deadmans Snitch Configuration which is supposed to be setup alongside the Addon. Cannot contain additional properties.

  - **`clusterDeploymentSelector`** *(object)*: Default: check selectorsyncset.yaml.j2 - line 260.

  - **`snitchNamePostFix`** *(string)*: Default: {{ADDON.metadata['id']}}.

  - **`targetSecretRef`** *(object)*: Cannot contain additional properties.

    - **`name`** *(string)*: Default: {{ADDON.metadata['id']}}-deadmanssnitch.

    - **`namespace`** *(string)*: Default: {{ADDON.metadata['targetNamespace']}}.

  - **`tags`** *(array)*

    - **Items** *(string)*

- **`extraResources`** *(array)*: Extra Resources to be applied to the Hive cluster.

  - **Items** *(string)*

- **`credentialsRequests`**: Refer to *shared/credentials_requests.json*.

- **`addOnParameters`**: Refer to *shared/addon_parameters.json*.

- **`addOnRequirements`**: Refer to *shared/addon_requirements.json*.

- **`subOperators`**: Refer to *shared/sub_operators.json*.

- **`subscriptionConfig`**: Refer to *shared/subscription_config.json*.

- **`managedService`** *(boolean)*: Indicates if the add-on will be used as a Managed Service.
