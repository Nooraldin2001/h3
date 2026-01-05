import os

# Optional: allow using PyMySQL as MySQL driver if mysqlclient is unavailable
def _env_truthy(value: str | None) -> bool:
	if value is None:
		return False
	return value.strip().lower() in {"1", "true", "yes", "on"}


# Support both env var names:
# - DJANGO_USE_PYMYSQL=1 (legacy)
# - USE_PYMYSQL=True (used in settings/docs)
if _env_truthy(os.environ.get("DJANGO_USE_PYMYSQL")) or _env_truthy(os.environ.get("USE_PYMYSQL")):
	import pymysql  # type: ignore

	pymysql.install_as_MySQLdb()





