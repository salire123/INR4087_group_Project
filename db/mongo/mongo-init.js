db.createUser({
    user: "mongo",
    pwd: "mongo",
    roles: [{ role: "readWrite", db: "social_media_db" }]
});

