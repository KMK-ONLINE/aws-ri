# AWS-RI
A Python script to calculate how many reserved instances to buy on AWS.

# Requirements
- SES successfully configured to send email - https://aws.amazon.com/documentation/ses
- Lambda to run the python script every month. You need to create a new role to allow Lambda to send email through SES - https://aws.amazon.com/documentation/lambda
