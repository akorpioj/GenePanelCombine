import redis

r = redis.Redis(
    host='redis-16422.c328.europe-west3-1.gce.redns.redis-cloud.com',
    port=16422,
    decode_responses=True,
    username="default",
    password="****",
)

success = r.set('foo', 'bar')
# True

result = r.get('foo')
print(result)