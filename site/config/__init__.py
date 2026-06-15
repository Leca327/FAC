"""
Registra o PyMySQL como driver MySQLdb para o Django (seção 2.6.8).

PyMySQL é um driver MySQL puro em Python — funciona sem necessidade de
compilação no Windows, ao contrário do mysqlclient.
"""

import pymysql

pymysql.install_as_MySQLdb()
