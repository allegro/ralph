echo -e "\n\ndc2"
redis-cli -h localhost -p 26379 -n 2 llen dc2
echo -e "\n\ndc3"
redis-cli -h localhost -p 26379 -n 2 llen dc3
echo -e "\n\nte2"
redis-cli -h localhost -p 26379 -n 2 llen te2
echo -e "\n\ncelery"
redis-cli -h localhost -p 26379 -n 2 llen celery
