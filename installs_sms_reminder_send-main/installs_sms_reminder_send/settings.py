from pydantic import BaseSettings


class Settings(BaseSettings):
    opsgenie_api_key: str
    smartsheet_sheet_id: int
    smartsheet_token: str
    twilio_account_sid: str
    twilio_token:str
    from_num:str

