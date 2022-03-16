resource "kubernetes_deployment" "your-deployment" {

    depends_on = [kubernetes_namespace.your-namespace]

    metadata {
        name = "your-deployment"
        namespace = "your-namespace"
        labels = {
            app = "your-app-selector"
        }
    }

    spec {
        replicas = 1

        selector {
            match_labels = {
                app = "your-app-selector"
            }
        }

        template {
            metadata {
                labels = {
                    app = "your-app-selector"
                }
            }

            spec {
                container {
                    image = "your-image:latest"
                    name  = "your-container"

                    port {
                        container_port = 80
                    }
                }
            }
        }
    }
}