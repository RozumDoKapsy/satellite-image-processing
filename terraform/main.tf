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
        kind = {
            source = "tehcyx/kind"
            version = "0.9.0"
        }
    }
}

provider "dotenv" {}

provider "docker" {}

provider "kind" {}

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
  }
}

module "satellite_postgres" {
  source = "./modules/postgres"

  postgres_user = data.dotenv.env.env.SATELLITE_POSTGRES_USER
  postgres_password = data.dotenv.env.env.SATELLITE_POSTGRES_PASSWORD
  postgres_db = data.dotenv.env.env.SATELLITE_POSTGRES_DB

  network_name = docker_network.satellite-network.name

  providers = {
    docker = docker
  }
}

module "kind_cluster" {
  source = "./modules/kind_cluster"

  cluster_name = data.dotenv.env.env.CLUSTER_NAME
  node_count = data.dotenv.env.env.NODE_COUNT

  providers = {
    kind = kind
  }
}
