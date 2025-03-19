

# Application Support:
## CAN ANSWER:

- Provide the latest transaction times for mock-app-id
- Show me all the latest metric data for mock-app-id
- Show me information about the latest change that may have affected mock-app-id
- What is the average response time for transactions hitting the app mock-app-id?
- What are the IPs in the mock-app-id service that are causing the most issues?
- What errors are ocurring the most in mock-app-id?
- What is the latest error in mock-app-id?
- Are there any errors in July for mock-app-id?

## CANNOT ANSWER:
- Any IP related questions.

ISSUE: We do not have a good source of IP information.


- Are there any issues with the databases associated with the application mock-app-id?
- What is the status of the XYZ component of app mock-app-id?

ISSUE:
Needs data that is related between cmdb, incidents, logs, metrics, change requests.

- What is the IP address of the mock-app-id-02 component?

ISSUE:
Does not know that the IP is in the logs table.
We either need a better repository for this data, or to better catalog this data content for the LLM.

- Show me the last 10 http requests that hit the app mock-app-id

ISSUE:
We do not have this data.

- Did change ticket XYZ cause any issues with the application?

ISSUE:
We do not have this data.


# Opearations Support:
## CAN ANSWER:
- What are the up and downstream dependencies of mock-app-id?
- Did any services of mock-app-id have any errors in the last 48 hours?
- Which applications are experiencing the most errors in the last day?
- What is the maximum CPU usage of any service for application mock-app-id in the last 48 hrs?

## CANNOT ANSWER:
- What is the status of change ticket XYZ?

ISSUE: There are no change ticket IDs provided in the data

- Are there any issues with the databases associated with application mock-app-id that correlate with changes to the system?

ISSUE: We need data to represent this.