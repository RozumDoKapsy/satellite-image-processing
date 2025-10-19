terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
    }
  }
}

resource "docker_volume" "satellite_pgdata" {
  name = "satellite_pgdata"
}

resource "docker_image" "postgres" {
  name = "postgres:15"
}

resource "docker_container" "satellite_postgres" {
  image = docker_image.postgres.name
  name = "satellite_pg"

  env = [
    "POSTGRES_USER=${var.postgres_user}",
    "POSTGRES_PASSWORD=${var.postgres_password}",
    "POSTGRES_DB=${var.postgres_db}"
  ]

  ports {
    internal = 5432
    external = 5432
  }

  mounts {
    target = "/var/lib/postgresql/data"
    source = docker_volume.satellite_pgdata.name
    type = "volume"
  }

  mounts {
    target = "/docker-entrypoint-initdb.d"
    source = abspath("${path.root}/../sql")
    type = "bind"
  }

  networks_advanced {
    name = var.network_name
  }
}
