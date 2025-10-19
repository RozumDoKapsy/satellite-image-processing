terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
    }
  }
}

resource "docker_volume" "minio_data" {
  name = "minio_data"
}

resource "docker_image" "minio" {
  name = "minio/minio:latest"
}

resource "docker_container" "minio" {
  image = docker_image.minio.name
  name = "satellite_minio"

  env = [
    "MINIO_ROOT_USER=${var.minio_root_user}",
    "MINIO_ROOT_PASSWORD=${var.minio_root_password}"
  ]

  ports {
    internal = 9000
    external = 9000
  }

  ports {
    internal = 9090
    external = 9090
  }

  command = ["server", "/data", "--console-address", ":9090"]

  mounts {
    target = "/data"
    source = docker_volume.minio_data.name
    type = "volume"
  }

  networks_advanced {
    name = var.network_name
  }
}
