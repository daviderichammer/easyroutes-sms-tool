# EasyRoutes API Research

## Authentication
- Endpoint: `POST https://easyroutes.roundtrip.ai/api/2024-07/authenticate`
- Requires: `clientId` and `clientSecret`
- Returns: `accessToken` with expiration time

## Key API Endpoints

### ListRoutes
- `GET https://easyroutes.roundtrip.ai/api/2024-07/routes`
- Query parameters: limit, sortKey, timestampStart, timestampEnd, includeArchived, cursor
- Returns: Array of Route objects

### GetRoute
- `GET https://easyroutes.roundtrip.ai/api/2024-07/routes/{id}`
- Returns: Single Route object with all stops

### GetRouteStop
- `GET https://easyroutes.roundtrip.ai/api/2024-07/routes/{route_id}/stops/{stop_id}`
- Returns: Single RouteStop object

## Data Structures

### Route Object
- `id`: Route ID
- `name`: Route name
- `driver`: Driver object
- `stops`: Array of RouteStop objects
- `createdAt`, `updatedAt`, `archivedAt`, `scheduledFor`: Timestamps
- `optimized`: Boolean

### RouteStop Object
- `id`: Stop ID
- `type`: StopType (DELIVERY, BREAK, PICKUP, TASK)
- `deliveryStatus`: DeliveryStatus enum
- `breakStatus`: BreakStatus enum
- `updatedAt`: Timestamp of last status update
- `address`: Address object
- `contact`: Contact object with phone number
- `note`: Top-level note for the stop

### DeliveryStatus Values
- `UNKNOWN`: Unknown delivery status (not marked as ready)
- `DELIVERED`: Stop was delivered ✅ (COMPLETED)
- `OUT_FOR_DELIVERY`: Stop is out for delivery ❌ (INCOMPLETE)
- `ATTEMPTED_DELIVERY`: Stop delivery was attempted ❌ (INCOMPLETE)
- `READY_FOR_DELIVERY`: Stop is ready for delivery ❌ (INCOMPLETE)

## Incomplete Stops Logic
Stops that are NOT completed are those with deliveryStatus:
- UNKNOWN
- OUT_FOR_DELIVERY
- ATTEMPTED_DELIVERY
- READY_FOR_DELIVERY

Only stops with deliveryStatus = "DELIVERED" are considered complete.

## Contact Information
RouteStop.contact object contains phone number for SMS delivery.



## Twilio SMS API Research

### Authentication
- Account SID: `your_twilio_account_sid_here` (provided)
- Auth Token: `your_twilio_auth_token_here` (provided)
- Environment variables: `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN`

### API Endpoint
- `POST https://api.twilio.com/2010-04-01/Accounts/{AccountSid}/Messages.json`

### Python SDK Usage
```python
from twilio.rest import Client

# Authentication
account_sid = os.environ["TWILIO_ACCOUNT_SID"]
auth_token = os.environ["TWILIO_AUTH_TOKEN"]
client = Client(account_sid, auth_token)

# Send SMS
message = client.messages.create(
    body="Your custom message text here",
    from_="+15017122661",  # Twilio phone number
    to="+15558675310",     # Recipient phone number
)
```

### Required Parameters
- `body`: The text message content
- `from_`: Twilio phone number (sender)
- `to`: Recipient phone number in E.164 format
- Authentication via Account SID and Auth Token

### Installation
- Install Twilio Python SDK: `pip install twilio`

## Integration Plan

### Tool Architecture
1. **EasyRoutes Integration**
   - Authenticate with EasyRoutes API using client credentials
   - Fetch routes using ListRoutes endpoint
   - For each route, get detailed route info including stops
   - Filter stops where deliveryStatus != "DELIVERED"

2. **Twilio Integration**
   - Use provided Twilio credentials
   - Send custom SMS to each incomplete stop's contact phone number
   - Handle phone number formatting (E.164)

3. **Tool Features**
   - Command-line interface for easy usage
   - Configuration file for API credentials
   - Custom message templates
   - Logging and error handling
   - Dry-run mode for testing

