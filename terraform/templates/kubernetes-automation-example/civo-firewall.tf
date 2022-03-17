resource "civo_firewall" "fw_demo_1" {
    name = "fw_demo_1"

    # (optional) Don't create Default Firewall rules [default = true]
    create_default_rules = false
    
    # (optnal) Specify network ID
    # network_id = 
}

resource "civo_firewall_rule" "kubernetes_api_server" {
    firewall_id = civo_firewall.fw_demo_1.id
    protocol = "tcp"
    start_port = "6443"
    end_port = "6443"
    cidr = ["0.0.0.0/0"]
    direction = "ingress"
    action = "allow"
    label = "kubernetes_api_server"
}

resource "civo_firewall_rule" "kubernetes_http" {
    firewall_id = civo_firewall.fw_demo_1.id
    protocol = "tcp"
    start_port = "80"
    end_port = "80"
    cidr = ["0.0.0.0/0"]
    direction = "ingress"
    action = "allow"
    label = "kubernetes_http"
}

resource "civo_firewall_rule" "kubernetes_https" {
    firewall_id = civo_firewall.fw_demo_1.id
    protocol = "tcp"
    start_port = "443"
    end_port = "443"
    cidr = ["0.0.0.0/0"]
    direction = "ingress"
    action = "allow"
    label = "kubernetes_https"
}