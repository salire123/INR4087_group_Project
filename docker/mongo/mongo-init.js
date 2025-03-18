db.createUser({
    user: "mongo",
    pwd: "mongo",
    roles: [{ role: "readWrite", db: "social_media_db" }]
});


db.createUser({
    user: "mongo",
    pwd: "mongo",
    roles: [{ role: "readWrite", db: "history_like" }]
});
