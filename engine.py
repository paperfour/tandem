from sqlalchemy import create_engine

_engine = None

def start_engine():
    # --- Engine / Session ---
    global _engine
    _engine = create_engine(
        "sqlite:///main.db",
        future=True
    )

def get_engine():
    global _engine
    return _engine