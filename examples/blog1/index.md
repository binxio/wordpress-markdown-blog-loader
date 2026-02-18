---
author: Mark van Holsteijn
brand: xebia.com
categories:
- uncategorized
date: 2025-02-15 23:21:00+01:00
excerpt: In this blog I would show you how to schedule serverless applications using
  Cloud Run and Cloud Scheduler
focus-keywords: markdown upload wordpress
guid: https://env-xebiainnovationproject-staging.kinsta.cloud/wp-json/wp/v2/posts/102254
image: images/banner.jpg
og:
  description: this goes to the Rankmath og description through meta
  image: images/og-banner.jpg
slug: try-this-one-5
status: publish
subtitle: using Google Cloud Run and Cloud Scheduler
title: Testing markdown upload through wordpress API
---

Google [Cloud Run](https://cloud.google.com/run/) is an easy way to deploy your serverless containerized applications. If you need to run your application periodically, you can use Google [Cloud Scheduler](https://cloud.google.com/scheduler/) to do so. In  this blog I will show you how to configure a schedule for a serverless application using [Terraform](https://www.terraform.io).
<!--more-->
To invoke serverless applications on a schedule, you need to:

1. create a service accounts
2. deploy your serverless application
3. grant the scheduler permission
4. create a schedule

As I promote the principle of infrastructure as code, I will show you how to do this using terraform code snippets.

### Create a service account
You can create a service account for the scheduler with which to invoke the application as follows: 

``` { .hcl .wp-block-code }
resource "google_service_account" "scheduler" {
  display_name = "Google Cloud Scheduler"
  account_id   = "scheduler"
}
```
### Deploy using your serverless application
Next you can deploy your serverless application:

```{ .hcl .wp-block-code }
resource "google_cloud_run_service" "application" {
  name     = "application"
  location = "europe-west1"

  template {
    spec {
      containers {
        image = "gcr.io/binx-io-public/paas-monitor:latest"
      }
    }
  }
  timeouts {
    create = "10m"
  }
  depends_on [google_project_service.run]
}
```
in this case, the applicaton deployed is my trusty [paas-monitor](https://github.com/mvanholsteijn/paas-monitor) application.

### Grant the scheduler permission
After the application is deploy, you grant the service account permission to invoke it:

```{ .hcl .wp-block-code }
resource "google_cloud_run_service_iam_member" "scheduler-run-invoker" {
  role   = "roles/run.invoker"
  member = "serviceAccount:${google_service_account.scheduler.email}"

  service  = google_cloud_run_service.application.name
  location = google_cloud_run_service.application.location
}
```

### Create a schedule
Finally you create a schedule to invoke the service as follows:

```{ .hcl .wp-block-code }
resource "google_cloud_scheduler_job" "application" {
  name        = "application"
  description = "invoke every 5 minutes"
  schedule    = "*/5 * * * *"	#<-- Cron expression

  http_target {
    http_method = "GET"
    uri         = "${google_cloud_run_service.application.status[0].url}/status"
    oidc_token {
      service_account_email = google_service_account.scheduler-invoker.email
    }
  }
  depends_on = [google_app_engine_application.app]
}
```

The schedule is defined using a [cron expression](https://en.wikipedia.org/wiki/Cron). Note
that Google Cloud Scheduler requires an app engine application to be deployed:

```{ .hcl .wp-block-code }
resource "google_app_engine_application" "app" {
  project     = data.google_project.current.project_id
  location_id = "europe-west"
  depends_on  = [google_project_service.appengine]
}
```

## Installation
If you want to deploy the complete example, download [main.tf](./main.tf) and type:

```{ .bash .wp-block-code }
export TF_VAR_project=$(gcloud config get-value project)
terraform init
terraform apply
```

## Conclusion
With Google [Cloud Run](https://cloud.google.com/run/) it is easy to deploy your containerized applications in a serverless fashion and 
use the Google [Cloud Scheduler](https://cloud.google.com/scheduler/) to schedule invocation of application in a secure way.

![binx.io logo](./images/binx-logo.png)