workspace {
    name "Delivery System"
    description "Система управления доставками посылок между пользователями"

    model {
        customer = person "Customer" "Пользователь, который отправляет и получает посылки"
        admin = person "Admin" "Администратор системы, управляющий пользователями и посылками"
        courier = person "Courier" "Курьер, доставляющий посылки"
        
        paymentSystem = softwareSystem "Payment System" "Внешняя платежная система" "External System"
        notificationSystem = softwareSystem "Notification System" "Система уведомлений (Email, SMS)" "External System"
        
        deliverySystem = softwareSystem "Delivery System" "Система управления доставками посылок между пользователями" {
            webApplication = container "Web Application" "Предоставляет пользовательский интерфейс для всех типов пользователей" "React, TypeScript" "Web Browser"
            
            apiGateway = container "API Gateway" "Единая точка входа для всех API-запросов" "Nginx, Traefik" "API Gateway"
            
            userService = container "User Service" "Управление пользователями и аутентификация" "Python, FastAPI" "Microservice"
            parcelService = container "Parcel Service" "Управление посылками" "Python, FastAPI" "Microservice"
            deliveryService = container "Delivery Service" "Управление доставками" "Python, FastAPI" "Microservice"
            paymentService = container "Payment Service" "Обработка платежей за доставку" "Python, FastAPI" "Microservice"
            notificationService = container "Notification Service" "Отправка уведомлений" "Python, FastAPI" "Microservice"
            
            userDb = container "User Database" "Хранит информацию о пользователях" "PostgreSQL" "Database"
            parcelDb = container "Parcel Database" "Хранит информацию о посылках" "PostgreSQL" "Database"
            deliveryDb = container "Delivery Database" "Хранит информацию о доставках" "PostgreSQL" "Database"
            
            messageBus = container "Message Bus" "Обеспечивает асинхронную коммуникацию между сервисами" "Kafka" "Message Bus"
            
            webApplication -> apiGateway "Отправляет запросы" "JSON/HTTPS"
            
            apiGateway -> userService "Перенаправляет запросы пользователей" "JSON/HTTPS"
            apiGateway -> parcelService "Перенаправляет запросы о посылках" "JSON/HTTPS"
            apiGateway -> deliveryService "Перенаправляет запросы о доставках" "JSON/HTTPS"
            apiGateway -> paymentService "Перенаправляет запросы о платежах" "JSON/HTTPS"
            
            userService -> userDb "Читает и записывает данные пользователей" "SQLAlchemy/PostgreSQL"
            parcelService -> parcelDb "Читает и записывает данные посылок" "SQLAlchemy/PostgreSQL"
            deliveryService -> deliveryDb "Читает и записывает данные доставок" "SQLAlchemy/PostgreSQL"
            
            userService -> messageBus "Публикует события пользователей" "Kafka Protocol"
            parcelService -> messageBus "Публикует события посылок" "Kafka Protocol"
            deliveryService -> messageBus "Публикует события доставок" "Kafka Protocol"
            paymentService -> messageBus "Публикует события платежей" "Kafka Protocol"
            notificationService -> messageBus "Подписывается на события для отправки уведомлений" "Kafka Protocol"
            
            deliveryService -> userService "Проверяет существование отправителя и получателя" "JSON/HTTPS"
            deliveryService -> parcelService "Получает информацию о посылке" "JSON/HTTPS"
            parcelService -> userService "Проверяет существование пользователя" "JSON/HTTPS"
            paymentService -> deliveryService "Получает информацию о стоимости доставки" "JSON/HTTPS"
            
            paymentService -> paymentSystem "Обрабатывает платежи" "JSON/HTTPS"
            notificationService -> notificationSystem "Отправляет уведомления" "JSON/HTTPS"
        }
        
        customer -> deliverySystem "Отправляет и получает посылки"
        admin -> deliverySystem "Управляет системой"
        courier -> deliverySystem "Доставляет посылки"
        
        customer -> webApplication "Использует веб-интерфейс для отправки и получения посылок"
        admin -> webApplication "Использует веб-интерфейс для управления системой"
        courier -> webApplication "Использует веб-интерфейс для управления доставками"
    }
    
    views {
        systemContext deliverySystem "SystemContext" {
            include *
            autoLayout
        }
        
        container deliverySystem "Containers" {
            include *
            autoLayout
        }
        
        dynamic deliverySystem "CreateDelivery" "Процесс создания доставки от пользователя к пользователю" {
            customer -> webApplication "Заполняет форму создания доставки"
            webApplication -> apiGateway "POST /api/deliveries"
            apiGateway -> deliveryService "Перенаправляет запрос"
            deliveryService -> userService "Проверяет существование отправителя и получателя"
            userService -> deliveryService "Возвращает данные пользователей"
            deliveryService -> parcelService "Запрашивает создание новой посылки"
            parcelService -> parcelDb "Сохраняет данные о посылке"
            parcelDb -> parcelService "Подтверждает сохранение"
            parcelService -> deliveryService "Возвращает данные созданной посылки"
            deliveryService -> deliveryDb "Сохраняет данные о доставке"
            deliveryDb -> deliveryService "Подтверждает сохранение"
            deliveryService -> messageBus "Публикует событие 'delivery.created'"
            messageBus -> notificationService "Передает событие для уведомления"
            notificationService -> notificationSystem "Отправляет уведомления отправителю и получателю"
            deliveryService -> paymentService "Запрашивает создание платежа"
            paymentService -> paymentSystem "Инициирует платеж"
            paymentSystem -> paymentService "Подтверждает платеж"
            paymentService -> deliveryService "Возвращает результат платежа"
            deliveryService -> apiGateway "Возвращает данные созданной доставки"
            apiGateway -> webApplication "Возвращает успешный ответ"
            webApplication -> customer "Отображает подтверждение и трек-номер"
            autoLayout
        }
        
        theme default
    }
}
