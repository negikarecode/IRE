output "s3_bucket_name" {
  value = aws_s3_bucket.ire_documents.id
}

output "rds_postgres_endpoint" {
  value = aws_db_instance.ire_postgres.endpoint
}

output "redis_cluster_endpoint" {
  value = aws_elasticache_cluster.ire_redis.cache_nodes[0].address
}
