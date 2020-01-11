from django.test import TestCase

# Create your tests here.
cart1 = {}
cart2 = {}
cart3 = {}
cart4 = {}
import random

for sku_id in range(1, 101):
    count = random.randint(1, 10)
    selected = (sku_id % 2 == 0)
    cart1[sku_id] = {'count': count, 'selected': selected}
    cart2[sku_id] = {'c': count, 's': selected}
    cart3[sku_id] = [count, selected]
    cart4[sku_id] = count * (1 if selected else -1)

import pickle, base64


def get_line(d):
    print(len(base64.b64encode(pickle.dumps(d))))


get_line(cart1)
get_line(cart2)
get_line(cart3)
get_line(cart4)

from itsdangerous import TimedJSONWebSignatureSerializer as ser

b = ser('123456', 3600)
data = {'openid': 654321}
s = b.dumps(data)
