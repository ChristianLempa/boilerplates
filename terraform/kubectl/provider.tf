# Kubectl Provider
# ---
# Initial Provider Configuration for Kubectl

terraform {

    required_version = ">= 0.13.0"

    required_providers {
        kubectl = {
            source = "gavinbunney/kubectl"
            version = "1.13.1"
        }
    }
}

# Dynamic Configuration from CIVO Kubernetes deployment
# provider "kubectl" {
#     host = "${yamldecode(civo_kubernetes_cluster.your-kubernetes-cluster.kubeconfig).clusters.0.cluster.server}"
#     client_certificate = "${base64decode(yamldecode(civo_kubernetes_cluster.your-kubernetes-cluster.kubeconfig).users.0.user.client-certificate-data)}"
#     client_key = "${base64decode(yamldecode(civo_kubernetes_cluster.your-kubernetes-cluster.kubeconfig).users.0.user.client-key-data)}"
#     cluster_ca_certificate = "${base64decode(yamldecode(civo_kubernetes_cluster.your-kubernetes-cluster.kubeconfig).clusters.0.cluster.certificate-authority-data)}"
#     load_config_file = false
# }
