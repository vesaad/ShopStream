// ShopStream MongoDB Initialization
db = db.getSiblingDB('shopstream');

// Krijo indekse vetëm nëse collections ekzistojnë (opsionale, por e sigurt)
db.products.createIndex({ "name": 1 });
db.products.createIndex({ "category": 1 });
db.shopping_carts.createIndex({ "user_id": 1 });
db.inventory.createIndex({ "product_id": 1 }, { unique: true });
db.analytics_data.createIndex({ "topic": 1 });
db.analytics_data.createIndex({ "timestamp": -1 });

// Fut produktet – insertMany krijon collection automatikisht nëse nuk ekziston
db.products.insertMany([
    {
        name: "MacBook Pro 16\"",
        price: 2499.99,
        stock: 15,
        category: "Electronics",
        description: "Apple MacBook Pro with M3 chip",
        created_at: new Date()
    },
    {
        name: "iPhone 15 Pro",
        price: 999.99,
        stock: 50,
        category: "Electronics",
        description: "Latest iPhone model",
        created_at: new Date()
    },
    {
        name: "Sony WH-1000XM5",
        price: 399.99,
        stock: 30,
        category: "Audio",
        description: "Premium wireless noise-canceling headphones",
        created_at: new Date()
    },
    {
        name: "Samsung 55\" QLED TV",
        price: 1299.99,
        stock: 10,
        category: "Electronics",
        description: "4K QLED Smart TV with Quantum HDR",
        created_at: new Date()
    },
    {
        name: "Dell XPS 15",
        price: 1799.99,
        stock: 20,
        category: "Electronics",
        description: "Intel Core i7, 16GB RAM, RTX 3050, 512GB SSD",
        created_at: new Date()
    }
]);