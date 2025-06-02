# Kubernetes Provider
# ---
# Initial Provider Configuration for Kubernetes

terraform {

    required_version = ">= 0.13.0"

    required_providers {
        kubernetes = {
            source = "hashicorp/kubernetes"
            version = "2.37.1"
        }
    }
}

# Dynamic Configuration from CIVO Kubernetes deployment
# provider "kubernetes" {
#     host = "${yamldecode(civo_kubernetes_cluster.your-kubernetes-cluster.kubeconfig).clusters.0.cluster.server}"
#     client_certificate = "${base64decode(yamldecode(civo_kubernetes_cluster.your-kubernetes-cluster.kubeconfig).users.0.user.client-certificate-data)}"
#     client_key = "${base64decode(yamldecode(civo_kubernetes_cluster.your-kubernetes-cluster.kubeconfig).users.0.user.client-key-data)}"
#     cluster_ca_certificate = "${base64decode(yamldecode(civo_kubernetes_cluster.your-kubernetes-cluster.kubeconfig).clusters.0.cluster.certificate-authority-data)}"
# }
