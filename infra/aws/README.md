# AWS Deployment Readiness

This Terraform stack prepares NEXUSMIND AI for AWS ECS Fargate with ECR repositories, CloudWatch logs, ALB routing, private API tasks, public web tasks, and ECS service autoscaling.

It expects production images to be pushed to ECR and managed data endpoints to be supplied through Terraform variables or an external secrets workflow.

Recommended managed services:

- ECS Fargate for `api` and `web`
- ECR for immutable container images with scan-on-push
- RDS PostgreSQL for relational analytics
- DocumentDB-compatible MongoDB for AI event logs
- ElastiCache Redis for realtime cache/pub-sub
- CloudWatch Logs for observability
- Application Load Balancer plus ACM TLS certificates for public traffic
- ECS service autoscaling for API and web workloads
