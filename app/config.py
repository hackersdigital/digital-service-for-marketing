import os
from dotenv import load_dotenv

def load_config(app):
    load_dotenv()
    app.config.update(
        SECRET_KEY=os.getenv("APP_SECRET", "change-me"),
        BASE_URL=os.getenv("BASE_URL", "http://localhost"),
        MONGO_URI=os.getenv("MONGO_URI", "mongodb://localhost:27017"),
        MONGO_DB=os.getenv("MONGO_DB", "marketingdb"),
        LP_CAMPAIGN_ID=os.getenv("LP_CAMPAIGN_ID"),
        LP_SUPPLIER_ID=os.getenv("LP_SUPPLIER_ID"),
        LP_KEY=os.getenv("LP_KEY"),
        AGENT_TOKEN=os.getenv("AGENT_TOKEN"),
        CLIENT_TOKEN=os.getenv("CLIENT_TOKEN")
    )
