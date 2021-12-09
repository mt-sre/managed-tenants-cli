# JSON Schema


## Properties


- **`name`** *(string)*: The name of the imageset along with the version.

- **`indexImage`** *(string)*: The url for the index image.

- **`relatedImages`** *(array)*: A list of image urls of related operators.

  - **Items** *(string)*

- **`addOnParameters`** *(object)*: List of Addon Parameters. Cannot contain additional properties.

  - **`items`** *(array)*

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

            - **`cloud_provider.id`** *(array)*

              - **Items** *(string)*

            - **`product.id`** *(array)*

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

      - **`cloud_provider.id`** *(array)*

        - **Items** *(string)*

      - **`product.id`** *(array)*

        - **Items** *(string)*

      - **`compute.memory`** *(integer)*

      - **`compute.cpu`** *(integer)*

      - **`ccs.enabled`** *(boolean)*

      - **`nodes.compute`** *(integer)*

      - **`nodes.compute_machine_type.id`** *(array)*

      - **`version.raw_id`** *(string)*

      - **`instance_type`** *(array)*

      - **`replicas`** *(integer)*

    - **`enabled`** *(boolean)*

- **`subOperators`** *(array)*: Representation of an add-on sub operator. A sub operator is an operator who's life cycle is controlled by the add-on umbrella operator.

  - **Items** *(object)*: Cannot contain additional properties.

    - **`operator_name`** *(string)*: Name of the add-on sub operator.

    - **`operator_namespace`** *(string)*: Namespace of the add-on sub operator.

    - **`enabled`** *(boolean)*: Indicates if the sub operator is enabled for the add-on.

- **`subscriptionConfig`** *(object)*: Configs to be passed to the subscription OLM object. Cannot contain additional properties.

  - **`env`** *(array)*: Array of environment variables (name, value pair) to be created as part of the subscription object.

    - **Items** *(object)*: Cannot contain additional properties.

      - **`name`** *(string)*

      - **`value`** *(string)*
