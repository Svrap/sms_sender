from installs_sms_reminder_send import logger, opsgenie, config
from installs_smartsheets import Smartsheet
from settings import Settings
import twillo
import exceptions

# send_sms reads the twillo deatils and send the sms
def send_Sms(twilio_account_sid : str,twilio_token : str,from_num : str,sms_body: str ,to_num : str):
    client=Client(twilio_account_sid,twilio_token)
    message=client.messages.create(
        from_=from_num,
        body=sms_body,
        to=to_num
    )
    # return message.sid
    return True

#adding creds here for testing purpose, will remove them once testing is completed
def get_creds():
    cred_data = {
        "opsgenie_api_key": "str",
        "smartsheet_sheet_id": "int",
        "smartsheet_token": "str",
        "twilio_account_sid": "str",
        "twilio_token":"str",
        "from_num":"str"
    }
    creds = Settings(**cred_data)
    return creds



def main(*args) -> None:
    """
    Main entrypoint into sending sms reminders
    :param args: Leave them the way these are. AWS lambda functions passed in two args but we dont need to use them
    :return:
    """
    logger.info('Running installs sms reminder')

    # First get data from smartsheet
    #ss = Smartsheet(config.smartsheet_sheet_id, config.smartsheet_token)
    creds = get_creds()
    ss = Smartsheet(creds.smartsheet_sheet_id, creds.smartsheet_token)

    reminder_list_72_hours = ss.reminder_list_72_hours()
    reminder_list_24_hours = ss.reminder_list_24_hours()

    # For each of the phone number in 72 and 24 hours, send the relevant sms message.
        # After sending sms, mark the relevant column in smartsheet as checked.

    #adding smsbody for 72hrs list
    sms_body_72_hours = "72 hours message template"
    for number in reminder_list_72_hours:
        name = reminder_list_72_hours[number]
        send_sms=send_Sms(creds.twilio_account_sid,creds.twilio_token,creds.from_num,sms_body_72_hours,number)
        if not send_sms:
            raise ModuleNotFoundError(
                "sms not send and not marked in sheet"
            )
            
        logger.info('Sending Sms to Name : {}, Number : {}'.format(name, number))
        sent_sms = ss.mark_sms_sent(number, 72)
        

    #adding smsbody for 24hrs list
    sms_body_24_hours = "24 hours messgae template"
    for number in reminder_list_24_hours:
        name = reminder_list_24_hours[number]
        send_sms=send_Sms(creds.twilio_account_sid,creds.twilio_token,creds.from_num,sms_body_24_hours,number)
        if not send_sms:
            raise ModuleNotFoundError(
                "sms not send and not marked in sheet"
            )
        logger.info('Sending Sms to Name : {}, Number : {}'.format(name, number))   
        sent_sms = ss.mark_sms_sent(number, 24)
    
    return None
