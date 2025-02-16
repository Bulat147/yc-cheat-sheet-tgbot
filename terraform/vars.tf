variable "cloud_id" {
  type        = string
  description = "Идентификатор облака в Yandex Cloud"
}

variable "folder_id" {
  type        = string
  description = "Идентификатор каталога в Yandex Cloud"
}

variable "zone" {
  type        = string
  description = "Зона доступности в Yandex Cloud"
  validation {
    condition     = contains(["ru-central1-a", "ru-central1-b", "ru-central1-c", "ru-central1-d"], var.zone)
    error_message = "Укажите верную зону доступности."
  }
}

variable "tf_sa_id" {
  type = string
  description = "Сервисный аккаунт для terraform"
}

variable "tg_token" {
  type = string
  description = "Токен телеграм-бота"
}