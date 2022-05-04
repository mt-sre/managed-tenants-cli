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
