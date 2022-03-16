resource "kubernetes_ingress_v1" "your-ingress" {

    depends_on = [kubernetes_namespace.your-namespace]

    metadata {
        name = "your-ingress"
        namespace = "your-namespace"
    }

    spec {
        rule {

            host = "your-domain"

            http {

                path {
                    path = "/"

                    backend {
                        service {
                            name = "your-service"
                            port {
                                number = 80
                            }
                        }
                    }

                }
            }
        }

        # (Optional) Add an SSL Certificate
        # tls {
        #     secret_name = "ssl-certificate-object"
        #     hosts = ["your-domain"]
        # }
    }
}