resource "kubernetes_namespace" "certmanager" {

    metadata {
        name = "certmanager"
    }
}

resource "helm_release" "certmanager" {
    
    depends_on = [kubernetes_namespace.certmanager]

    name = "certmanager"
    namespace = "certmanager"

    repository = "https://charts.jetstack.io"
    chart      = "cert-manager"

    # Install Kubernetes CRDs
    set {
        name  = "installCRDs"
        value = "true"
    }
}

# (Optional) Create a Time-Sleep for Certificates and Issuer Manifests to deploy later
# resource "time_sleep" "wait_for_certmanager" {
# 
#     depends_on = [helm_release.certmanager]
# 
#     create_duration = "10s"
# }
