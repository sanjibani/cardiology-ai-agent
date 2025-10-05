# Cardiology AI Multi-Agent System

A sophisticated multi-agent system built with LangGraph and LangChain for cardiology patient triage, appointment booking, virtual assistance, and clinical documentation.

## Features

- **Intelligent Triage System**: AI-powered symptom assessment with emergency escalation
- **Appointment Management**: Automated scheduling with urgency-based prioritization  
- **Virtual Assistant**: Patient education and medication guidance
- **Clinical Documentation**: Automated report generation and documentation
- **Emergency Detection**: Real-time identification of critical symptoms with immediate response protocols

## System Architecture

The system uses LangGraph to orchestrate multiple specialized agents:

- **Supervisor Agent**: Routes queries to appropriate specialist agents
- **Triage Agent**: Assesses symptoms and determines urgency levels
- **Appointment Agent**: Handles scheduling and calendar management
- **Virtual Assistant Agent**: Provides patient education and support
- **Clinical Documentation Agent**: Generates clinical summaries and reports

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd cardiology-ai-agent
   ```

2. **Set up Python environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env file with your API keys and configuration
   ```

5. **Set up API keys**
   - Get an OpenAI API key from https://platform.openai.com/
   - Add your key to the `.env` file:
     ```
     OPENAI_API_KEY=your_api_key_here
     ```

## Usage

### Starting the Server

```bash
python main.py
```

The API will be available at `http://localhost:8002`

### API Documentation

Visit `http://localhost:8002/docs` for interactive API documentation.

### Key Endpoints

- **POST /chat** - Main chat interface for patient interactions
- **POST /triage** - Dedicated triage assessment endpoint
- **POST /appointment** - Appointment booking endpoint
- **GET /patient/{patient_id}** - Retrieve patient information
- **GET /patient/{patient_id}/appointments** - Get patient appointments

### Example Usage

```python
import requests

# Patient triage assessment
response = requests.post("http://localhost:8002/triage", json={
    "patient_id": "P001",
    "message": "I'm having chest pain that started an hour ago",
    "conversation_context": {}
})

# Appointment booking
response = requests.post("http://localhost:8002/appointment", json={
    "patient_id": "P001", 
    "message": "I need to schedule a follow-up appointment",
    "conversation_context": {}
})
```

## Project Structure

```
cardiology-ai-agent/
├── agents/                 # Agent implementations
│   ├── supervisor.py      # Query routing logic
│   ├── triage_agent.py    # Symptom assessment
│   ├── appointment_agent.py # Scheduling management
│   ├── virtual_assistant.py # Patient education
│   └── clinical_docs_agent.py # Documentation
├── models/                 # Data models and schemas
│   ├── schemas.py         # Pydantic models
│   └── state.py           # LangGraph state definitions
├── tools/                  # Utility tools
│   ├── patient_lookup.py  # Patient data access
│   ├── appointment_system.py # Scheduling system
│   ├── knowledge_base.py  # Medical knowledge access
│   └── emergency_escalation.py # Emergency handling
├── data/                   # Sample data and knowledge base
│   ├── cardiology_knowledge_base.json
│   └── sample_patient_data.json
├── main.py                 # FastAPI application
├── workflow.py             # LangGraph workflow definition
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Configuration

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8002)
- `DEBUG`: Enable debug mode (default: false)

### Customization

1. **Adding New Agents**: Create new agent classes in the `agents/` directory
2. **Extending Knowledge Base**: Update `data/cardiology_knowledge_base.json`
3. **Adding Tools**: Implement new tools in the `tools/` directory
4. **Modifying Workflow**: Update `workflow.py` to change agent routing logic

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black .
flake8 .
```

### Development Server

For development with auto-reload:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8002
```

## Security Considerations

- Never commit API keys to version control
- Use environment variables for sensitive configuration
- Implement proper authentication for production use
- Validate and sanitize all input data
- Use HTTPS in production environments

## Emergency Protocols

The system includes built-in emergency detection and escalation:

- **Critical symptoms** trigger immediate 911 alerts
- **Urgent conditions** route to same-day appointments
- **All emergencies** are logged for audit trails
- **Escalation protocols** follow medical best practices

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This system is for educational and demonstration purposes. It should not be used as a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of qualified health providers with questions about medical conditions.

## Support

For issues and questions:
- Create an issue in the GitHub repository
- Contact the development team
- Review the API documentation at `/docs`

## Roadmap

- [ ] Integration with real EHR systems
- [ ] Voice interface support
- [ ] Mobile application
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Integration with wearable devices