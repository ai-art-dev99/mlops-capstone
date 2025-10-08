variable "project_id" { type = string }
variable "region" { type = string  default = "europe-west2" }
variable "cluster_name" { type = string default = "mlops-capstone" }
variable "image_repository" { type = string default = "ghcr.io/yourname/mlops-capstone" }
variable "image_tag" { type = string default = "latest" }
