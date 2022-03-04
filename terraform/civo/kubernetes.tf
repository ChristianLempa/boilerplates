# CIVO Kubernetes
# ---
# Templates to create a Kubernetes Cluster on CIVO

# Create a new Kubernetes Cluster
resource "civo_kubernetes_cluster" "your-kubernetes-cluster" {
    name = "your-kubernetes-cluster"
    applications = ""
    num_target_nodes = 2
    target_nodes_size = element(data.civo_size.xsmall.sizes, 0).name
}

# (Optional) Time Sleep elements for other Objects that need to wait a few seconds after the Cluster deployment
resource "time_sleep" "wait_for_kubernetes" {
  depends_on = [civo_kubernetes_cluster.your-kubernetes-cluster]

  create_duration = "20s"
}
