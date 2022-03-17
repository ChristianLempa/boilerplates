resource "civo_kubernetes_cluster" "k8s_demo_1" {
    name = "k8s_demo_1"
    applications = ""
    num_target_nodes = 2
    target_nodes_size = element(data.civo_size.xsmall.sizes, 0).name
    firewall_id = civo_firewall.fw_demo_1.id
}

resource "time_sleep" "wait_for_kubernetes" {

    depends_on = [civo_kubernetes_cluster.k8s_demo_1]

    create_duration = "20s"
}
