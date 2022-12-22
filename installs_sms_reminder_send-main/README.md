# installs_sms_reminder_send
Sends SMS reminders to end users for upcoming installs
The SMS receive functionality is in a different repo and can be found here: https://github.com/Full-Fibre/install_sms_reminder_receive

<!-- TOC -->
  * [Deployment](#deployment)
  * [Workflow](#workflow)
    * [SMS send](#sms-send)
  * [Config management](#config-management)
<!-- TOC -->

## Deployment
This is deployed as a scheduled lambda function. Basically this is running on a schedule. Schedule is set to 
every 8 hours. This can be changed in AWS lambda console or in the `template.yaml` file. 

It has been deployed to AWS stack `installs_sms_reminder`. You can google AWS cloudformation and stack to gain more
understanding about it. It is essentially IaaC (infrastructure as a code) service. 
We have not done anything fancy to make use on this. It is deployed using `AWS SAM CLI` which handled pretty much 
everything. 

To deploy it you need aws sam cli. Please google and read up on it on how to use it. 

## Workflow
The workflow for this is pretty straight forward. The app is abit static, in a sense that changing SMS reminder interval
would require tiny amount of rework. And the app relies on filters that are setup on smartsheet. So if someone changes
those filters, stuff could break. This also provide flexibilty that we can update the filters on smartsheet to control
who sms will be sent to. 
The filters on called
- 24_hours_reminder
- 72_hours_reminder

The name needs to be exactly the same, it is case sensitive. The app looks for these filters. 

### SMS send
Periodic execution at an interval of 8 hours. 

```plantuml
actor end_user
participant code
participant twilio
participant smartsheet

code -> smartsheet: Get list of install date and customer details
smartsheet -> code: response
code -> twilio: send SMS 
twilio -> end_user: send SMS
end_user -> twilio: response
twilio -> code: response
code -> smartsheet: Mark SMS sent
smartsheet -> code: response
```

## Config management
pydantic is used for config management. All config params are passed as env variables. 


|     |     |     |     |
|-----|-----|-----|-----|
|     |     |     |     |
