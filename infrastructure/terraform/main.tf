# Enterprise Platform — Terraform Infrastructure as Code (AWS EKS, RDS PostgreSQL, ElastiCache Redis, S3)
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# 1. VPC & Networking
resource "aws_vpc" "ire_vpc" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = {
    Name        = "ire-production-vpc"
    Environment = "production"
  }
}

resource "aws_subnet" "public_1" {
  vpc_id                  = aws_vpc.ire_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true
}

resource "aws_subnet" "private_1" {
  vpc_id            = aws_vpc.ire_vpc.id
  cidr_block        = "10.0.10.0/24"
  availability_zone = "${var.aws_region}a"
}

# 2. S3 Storage Bucket for Backups & Artifacts
resource "aws_s3_bucket" "ire_documents" {
  bucket = "ire-enterprise-documents-${var.aws_region}"
}

resource "aws_s3_bucket_server_side_encryption_configuration" "s3_encryption" {
  bucket = aws_s3_bucket.ire_documents.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# 3. PostgreSQL RDS Database Cluster
resource "aws_db_instance" "ire_postgres" {
  allocated_storage         = 100
  max_allocated_storage     = 500
  engine                    = "postgres"
  engine_version            = "16.1"
  instance_class            = "db.m6i.large"
  db_name                   = "ire_production_db"
  username                  = var.db_username
  password                  = var.db_password
  multi_az                  = true
  storage_encrypted         = true
  skip_final_snapshot       = false
  final_snapshot_identifier = "ire-postgres-final-snapshot"
}

# 4. ElastiCache Redis Cluster
resource "aws_elasticache_cluster" "ire_redis" {
  cluster_id           = "ire-redis-cluster"
  engine               = "redis"
  node_type            = "cache.m6g.large"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
}
