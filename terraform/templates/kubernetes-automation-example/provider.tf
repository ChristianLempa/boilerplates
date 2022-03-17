terraform {

    required_version = ">= 0.13.0"

    required_providers {
        cloudflare = {
            source = "cloudflare/cloudflare"
            version = "~> 3.0"
        }
        civo = {
            source = "civo/civo"
            version = "~> 1.0.13"
        }
        kubernetes = {
            source = "hashicorp/kubernetes"
            version = "2.8.0"     
        }
        helm = {
            source = "hashicorp/helm"
            version = "2.4.1"
        }
        kubectl = {
            source = "gavinbunney/kubectl"
            version = "1.13.1"
        }
    }
}

provider "civo" {
    token = var.civo_token
    # (Optional) switch datacenter region
    # region = "FRA1"
}

provider "cloudflare" {
    email = var.cloudflare_email
    api_key =  var.cloudflare_api_key
}

provider "kubernetes" {
    host = "${yamldecode(civo_kubernetes_cluster.k8s_demo_1.kubeconfig).clusters.0.cluster.server}"
    client_certificate = "${base64decode(yamldecode(civo_kubernetes_cluster.k8s_demo_1.kubeconfig).users.0.user.client-certificate-data)}"
    client_key = "${base64decode(yamldecode(civo_kubernetes_cluster.k8s_demo_1.kubeconfig).users.0.user.client-key-data)}"
    cluster_ca_certificate = "${base64decode(yamldecode(civo_kubernetes_cluster.k8s_demo_1.kubeconfig).clusters.0.cluster.certificate-authority-data)}"
}

provider "helm" {
    kubernetes {
        host = "${yamldecode(civo_kubernetes_cluster.k8s_demo_1.kubeconfig).clusters.0.cluster.server}"
        client_certificate = "${base64decode(yamldecode(civo_kubernetes_cluster.k8s_demo_1.kubeconfig).users.0.user.client-certificate-data)}"
        client_key = "${base64decode(yamldecode(civo_kubernetes_cluster.k8s_demo_1.kubeconfig).users.0.user.client-key-data)}"
        cluster_ca_certificate = "${base64decode(yamldecode(civo_kubernetes_cluster.k8s_demo_1.kubeconfig).clusters.0.cluster.certificate-authority-data)}"
    }
}

provider "kubectl" {
    host = "${yamldecode(civo_kubernetes_cluster.k8s_demo_1.kubeconfig).clusters.0.cluster.server}"
    client_certificate = "${base64decode(yamldecode(civo_kubernetes_cluster.k8s_demo_1.kubeconfig).users.0.user.client-certificate-data)}"
    client_key = "${base64decode(yamldecode(civo_kubernetes_cluster.k8s_demo_1.kubeconfig).users.0.user.client-key-data)}"
    cluster_ca_certificate = "${base64decode(yamldecode(civo_kubernetes_cluster.k8s_demo_1.kubeconfig).clusters.0.cluster.certificate-authority-data)}"
    load_config_file = false
}