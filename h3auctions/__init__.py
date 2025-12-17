import os

# Optional: allow using PyMySQL as MySQL driver if mysqlclient is unavailable
if os.environ.get("DJANGO_USE_PYMYSQL", "0") == "1":
	import pymysql  # type: ignore
	pymysql.install_as_MySQLdb()





