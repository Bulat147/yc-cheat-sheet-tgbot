terraform {
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "2.7.0"
    }
    http = {
      source  = "hashicorp/http"
      version = "3.4.5"
    }
    null = {
      source  = "hashicorp/null"
      version = "3.2.3"
    }
  }
  required_version = ">= 0.13"
}

provider "yandex" {
  service_account_key_file = pathexpand("keys/key.json")
  cloud_id  = var.cloud_id
  folder_id = var.folder_id
  zone      = var.zone
}

resource "yandex_function" "tgbot-func" {
  name              = "tgbot-func"
  description       = "Telegram bot function"
  user_hash         = archive_file.zip.output_sha256
  runtime           = "python312"
  entrypoint        = "tg_bot.handler"
  memory            = 128
  execution_timeout = "100"

  environment = {
    CATALOG_ID = var.folder_id
    TELEGRAM_TOKEN = var.tg_bot_key
    GPT_API_KEY = yandex_iam_service_account_api_key.sa-api-key.secret_key
    GPT_API_URI = "gpt://${var.folder_id}/yandexgpt/latest"
    BUCKET_NAME = yandex_storage_bucket.bucket-tg.bucket
    INSTRUCTION_KEY = yandex_storage_object.instruction.key
    STORAGE_ACCESS_KEY = yandex_iam_service_account_static_access_key.sa-static-key.access_key
    STORAGE_SECRET_KEY = yandex_iam_service_account_static_access_key.sa-static-key.secret_key
  }
  content {
    zip_filename = archive_file.zip.output_path
  }
}

resource "yandex_function_iam_binding" "function-iam" {
  function_id = yandex_function.tgbot-func.id
  role        = "functions.functionInvoker"
  members = [
    "system:allUsers",
  ]
}

output "func_url" {
  value = "https://functions.yandexcloud.net/${yandex_function.tgbot-func.id}"
}

resource "archive_file" "zip" {
  output_path = "../tgbot.zip"
  source_dir = "../tgbot"
  type        = "zip"
}

output "yandex_function_tgbot_func" {
  value = yandex_function.tgbot-func.id
}

resource "null_resource" "set_tg_webhook" {
  provisioner "local-exec" {
    command = "curl 'https://api.telegram.org/bot${var.tg_bot_key}/setWebhook?url=https://functions.yandexcloud.net/${yandex_function.tgbot-func.id}'"
  }

  depends_on = [yandex_function.tgbot-func]
}

resource "null_resource" "delete_tf_webhook" {
  triggers = {
    tg_token = var.tg_bot_key
  }

  provisioner "local-exec" {
    when = destroy
    command = "curl 'https://api.telegram.org/bot${self.triggers.tg_token}/deleteWebhook'"
  }
}

resource "yandex_iam_service_account_api_key" "sa-api-key" {
  service_account_id = var.tf_sa_id
}

resource "yandex_iam_service_account_static_access_key" "sa-static-key" {
  service_account_id = var.tf_sa_id
  description        = "static access key for object storage"
}

resource "yandex_storage_bucket" "bucket-tg" {
  access_key            = yandex_iam_service_account_static_access_key.sa-static-key.access_key
  secret_key            = yandex_iam_service_account_static_access_key.sa-static-key.secret_key
  bucket                = "bkhalilov-bucket-147"
  default_storage_class = "standard"
  anonymous_access_flags {
    read        = true
    list        = true
    config_read = false
  }
}

resource "yandex_storage_object" "instruction" {
  access_key = yandex_iam_service_account_static_access_key.sa-static-key.access_key
  secret_key = yandex_iam_service_account_static_access_key.sa-static-key.secret_key
  bucket     = yandex_storage_bucket.bucket-tg.bucket
  key        = "instruction"
  source     = "../yandex-gpt/instruction.json"
}

