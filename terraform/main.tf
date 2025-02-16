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
  environment = { "TELEGRAM_TOKEN" = var.tg_token }
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
    command = "curl 'https://api.telegram.org/bot${var.tg_token}/setWebhook?url=https://functions.yandexcloud.net/${yandex_function.tgbot-func.id}'"
  }

  depends_on = [yandex_function.tgbot-func]
}

resource "null_resource" "delete_tf_webhook" {
  triggers = {
    tg_token = var.tg_token
  }

  provisioner "local-exec" {
    when = destroy
    command = "curl 'https://api.telegram.org/bot${self.triggers.tg_token}/deleteWebhook'"
  }
}
