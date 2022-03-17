resource "kubectl_manifest" "cloudflare_prod" {

    depends_on = [time_sleep.wait_for_certmanager]

    yaml_body = <<YAML
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: cloudflare-prod
spec:
  acme:
    email: your-mail-address
    server: https://acme-v02.api.letsencrypt.org/directory
    privateKeySecretRef:
      name: cloudflare-prod-account-key
    solvers:
    - dns01:
        cloudflare:
          email: your-mail-address
          apiKeySecretRef:
            name: cloudflare-api-key-secret
            key: api-key
    YAML
}

resource "time_sleep" "wait_for_clusterissuer" {

    depends_on = [kubectl_manifest.cloudflare_prod]

    create_duration = "30s"
}
