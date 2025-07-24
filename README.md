# EasyRoutes SMS Notification Tool

A Python-based command-line tool that integrates with EasyRoutes delivery management platform and Twilio SMS service to automatically send custom text messages to customers with incomplete delivery stops.

## Overview

This tool streamlines customer communication by automatically identifying delivery stops that have not been completed and sending personalized SMS notifications to the associated customers. It eliminates manual effort in tracking delivery status and customer communication while improving customer satisfaction through proactive updates.

## Features

- **Automated Route Processing**: Retrieves route data from EasyRoutes API and identifies incomplete stops
- **Smart Filtering**: Only targets stops with delivery status other than "DELIVERED"
- **Custom Messaging**: Configurable message templates with dynamic content insertion
- **Reliable Delivery**: Integrates with Twilio SMS API for reliable message delivery
- **Error Handling**: Comprehensive error handling and retry logic for production reliability
- **Dry Run Mode**: Test functionality without sending actual messages
- **Detailed Logging**: Comprehensive logging for monitoring and troubleshooting
- **Security**: Secure credential management using environment variables

## Quick Start

### Prerequisites

- Python 3.8 or later
- EasyRoutes API credentials (client ID and secret)
- Twilio account with SMS capabilities
- Ubuntu 20.04 LTS or later (recommended)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd easyroutes-sms-tool
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API credentials
```

5. Run the tool:
```bash
python src/main.py
```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# EasyRoutes API Configuration
EASYROUTES_CLIENT_ID=your_client_id_here
EASYROUTES_CLIENT_SECRET=your_client_secret_here

# Twilio SMS Configuration  
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_FROM_NUMBER=+1234567890

# Application Configuration
LOG_LEVEL=INFO
DRY_RUN=false
```

### Message Templates

Customize SMS message templates in `config/message_templates.yaml`:

```yaml
templates:
  default:
    body: |
      Hello {customer_name},
      
      Your delivery to {address} is currently {status_message}.
      
      If you have any questions, please contact us.
      
      Thank you!
```

## Usage

### Basic Usage

```bash
# Send messages to all incomplete stops
python src/main.py

# Dry run mode (test without sending)
python src/main.py --dry-run

# Process specific routes only
python src/main.py --route-ids route1,route2

# Use custom message template
python src/main.py --template urgent
```

### Command Line Options

- `--dry-run`: Test mode - show what would be sent without actually sending
- `--route-ids`: Comma-separated list of specific route IDs to process
- `--template`: Message template name to use (default: "default")
- `--log-level`: Logging level (DEBUG, INFO, WARN, ERROR)
- `--config`: Path to custom configuration file

## Project Structure

```
easyroutes-sms-tool/
├── src/                          # Source code
│   ├── main.py                   # Main application entry point
│   ├── config/                   # Configuration management
│   ├── clients/                  # API client modules
│   ├── models/                   # Data models
│   └── utils/                    # Utility functions
├── tests/                        # Test suite
├── config/                       # Configuration files
├── docs/                         # Additional documentation
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variables template
└── README.md                     # This file
```

## API Integration

### EasyRoutes API

- **Authentication**: OAuth2 client credentials flow
- **Endpoints Used**:
  - `POST /authenticate` - Get access token
  - `GET /routes` - List routes
  - `GET /routes/{id}` - Get route details with stops

### Twilio SMS API

- **Authentication**: Account SID and Auth Token
- **Endpoints Used**:
  - `POST /Messages` - Send SMS messages

## Development

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=src

# Run specific test file
python -m pytest tests/test_easyroutes.py
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

## Deployment

### Production Deployment

1. Set up Ubuntu server with Python 3.8+
2. Clone repository and install dependencies
3. Configure environment variables securely
4. Set up systemd service for automated execution
5. Configure log rotation and monitoring

See `docs/deployment.md` for detailed deployment instructions.

### Docker Deployment

```bash
# Build image
docker build -t easyroutes-sms-tool .

# Run container
docker run --env-file .env easyroutes-sms-tool
```

## Monitoring and Logging

The tool provides comprehensive logging for operational monitoring:

- **Application logs**: Execution status, errors, and performance metrics
- **API logs**: Request/response details for troubleshooting
- **Message logs**: SMS delivery status and results
- **Error logs**: Detailed error information for debugging

Logs are written to both console and file outputs with configurable levels and rotation policies.

## Security

- **Credential Security**: All sensitive credentials stored in environment variables
- **Data Protection**: Customer phone numbers and message content filtered from logs
- **Communication Security**: All API communication uses HTTPS
- **Access Control**: Minimal required permissions for execution

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Verify API credentials and network connectivity
2. **Message Delivery Failures**: Check phone number formatting and Twilio account status
3. **Rate Limiting**: Tool includes automatic retry logic with exponential backoff
4. **Network Issues**: Verify internet connectivity and firewall settings

See `docs/troubleshooting.md` for detailed troubleshooting guide.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Check the troubleshooting guide
- Review the technical specifications
- Contact the development team

## Documentation

- [Project Plan](easyroutes_sms_tool_project_plan.md) - Comprehensive project planning document
- [Technical Specifications](technical_specifications.md) - Detailed technical architecture and implementation
- [API Research](easyroutes_api_research.md) - EasyRoutes and Twilio API analysis
- [Todo List](todo.md) - Implementation progress tracking

