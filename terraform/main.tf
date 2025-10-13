terraform {
    required_providers {
        docker = {
            source = "kreuzwerker/docker"
            version = "~> 3.0.1"
        }
        dotenv = {
            source = "jrhouston/dotenv"
            version = "~> 1.0.1"
        }
    }
}

provider "dotenv" {}

provider "docker" {}

resource "docker_network" "satellite-network" {
  name = var.network_name
}

data dotenv env {
  filename = abspath("${path.root}/../.env")
}

module "minio" {
  source = "./modules/minio"

  minio_root_user = data.dotenv.env.env.MINIO_ROOT_USER
  minio_root_password = data.dotenv.env.env.MINIO_ROOT_PASSWORD
  minio_endpoint = data.dotenv.env.env.MINIO_ENDPOINT

  network_name = docker_network.satellite-network.name

  providers = {
    docker = docker
    dotenv = dotenv
  }
}