import requests
import json
import random
from config import *

parent_resource = 259

request_url = '%s/api/resource/%s/feature/' % (ngw_host, 55)

for i in range(0, 3):
    # Структура нового объекта
    # new object structure
    data = {
        "extensions": {
            "attachment": None,
            "description": None
        },
        "fields": {
            "id": i,
            "Name": u"Пример (example) %s" % i
        },
        "geom": "POINT (%s %s)" % (random.randint(15112000,15114000), random.randint(6057000,6059000))
    }

    # отправляем запрос
    # send request
    r = requests.post(request_url,
                      data=json.dumps(data),
                      auth=(ngw_user, ngw_password))

    print(i)
    print(u'Статус (Status): %s' % r.status_code)
    print(r.content)