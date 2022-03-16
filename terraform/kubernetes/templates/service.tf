resource "kubernetes_service" "your-service" {

    depends_on = [kubernetes_namespace.your-namespace]

    metadata {
        name = "your-service"
        namespace = "your-namespace"
    }
    spec {
        selector = {
            app = "your-app-selector"
        }
        port {
            port = 80
        }

        type = "ClusterIP"
    }
}