# Разворачивание бота

1. Создать сервисный аккаунт для terraform с ролью admin
```bash
  yc iam service-account create --name terraformsa \
  --description "sa for terraform"
```
Полученный id сохранить и указать в команде ниже:
* \<folder-id\> - идентификатор директории в облаке
* \<service-account-id\> - идентификатор созданного сервисного аккаунта
```bash
  yc resource-manager folder add-access-binding <folder-id> \
  --role admin \
  --subject serviceAccount:<service-account-id>
```
2. Создать ключ сервисного аккаунта
```bash
  yc iam key create --service-account-id <service-account-id> --output terraform/keys/key.json
```
Гдe \<service-account-id\> - идентификатор созданного сервисного аккаунта

3. Создать файл terraform/values.tfvars со следующим содержанием:
```
cloud_id  = "<id облака>"
folder_id = "<id директории в облаке>"
zone      = "<дефолтная зона>"
tf_sa_id  = "<id сервисного аккаунта для terraform>"
tg_token  = "<токен телеграм бота>"
```
4. Проинициализировать провайдеров для terraform
```bash
  cd terraform
  terraform init
```
4. Посмотреть план разворачиваемых ресурсов
```bash
  terraform plan -var-file=values.tfvars
```
5. Развернуть ресурсы в облаке
```bash
  terraform apply -var-file=values.tfvars
```
6. Удалить ресурсы с облака
```bash
  terraform apply -var-file=values.tfvars
```