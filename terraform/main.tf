terraform {
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
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
  user_hash         = "tg-bot-function"
  runtime           = "python312"
  entrypoint        = "main"
  memory            = "128"
  execution_timeout = "10"
  tags = ["my_tag"]
  content {
    zip_filename = "../tgbot.zip"
  }
}

output "yandex_function_tgbot_func" {
  value = yandex_function.tgbot-func.id
}

