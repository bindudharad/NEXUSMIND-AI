variable "project_name" {
  type    = string
  default = "nexusmind-ai"
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "vpc_id" {
  type = string
}

variable "public_subnet_ids" {
  type = list(string)
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "container_image_api" {
  type = string
}

variable "container_image_web" {
  type = string
}

variable "postgres_dsn" {
  type      = string
  sensitive = true
}

variable "mongo_uri" {
  type      = string
  sensitive = true
}

variable "redis_url" {
  type      = string
  sensitive = true
}

variable "qdrant_url" {
  type = string
}

variable "neo4j_uri" {
  type      = string
  sensitive = true
}

variable "kafka_bootstrap_servers" {
  type = string
}

variable "spark_master_url" {
  type = string
}
