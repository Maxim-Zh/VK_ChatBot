from pony.orm import Database, Required, Json
from settings import DB_CONFIG

db = Database()
db.bind(**DB_CONFIG)


class UserState(db.Entity):
    """
    UserState in Scenario
    """
    user_id = Required(str, unique=True)
    scenario_name = Required(str)
    scenario_step_name = Required(str)
    context = Required(Json)


class Registration(db.Entity):
    """
    Registration application
    """
    name = Required(str)
    email = Required(str)


db.generate_mapping(create_tables=True)
