# CIVO Kubernetes
# ---
# Templates to create a Kubernetes Cluster on CIVO

# Create a new Kubernetes Cluster
resource "civo_kubernetes_cluster" "your-kubernetes-cluster" {
  name = "your-kubernetes-cluster"
  applications = ""
  firewall_id = civo_firewall.your_firewall.id
  network_id = civo_network.your_network.id
  pools {
    size = element(data.civo_size.k8s_std_small.sizes, 0).name
    node_count = 3
  }
  # (Optional) add depenencies on other resources
  depends_on = [ civo_firewall.your_firewall, civo_network.your_network ]
}

# (Optional) Time Sleep elements for other Objects that need to wait a few seconds after the Cluster deployment
# resource "time_sleep" "wait_for_kubernetes" {
#   depends_on = [civo_kubernetes_cluster.your-kubernetes-cluster]
#   create_duration = "20s"
# }
