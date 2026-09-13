---
title: 20231124-terraform-vercel
date: 2023-11-24
tags:
  - terraform
  - vercel
---
vercel token: https://vercel.com/guides/how-do-i-use-a-vercel-api-access-token
npx create-next-app nextjs-terraform-demo
main.tf
```terraform
terraform {
  required_providers {
    vercel = {
      source = "vercel/vercel"
      version = "~> 0.3"
    }
  }
}
```
`terraform init`
```terraform
terraform {
  required_providers {
    vercel = {
      source = "vercel/vercel"
      version = "~> 0.3"
    }
  }
}
resource "vercel_project" "example" {
  name      = "terraform-test-project"
  framework = "nextjs"
  git_repository = {
    type = "github"
    repo = "alanhc/nextjs-terraform-demo"
  }
}
```
terraform apply
## Ref
- https://vercel.com/guides/integrating-terraform-with-vercel
- https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli
- https://vercel.com/guides/how-do-i-use-a-vercel-api-access-token