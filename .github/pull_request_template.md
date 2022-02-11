# py-mtcli

## Description

Short description of the change:

- modified X
- modified Y
- modified Z

## Checklist

**For any modification to `managedtenants/bundles/`**

- [ ] `$ managedtenants --addons-dir=../managed-tenants-bundles/addons --dry-run bundles` (successfuly built all addons)
- [ ] `$ managedtenants -addons-dir=../managed-tenants-bundles/addons --addon-name=<addon> bundles --quay-org <personal_org>` (successfuly built and push a single addon)
