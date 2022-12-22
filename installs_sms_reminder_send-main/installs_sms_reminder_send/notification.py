import opsgenie_sdk

class Opsgenie:

    def __init__(self, opsgenie_api_key):
        self.conf = opsgenie_sdk.configuration.Configuration()
        self.conf.api_key['Authorization'] = opsgenie_api_key

        self.api_client = opsgenie_sdk.api_client.ApiClient(configuration=self.conf)
        self.alert_api = opsgenie_sdk.AlertApi(api_client=self.api_client)

    def create_alert(self, alert_body: dict):
        """
        Creates an alert on opsgenie. For details on alert_body please refer to;
        https://docs.opsgenie.com/docs/alert-api#section-create-alert
        and
        https://docs.opsgenie.com/docs/python-sdk-alert#create-alert
        """

        body = opsgenie_sdk.CreateAlertPayload(**alert_body)

        _ = self.alert_api.create_alert(create_alert_payload=body)