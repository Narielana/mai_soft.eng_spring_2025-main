db = db.getSiblingDB('delivery_db');
db.createCollection('deliveries');

db.deliveries.insertMany([
  {
    status: "pending",
    created_at: new Date(),
    updated_at: null,
    user_id: 1,
    description: "Доставка смартфона с аксессуарами",
    address: "ул. Ленина, 10, кв. 5",
    contact_phone: "+7 (999) 123-45-67",
    delivery_time: null
  },
  {
    status: "in_progress",
    created_at: new Date(Date.now() - 2*24*60*60*1000), // 2 дня назад
    updated_at: new Date(Date.now() - 1*24*60*60*1000), // 1 день назад
    user_id: 1,
    description: "Доставка ноутбука и периферии",
    address: "ул. Гагарина, 22, кв. 15",
    contact_phone: "+7 (999) 987-65-43",
    delivery_time: new Date(Date.now() + 1*24*60*60*1000) // завтра
  },
  {
    status: "delivered",
    created_at: new Date(Date.now() - 5*24*60*60*1000), // 5 дней назад
    updated_at: new Date(Date.now() - 2*24*60*60*1000), // 2 дня назад
    user_id: 1,
    description: "Доставка телевизора и кронштейна",
    address: "пр. Мира, 156, кв. 78",
    contact_phone: "+7 (999) 456-78-90",
    delivery_time: new Date(Date.now() - 2*24*60*60*1000) // 2 дня назад
  },
  {
    status: "canceled",
    created_at: new Date(Date.now() - 3*24*60*60*1000), // 3 дня назад
    updated_at: new Date(Date.now() - 2*24*60*60*1000), // 2 дня назад
    user_id: 1,
    description: "Доставка книг",
    address: "ул. Советская, 42, кв. 15",
    contact_phone: "+7 (999) 111-22-33",
    delivery_time: null
  },
  {
    status: "pending",
    created_at: new Date(),
    updated_at: null,
    user_id: 1,
    description: "Доставка мебели",
    address: "ул. Пушкина, 15, кв. 10",
    contact_phone: "+7 (999) 444-55-66",
    delivery_time: new Date(Date.now() + 5*24*60*60*1000) // через 5 дней
  }
]);

db.deliveries.createIndex({ user_id: 1 });
db.deliveries.createIndex({ status: 1 });


db.createUser({
  user: "stud",
  pwd: "stud",
  roles: [
    { role: "readWrite", db: "delivery_db" }
  ]
});

print("Инициализация MongoDB завершена успешно");
