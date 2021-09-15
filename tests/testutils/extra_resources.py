DEADMANSSNITCH = """
apiVersion: deadmanssnitch.managed.openshift.io/v1alpha1
kind: DeadmansSnitchIntegration
metadata:
  name: mtsre-dms-test
  namespace: deadmanssnitch-operator
spec:
  clusterDeploymentSelector:
    matchExpressions:
    - key: {{ADDON.metadata['label']}}
      operator: In
      values:
      - "true"
    - key: {{ADDON.metadata['label']}}-delete
      operator: NotIn
      values:
      - 'true'
  dmsAPIKeySecretRef:
    name: deadmanssnitch-api-key
    namespace: deadmanssnitch-operator
  snitchNamePostFix: mtsre-testing
  tags: ["mtsre-testing"]
  targetSecretRef:
    name: redhat-mtsre-testing-deadmanssnitch
    namespace: {{ADDON.metadata['targetNamespace']}}
"""

PAGERDUTYINTEGRATION = """
apiVersion: pagerduty.openshift.io/v1alpha1
kind: PagerDutyIntegration
metadata:
  name: mtsre-pdi-test
  namespace: pagerduty-operator
spec:
  acknowledgeTimeout: 0
  resolveTimeout: 0
  escalationPolicy: PDGB0P2
  servicePrefix: mtsre-pdi
  pagerdutyApiKeySecretRef:
    name: pagerduty-api-key
    namespace: pagerduty-operator
  clusterDeploymentSelector:
    matchLabels:
      api.openshift.com/addon-mtsre-pdi: "true"
  targetSecretRef:
    name: mtsre-pdi-test
    namespace: mtsre-pdi-test
"""
