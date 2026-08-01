# Deployment & DevOps Infrastructure Guide

This guide covers production deployment for the **Insurance Reasoning Engine (IRE)** using Docker, Terraform, Kubernetes, Nginx, Prometheus, ELK, and S3 Backups.

## 1. Production Docker Compose

Run all microservices, backend, datastores, and Nginx reverse proxy:

```bash
docker-compose -f docker-compose.prod.yml up --build -d
```

## 2. Infrastructure as Code (Terraform)

Provision AWS EKS, PostgreSQL RDS, ElastiCache Redis, and S3 Document Bucket:

```bash
cd infrastructure/terraform
terraform init
terraform plan
terraform apply
```

## 3. Kubernetes Deployment (EKS / GKE)

Deploy production manifests with Horizontal Pod Autoscaler (HPA):

```bash
kubectl create namespace ire-production
kubectl apply -f infrastructure/k8s/namespace.yaml
kubectl apply -f infrastructure/k8s/configmap-secrets.yaml
kubectl apply -f infrastructure/k8s/backend-deployment.yaml
kubectl apply -f infrastructure/k8s/ingress.yaml
```

Check HPA auto-scaling status (Scales from 3 to 20 replicas at 70% CPU):

```bash
kubectl get hpa -n ire-production
```

## 4. Automated Database Backup & Recovery

Run encrypted PostgreSQL backup with AES-256 and S3 upload:

```bash
./infrastructure/scripts/backup_recovery.sh backup
```

Restore database from encrypted backup file:

```bash
./infrastructure/scripts/backup_recovery.sh restore /tmp/ire_backups/backup_ire_production_db_20260731_224600.sql.gz.enc
```
