# JSON Schema


*Addon imageset schema for the files found under the addonimagesets/ dir.*


## Properties


- **`name`** *(string)*: The name of the imageset along with the version.

- **`indexImage`** *(string)*: The url for the index image.

- **`relatedImages`** *(array)*: A list of image urls of related operators.

  - **Items** *(string)*

- **`addOnParameters`**: List of parameters for the addon. Refer to *shared/addon_parameters.json*.

- **`addOnRequirements`**: List of requirements for the addon. Refer to *shared/addon_requirements.json*.

- **`subOperators`**: Sub operator under the umbrella of add-on operator. Refer to *shared/sub_operators.json*.

- **`subscriptionConfig`**: Subscription config of the addons for the OLM object. Refer to *shared/subscription_config.json*.

- **`pullSecretName`** *(string)*: Name of the secret under `secrets` which is supposed to be used for pulling Catalog Image under CatalogSource.

- **`additionalCatalogSources`** *(array)*: List of additional catalog sources to be created.

  - **Items** *(object)*: Cannot contain additional properties.

    - **`name`** *(string)*: Name of the additional catalog source.

    - **`image`** *(string)*: Url of the additional catalog source image.
