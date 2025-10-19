terraform {
  required_providers {
    kind = {
      source = "tehcyx/kind"
      version = "0.9.0"
    }
  }
}

resource "kind_cluster" "kind_cluster" {
  name = var.cluster_name
  node_image = "kindest/node:v1.34.0"

  kind_config {
    api_version = "kind.x-k8s.io/v1alpha4"
    kind        = "Cluster"

    node {
        role = "control-plane"
        extra_port_mappings {
            container_port = 80
            host_port      = 80
        }
    }
    dynamic "node" {
      for_each = toset([for i in range(var.node_count) : i])
      content {
        role = "worker"
      }
    }
  }
}
