# EasyRoutes SMS Tool - Technical Specifications

**Author:** Manus AI  
**Date:** July 24, 2025  
**Version:** 1.0  

## System Overview

The EasyRoutes SMS Tool is a Python-based command-line application designed to integrate with the EasyRoutes delivery management platform and Twilio SMS service. The tool automatically identifies incomplete delivery stops and sends customized SMS notifications to customers, streamlining communication workflows and improving customer service efficiency.

## Technical Architecture

### Application Structure

```
easyroutes-sms-tool/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Main application entry point
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py         # Configuration management
│   │   └── templates.py        # Message templates
│   ├── clients/
│   │   ├── __init__.py
│   │   ├── easyroutes.py       # EasyRoutes API client
│   │   └── twilio_client.py    # Twilio SMS client
│   ├── models/
│   │   ├── __init__.py
│   │   ├── route.py            # Route data models
│   │   └── message.py          # Message data models
│   └── utils/
│       ├── __init__.py
│       ├── logger.py           # Logging utilities
│       ├── validators.py       # Data validation
│       └── formatters.py       # Data formatting utilities
├── tests/
│   ├── __init__.py
│   ├── test_easyroutes.py
│   ├── test_twilio.py
│   └── test_integration.py
├── config/
│   ├── config.yaml             # Application configuration
│   └── message_templates.yaml  # SMS message templates
├── requirements.txt            # Python dependencies
├── setup.py                    # Package setup
├── README.md                   # Project documentation
└── .env.example                # Environment variables template
```

### Core Components

#### Configuration Management (config/settings.py)

The configuration management system handles application settings, credential loading, and runtime parameter validation. It supports multiple configuration sources with appropriate precedence rules.

```python
class Config:
    def __init__(self):
        self.easyroutes_client_id = os.getenv('EASYROUTES_CLIENT_ID')
        self.easyroutes_client_secret = os.getenv('EASYROUTES_CLIENT_SECRET')
        self.twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_from_number = os.getenv('TWILIO_FROM_NUMBER')
        
    def validate(self):
        required_vars = [
            'easyroutes_client_id', 'easyroutes_client_secret',
            'twilio_account_sid', 'twilio_auth_token', 'twilio_from_number'
        ]
        missing = [var for var in required_vars if not getattr(self, var)]
        if missing:
            raise ConfigurationError(f"Missing required environment variables: {missing}")
```

#### EasyRoutes API Client (clients/easyroutes.py)

The EasyRoutes client manages authentication, route data retrieval, and stop filtering logic. It implements automatic token renewal and comprehensive error handling.

```python
class EasyRoutesClient:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://easyroutes.roundtrip.ai/api/2024-07"
        self.access_token = None
        self.token_expires_at = None
        
    async def authenticate(self):
        """Authenticate and obtain access token"""
        auth_data = {
            "clientId": self.client_id,
            "clientSecret": self.client_secret
        }
        response = await self._post("/authenticate", auth_data)
        self.access_token = response["accessToken"]
        self.token_expires_at = datetime.now() + timedelta(seconds=response["expiresInSeconds"])
        
    async def get_routes(self, include_archived=False, limit=20):
        """Retrieve routes with pagination support"""
        await self._ensure_authenticated()
        params = {
            "query.limit": limit,
            "query.includeArchived": include_archived
        }
        return await self._get("/routes", params)
        
    async def get_incomplete_stops(self, route_id):
        """Get stops that are not delivered"""
        route = await self.get_route(route_id)
        incomplete_stops = []
        
        for stop in route.get("stops", []):
            delivery_status = stop.get("deliveryStatus")
            if delivery_status != "DELIVERED":
                incomplete_stops.append(stop)
                
        return incomplete_stops
```

#### Twilio SMS Client (clients/twilio_client.py)

The Twilio client handles SMS message delivery with error handling, rate limiting compliance, and delivery status tracking.

```python
class TwilioSMSClient:
    def __init__(self, account_sid, auth_token, from_number):
        self.client = Client(account_sid, auth_token)
        self.from_number = from_number
        
    async def send_message(self, to_number, message_body):
        """Send SMS message with error handling"""
        try:
            # Validate and format phone number
            formatted_number = self._format_phone_number(to_number)
            
            message = self.client.messages.create(
                body=message_body,
                from_=self.from_number,
                to=formatted_number
            )
            
            return {
                "success": True,
                "message_sid": message.sid,
                "status": message.status,
                "to": formatted_number
            }
            
        except TwilioException as e:
            logger.error(f"Twilio error sending to {to_number}: {e}")
            return {
                "success": False,
                "error": str(e),
                "to": to_number
            }
            
    def _format_phone_number(self, phone_number):
        """Format phone number to E.164 standard"""
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone_number)
        
        # Add country code if missing (assume US +1)
        if len(digits_only) == 10:
            return f"+1{digits_only}"
        elif len(digits_only) == 11 and digits_only.startswith('1'):
            return f"+{digits_only}"
        else:
            return f"+{digits_only}"
```

### Data Models

#### Route Model (models/route.py)

```python
@dataclass
class RouteStop:
    id: str
    delivery_status: str
    contact: dict
    address: dict
    note: str = ""
    
    @property
    def is_incomplete(self) -> bool:
        return self.delivery_status != "DELIVERED"
        
    @property
    def phone_number(self) -> str:
        return self.contact.get("phone", "")
        
    @property
    def customer_name(self) -> str:
        return self.contact.get("name", "")

@dataclass
class Route:
    id: str
    name: str
    stops: List[RouteStop]
    driver: dict
    scheduled_for: str
    
    @property
    def incomplete_stops(self) -> List[RouteStop]:
        return [stop for stop in self.stops if stop.is_incomplete]
```

#### Message Model (models/message.py)

```python
@dataclass
class SMSMessage:
    to_number: str
    body: str
    route_id: str
    stop_id: str
    template_name: str
    
@dataclass
class MessageResult:
    message: SMSMessage
    success: bool
    message_sid: str = None
    error: str = None
    timestamp: datetime = field(default_factory=datetime.now)
```

### Message Templates

The system supports configurable message templates with dynamic content insertion:

```yaml
# config/message_templates.yaml
templates:
  default:
    subject: "Delivery Update"
    body: |
      Hello {customer_name},
      
      Your delivery to {address} is currently {status_message}.
      
      If you have any questions, please contact us.
      
      Thank you!
      
  urgent:
    subject: "Urgent Delivery Update"
    body: |
      Hello {customer_name},
      
      We need to update you about your delivery to {address}.
      Current status: {status_message}
      
      Please contact us at your earliest convenience.
      
status_messages:
  UNKNOWN: "being processed"
  OUT_FOR_DELIVERY: "out for delivery"
  ATTEMPTED_DELIVERY: "attempted - we'll try again"
  READY_FOR_DELIVERY: "ready for delivery"
```

### Main Application Logic (main.py)

```python
async def main():
    """Main application entry point"""
    try:
        # Load configuration
        config = Config()
        config.validate()
        
        # Initialize clients
        easyroutes_client = EasyRoutesClient(
            config.easyroutes_client_id,
            config.easyroutes_client_secret
        )
        
        twilio_client = TwilioSMSClient(
            config.twilio_account_sid,
            config.twilio_auth_token,
            config.twilio_from_number
        )
        
        # Load message templates
        templates = MessageTemplates.load()
        
        # Process routes
        results = await process_routes(
            easyroutes_client,
            twilio_client,
            templates,
            config
        )
        
        # Generate report
        generate_report(results)
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)

async def process_routes(easyroutes_client, twilio_client, templates, config):
    """Process all routes and send messages to incomplete stops"""
    results = []
    
    # Get all routes
    routes_response = await easyroutes_client.get_routes()
    
    for route_data in routes_response.get("routes", []):
        route = Route.from_dict(route_data)
        
        logger.info(f"Processing route: {route.name} ({route.id})")
        
        # Process incomplete stops
        for stop in route.incomplete_stops:
            if not stop.phone_number:
                logger.warning(f"No phone number for stop {stop.id}")
                continue
                
            # Generate message
            message_body = templates.render(
                template_name="default",
                customer_name=stop.customer_name,
                address=stop.address.get("formatted", ""),
                status_message=templates.get_status_message(stop.delivery_status)
            )
            
            # Send message
            if not config.dry_run:
                result = await twilio_client.send_message(
                    stop.phone_number,
                    message_body
                )
                results.append(result)
                
                # Rate limiting
                await asyncio.sleep(1)
            else:
                logger.info(f"DRY RUN: Would send to {stop.phone_number}: {message_body}")
                
    return results
```

## API Integration Specifications

### EasyRoutes API Integration

#### Authentication Flow

1. POST to `/authenticate` with client credentials
2. Store access token and expiration time
3. Include token in Authorization header for subsequent requests
4. Automatically renew token before expiration

#### Route Data Retrieval

1. GET `/routes` to list available routes
2. For each route, extract stop information
3. Filter stops by delivery status
4. Extract contact information for SMS delivery

#### Error Handling

- Network timeouts: Retry with exponential backoff
- Authentication errors: Re-authenticate and retry
- Rate limiting: Respect rate limits and retry after delay
- Invalid responses: Log error and continue with next item

### Twilio API Integration

#### Message Delivery Flow

1. Validate and format phone number to E.164 standard
2. Create message using Twilio SDK
3. Handle delivery status and errors
4. Log results for monitoring and reporting

#### Error Handling

- Invalid phone numbers: Log error and skip
- Rate limiting: Implement backoff and retry
- Service errors: Log and continue with next message
- Network errors: Retry with exponential backoff

## Security Specifications

### Credential Management

- All API credentials stored in environment variables
- No credentials in configuration files or code
- Secure credential loading with validation
- Support for credential rotation procedures

### Data Protection

- Customer phone numbers not logged in plain text
- Message content filtered from logs
- Secure communication using HTTPS only
- Minimal data retention policies

### Access Control

- Application runs under dedicated service account
- Minimal required system privileges
- Secure file permissions for configuration and logs
- Network access restricted to required endpoints

## Performance Specifications

### Throughput Requirements

- Process 100 routes within 5 minutes
- Send 1000 SMS messages within 10 minutes
- Support concurrent processing of multiple routes
- Respect API rate limits for both services

### Resource Requirements

- Memory usage under 512MB during normal operation
- CPU usage under 50% on single core
- Network bandwidth under 10Mbps
- Storage requirements under 1GB for logs and configuration

### Scalability Considerations

- Horizontal scaling through multiple instances
- Database-free architecture for simplicity
- Stateless operation for easy deployment
- Configuration-driven scaling parameters

## Testing Specifications

### Unit Testing

- Test coverage minimum 80% for all modules
- Mock external API dependencies
- Test error conditions and edge cases
- Automated test execution in CI/CD pipeline

### Integration Testing

- Test EasyRoutes API integration with test credentials
- Test Twilio SMS delivery with test numbers
- Validate end-to-end workflow execution
- Test error recovery and retry logic

### Performance Testing

- Load testing with high volume of routes and stops
- Memory usage monitoring during extended operation
- Network performance testing with API rate limits
- Concurrent execution testing

## Deployment Specifications

### System Requirements

- Ubuntu 20.04 LTS or later
- Python 3.8 or later
- Internet connectivity for API access
- 2GB RAM minimum, 4GB recommended
- 10GB storage for application and logs

### Installation Process

1. Clone repository to target directory
2. Create Python virtual environment
3. Install dependencies from requirements.txt
4. Configure environment variables
5. Validate configuration and connectivity
6. Run initial test execution

### Configuration Management

- Environment-specific configuration files
- Secure credential management procedures
- Configuration validation tools
- Change management procedures

## Monitoring and Logging

### Logging Strategy

- Structured logging with JSON format
- Configurable log levels (DEBUG, INFO, WARN, ERROR)
- Log rotation with size and time-based policies
- Integration with system logging infrastructure

### Monitoring Metrics

- Message delivery success rates
- API response times and error rates
- System resource utilization
- Application execution frequency and duration

### Alerting

- Critical error notifications
- API service availability monitoring
- Performance threshold alerts
- Operational anomaly detection

## Maintenance Procedures

### Regular Maintenance

- Log file cleanup and archival
- Dependency security updates
- Configuration review and updates
- Performance monitoring and optimization

### Troubleshooting

- Comprehensive error logging and categorization
- Diagnostic tools for API connectivity testing
- Performance profiling capabilities
- Operational runbooks for common issues

### Updates and Enhancements

- Version control and release management
- Backward compatibility considerations
- Testing procedures for updates
- Rollback procedures for failed deployments

