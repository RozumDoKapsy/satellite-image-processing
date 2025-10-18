resource "null_resource" "kind_cluster" {
  provisioner "local-exec" {
    command = "bash ${abspath("${path.root}/../scripts/kind_create_cluster.sh")} --name ${var.cluster_name} --nodes ${var.node_count}"
  }
}