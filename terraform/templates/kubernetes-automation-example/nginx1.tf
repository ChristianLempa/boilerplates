# NGINX 1 Test Deployment
#
# TODO: Change your-domain according to your DNS record that you want to create
# TODO: Change your-zone-id according to your DNS zone ID in Cloudflare
# ---

resource "kubernetes_namespace" "nginx1" {

    depends_on = [
        time_sleep.wait_for_kubernetes
    ]

    metadata {
        name = "nginx1"
    }
}


resource "kubernetes_deployment" "nginx1" {

    depends_on = [
        kubernetes_namespace.nginx1
    ]

    metadata {
        name = "nginx1"
        namespace = "nginx1"
        labels = {
            app = "nginx1"
        }
    }

    spec {
        replicas = 1

        selector {
            match_labels = {
                app = "nginx1"
            }
        }

        template {
            metadata {
                labels = {
                    app = "nginx1"
                }
            }

            spec {
                container {
                    image = "nginx:latest"
                    name  = "nginx"

                    port {
                        container_port = 80
                    }
                }
            }
        }
    }
}


resource "kubernetes_service" "nginx1" {

    depends_on = [
        kubernetes_namespace.nginx1
    ]

    metadata {
        name = "nginx1"
        namespace = "nginx1"
    }
    spec {
        selector = {
            app = "nginx1"
        }
        port {
            port = 80
        }

        type = "ClusterIP"
    }
}


resource "kubectl_manifest" "nginx1-certificate" {

    depends_on = [kubernetes_namespace.nginx1, time_sleep.wait_for_clusterissuer]

    yaml_body = <<YAML
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: nginx1
  namespace: nginx1
spec:
  secretName: nginx1
  issuerRef:
    name: cloudflare-prod
    kind: ClusterIssuer
  dnsNames:
  - 'your-domain'   
    YAML
}


resource "kubernetes_ingress_v1" "nginx1" {

    depends_on = [kubernetes_namespace.nginx1]

    metadata {
        name = "nginx1"
        namespace = "nginx1"
    }

    spec {
        rule {

            host = "your-domain"

            http {

                path {
                    path = "/"

                    backend {
                        service {
                            name = "nginx1"
                            port {
                                number = 80
                            }
                        }
                    }

                }
            }
        }

        tls {
          secret_name = "nginx1"
          hosts = ["your-domain"]
        }
    }
}

resource "cloudflare_record" "clcreative-main-cluster" {
    zone_id = "your-zone-id"
    name = "your-domain"
    value =  data.civo_loadbalancer.traefik_lb.public_ip
    type = "A"
    proxied = false
}
