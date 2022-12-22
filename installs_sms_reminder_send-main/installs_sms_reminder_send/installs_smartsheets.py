import smartsheet
import phonenumbers

from installs_sms_reminder_send.exceptions import (
    FilterNotFoundError, ColumnNotFoundError, NumberNotFoundError, InvalidReminderHoursError, InvalidPhoneNumberError
)
from installs_sms_reminder_send import logger, opsgenie


class Smartsheet:

    def __init__(self, sheet_id: str, sheet_token: str):
        self.sheet_id = sheet_id
        self.sheet_token = sheet_token

        # Initialise smartsheet client
        self.client = smartsheet.Smartsheet(self.sheet_token)
        self.client.errors_as_exceptions(True)

        # Get filters for 24 and 72 hours reminders
        self.filter_24_hours_id, self.filter_72_hours_id = self._get_filters()

        # Get column IDs for end user name, phone number and for recording 24 and 72 hours sms sent
        # This also works as a validation before starting the process to send sms
        self.eu_name_column_id, \
        self.eu_phone_column_id, \
        self.reminder_sent_24_hours_column_id, \
        self.reminder_sent_72_hours_column_id = self._column_ids()

    def _get_filters(self) -> tuple[int, int]:
        """
        Gets filter IDs for filters setup on a smartsheet for 24 and 72 hours reminder
        :return: filter_24_hours_id, filter_72_hours_id
        :raises FilterNotFoundError - If either or both of the filters not found in smartsheet
        """
        filters = self.client.Sheets.list_filters(self.sheet_id)
        filter_72_hours_id = None
        filter_24_hours_id = None
        for sheet_filter in filters.data:
            if sheet_filter.name == '72_hours_reminder':
                filter_72_hours_id = sheet_filter.id_  # This is not a type, the attribute is named id_
            elif sheet_filter.name == '24_hours_reminder':
                filter_24_hours_id = sheet_filter.id_

        if filter_72_hours_id is None or filter_24_hours_id is None:
            raise FilterNotFoundError(
                'Filter not found. Please make sure both 72 and 24 hours reminder filter are on '
                'smartsheet and name as 72_hours_reminder and 24_hours_reminder'
            )

        return filter_24_hours_id, filter_72_hours_id

    def _column_ids(self) -> tuple[int, int, int, int]:
        """
        Gets smartsheet column IDs for end user name, phone number and columns for 24 and 72 hours sms sent status
        :return: end user name column id, end user telephone column id, 24 hours sms sent, 72 hours sms sent
        :raises ColumnNotFoundError - If any of columns are missing
        """

        name_column_id = None
        phone_column_id = None
        reminder_sent_24_hours_column_id = None
        reminder_sent_72_hours_column_id = None

        cols = self.client.Sheets.get_columns(self.sheet_id)
        cols = cols.result
        for col in cols:
            if col.title == 'End User':
                name_column_id = col.id_
            elif col.title == 'Telephone Number':
                phone_column_id = col.id_
            elif col.title == '24 hours reminder sent':
                reminder_sent_24_hours_column_id = col.id_
            elif col.title == '72 hours reminder sent':
                reminder_sent_72_hours_column_id = col.id_

        if name_column_id is None or phone_column_id is None \
                or reminder_sent_24_hours_column_id is None or reminder_sent_72_hours_column_id is None:
            raise ColumnNotFoundError(
                'Column missing. Please make sure following columns are on smartsheet'
                'End User, Telephone number, 24 hours reminder sent and 72 hours reminder sent'
            )

        return name_column_id, phone_column_id, reminder_sent_24_hours_column_id, reminder_sent_72_hours_column_id

    def column_id_by_name(self, column_name: str):
        """ Returns column ID by column name. Returns 0 is no column found """

        cols = self.client.Sheets.get_columns(self.sheet_id)
        cols = cols.result
        for col in cols:
            if col.title == column_name:
                return col.id_
        return 0

    def _fetch_smartsheet_data(self, filter_id: int):
        """
        Fetches the smartsheet data applying the filter
        :return: dict of end user phone number and names
        """

        sheet = self.client.Sheets.get_sheet(self.sheet_id, filter_id=filter_id)
        sheet_dict = sheet.to_dict()
        sheet_rows: list = sheet_dict['rows']

        not_filtered_rows = []
        for row in sheet_rows:
            if not row['filteredOut']:  # If a row is filtered due to the applied filter then this is True
                not_filtered_rows.append(row['cells'])  # cells is a list
        logger.info(f'Not filtered rows: {len(not_filtered_rows)}')

        # So we should have a nested list of only containing the not filtered rows
        result = {}
        for not_filtered in not_filtered_rows:
            # The inner list contains a dict
            eu_name = None
            eu_telephone = None
            for cell in not_filtered:
                if cell['columnId'] == self.eu_name_column_id:
                    eu_name = cell['displayValue']
                elif cell['columnId'] == self.eu_phone_column_id:
                    eu_telephone = cell['displayValue']
            result[str(eu_telephone)] = eu_name
        return result

    @staticmethod
    def _validate_phone_numbers(data: dict) -> tuple[dict, list]:
        """
        Validates phone numbers and converts them to E.164 format. Un-validated phone numbers are removed from output
        :param data: Dict with phone numbers (str) as key and name as value
        :return: tuple of Dict with validated phone numbers (str) in E.164 format as key and name as value
        and a list of not valid phone numbers
        """

        result = {}
        not_valid_numbers = []
        for phone, name in data.items():
            num = phonenumbers.parse(phone, 'GB')
            if not phonenumbers.is_valid_number(num):
                not_valid_numbers.append(phone)
                continue

            result[phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164)] = name

        return result, not_valid_numbers

    @staticmethod
    def _raise_not_valid_num_alert(nums: list):

        opsgenie.create_alert({
            'message': 'Invalid phone numbers for install sms reminder',
            'priority': 'P3',
            'description': f'{nums}',
            'tags': ['smartsheet', 'installs', 'sms_reminder'],
            'alias': f'{len(nums)}-{nums}'
        })
        return

    def reminder_list_72_hours(self):
        """
        Returns a dict of phone numbers and names to whom a sms reminder needs to sent in 72 hours

        :return: Dict with phone numbers (str) as key and name as value
        Phone numbers are in the E.164 format
        Example:
            {
                "+4477733338883": "Mr John Doe"
            }
        """
        logger.info('Fetching 72 hours reminder data from smartsheet')
        eu_data = self._fetch_smartsheet_data(filter_id=self.filter_72_hours_id)
        logger.info(f'{len(eu_data)} sms reminders to send for 72 hours')
        # validate the phone numbers
        logger.info('Validating phone numbers')
        valid_data, not_valid_numbers = self._validate_phone_numbers(eu_data)

        if not_valid_numbers:
            logger.error(f'{len(not_valid_numbers)} invalid phone numbers. These are: {not_valid_numbers}')

            self._raise_not_valid_num_alert(not_valid_numbers)

        return valid_data

    def reminder_list_24_hours(self):
        """
        Returns a dict of phone numbers and names to whom a sms reminder needs to sent in 72 hours

        :return: Dict with phone numbers (str) as key and name as value
        Phone numbers are in the E.164 format
        Example:
            {
                "+4477733338883": "Mr John Doe"
            }
        """
        logger.info('Fetching 24 hours reminder data from smartsheet')
        eu_data = self._fetch_smartsheet_data(filter_id=self.filter_24_hours_id)
        logger.info(f'{len(eu_data)} sms reminders to send for 24 hours')

        # validate the phone numbers
        valid_data, not_valid_numbers = self._validate_phone_numbers(eu_data)

        if not_valid_numbers:
            logger.error(f'{len(not_valid_numbers)} invalid phone numbers. These are: {not_valid_numbers}')

            self._raise_not_valid_num_alert(not_valid_numbers)

        return valid_data

    def mark_sms_sent(self, phone_number: str, reminder_hours: int) -> None:
        """
        Marks the sms sent column in the smartsheet
        :param phone_number: Phone number in the E.164 format
        :param reminder_hours: Whether sms was sent for 24 or 72 hours reminder
        :raises NumberNotFoundError - If phone number not found in smartsheet
        :raises InvalidPhoneNumberError - If the phone number provided is not a valid phone number
        :raises InvalidReminderHoursError - If the reminder hours are not valid. Valid values: 24, 72
        """

        # Convert the phone number to national format
        gb_num = phonenumbers.parse(phone_number, 'GB')

        if not phonenumbers.is_valid_number(gb_num):
            raise InvalidPhoneNumberError(f'Invalid phone number: {phone_number}')

        # Search smartsheet for the number. Looks like the search only works if there is full match.
        search_sheet = self.client.Sheets.search_sheet(self.sheet_id, f'0{gb_num.national_number}')

        search_dict = search_sheet.to_dict()

        if search_dict['totalCount'] == 0:
            raise NumberNotFoundError(f'Phone number: {phone_number} not found in smartsheet')

        search_result: list[dict] = search_dict['results']  # objectId in the dict is the row id

        if reminder_hours == 72:
            column_id = self.reminder_sent_72_hours_column_id
        elif reminder_hours == 24:
            column_id = self.reminder_sent_24_hours_column_id
        else:
            raise InvalidReminderHoursError(f'Invalid reminder hour: {reminder_hours}. Valid values: 24, 72')

        for result in search_result:
            # Build new cell value
            new_cell = smartsheet.models.Cell()
            new_cell.column_id = column_id
            new_cell.value = True
            new_cell.strict = False

            # Build the row to update
            new_row = smartsheet.models.Row()
            new_row.id = result['objectId']
            new_row.cells.append(new_cell)

            # Update rows
            updated_row = self.client.Sheets.update_rows(self.sheet_id, [new_row])

        return