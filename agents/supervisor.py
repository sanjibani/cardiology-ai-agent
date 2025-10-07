from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import Dict, Any
from models.state import AgentState
import time


class SupervisorAgent:
    """Enhanced LangGraph Supervisor Agent with reactive routing capabilities"""
    
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.1)
        self.name = "supervisor"
        
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are the Supervisor Agent for a cardiology AI multi-agent system.
            
            Your role is to analyze incoming patient queries and intelligently route them to the most appropriate specialist agent.
            
            Available specialist agents:
            1. TRIAGE_AGENT: 
               - Emergency cardiac symptoms (chest pain, shortness of breath, palpitations)
               - Symptom assessment and risk stratification
               - Emergency escalation protocols
               
            2. APPOINTMENT_AGENT:
               - Scheduling new appointments
               - Rescheduling existing appointments  
               - Appointment-related queries and calendar management
               
            3. VIRTUAL_ASSISTANT:
               - General cardiology education and information
               - Medication questions and adherence
               - Post-procedure care instructions
               - Lifestyle and prevention advice
               
            4. CLINICAL_DOCS:
               - Medical record requests
               - Test result explanations
               - Report generation and documentation
               - Clinical summary requests
            
            Analysis requirements:
            1. Determine urgency level: EMERGENCY, URGENT, or ROUTINE
            2. Identify primary intent and required expertise
            3. Route to the most appropriate agent
            4. Provide clear reasoning for your routing decision
            
            Respond with a structured decision including:
            - AGENT: The chosen agent name
            - URGENCY: The urgency level
            - REASONING: Brief explanation of routing logic
            - CONTEXT: Any important context for the receiving agent"""),
            MessagesPlaceholder(variable_name="messages"),
            HumanMessage(content="Analyze the above query and provide your routing decision.")
        ])
    
    def __call__(self, state: AgentState) -> AgentState:
        """Process state and route to appropriate agent"""
        start_time = time.time()
        
        # Get the latest message for analysis
        if not state.get("messages"):
            return self._create_error_response(state, "No messages to process")
        
        last_message = state["messages"][-1]
        query_content = last_message.content if hasattr(last_message, 'content') else str(last_message)
        
        # Prepare context for routing decision
        context_info = {
            "patient_id": state.get("patient_id"),
            "session_context": state.get("session_context", {}),
            "conversation_history": len(state.get("conversation_history", [])),
            "previous_agent": state.get("current_agent"),
            "urgency_level": state.get("urgency_level")
        }
        
        # Create enhanced prompt with context
        enhanced_messages = state["messages"] + [
            HumanMessage(content=f"""
            Current Query: {query_content}
            
            Context Information:
            - Patient ID: {context_info['patient_id'] or 'Not provided'}
            - Session Context: {context_info['session_context']}
            - Previous Agent: {context_info['previous_agent'] or 'None'}
            - Current Urgency: {context_info['urgency_level'] or 'Not assessed'}
            
            Provide routing decision with the following format:
            AGENT: [agent_name]
            URGENCY: [urgency_level]
            REASONING: [explanation]
            CONTEXT: [context_for_receiving_agent]
            """)
        ]
        
        # Get routing decision from LLM
        try:
            chain = self.prompt | self.llm
            response = chain.invoke({"messages": enhanced_messages})
            routing_decision = self._parse_routing_response(response.content)
            
            # Update state with routing decision
            processing_time = time.time() - start_time
            
            updated_state = {
                **state,
                "current_agent": "supervisor",
                "next_agent": routing_decision["agent"],
                "urgency_level": routing_decision["urgency"],
                "original_query": query_content,
                "session_context": {
                    **state.get("session_context", {}),
                    "supervisor_reasoning": routing_decision["reasoning"],
                    "routing_context": routing_decision["context"]
                },
                "agent_transitions": state.get("agent_transitions", []) + [{
                    "from_agent": state.get("current_agent", "user"),
                    "to_agent": routing_decision["agent"],
                    "timestamp": time.time(),
                    "reasoning": routing_decision["reasoning"]
                }],
                "processing_time": processing_time,
                "confidence_scores": {
                    **state.get("confidence_scores", {}),
                    "routing_confidence": routing_decision.get("confidence", 0.8)
                },
                "messages": state["messages"] + [AIMessage(
                    content=f"Routing to {routing_decision['agent']} - {routing_decision['reasoning']}"
                )]
            }
            
            return updated_state
            
        except Exception as e:
            return self._create_error_response(state, f"Routing error: {str(e)}")
    
    def _parse_routing_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured routing decision"""
        
        # Initialize with defaults
        decision = {
            "agent": "VIRTUAL_ASSISTANT",  # Default fallback
            "urgency": "ROUTINE",
            "reasoning": "Default routing due to parsing error",
            "context": "",
            "confidence": 0.5
        }
        
        try:
            lines = response.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if line.startswith("AGENT:"):
                    agent = line.split(":", 1)[1].strip()
                    if agent in ["TRIAGE_AGENT", "APPOINTMENT_AGENT", "VIRTUAL_ASSISTANT", "CLINICAL_DOCS"]:
                        decision["agent"] = agent
                        decision["confidence"] = 0.9
                        
                elif line.startswith("URGENCY:"):
                    urgency = line.split(":", 1)[1].strip()
                    if urgency in ["EMERGENCY", "URGENT", "ROUTINE"]:
                        decision["urgency"] = urgency
                        
                elif line.startswith("REASONING:"):
                    decision["reasoning"] = line.split(":", 1)[1].strip()
                    
                elif line.startswith("CONTEXT:"):
                    decision["context"] = line.split(":", 1)[1].strip()
            
            # Fallback parsing for unstructured responses
            if decision["agent"] == "VIRTUAL_ASSISTANT" and decision["confidence"] == 0.5:
                response_upper = response.upper()
                
                if any(word in response_upper for word in ["CHEST PAIN", "EMERGENCY", "URGENT", "BREATHING"]):
                    decision["agent"] = "TRIAGE_AGENT"
                    decision["urgency"] = "URGENT"
                    decision["confidence"] = 0.7
                elif any(word in response_upper for word in ["APPOINTMENT", "SCHEDULE", "RESCHEDULE"]):
                    decision["agent"] = "APPOINTMENT_AGENT"
                    decision["confidence"] = 0.7
                elif any(word in response_upper for word in ["DOCUMENT", "RECORD", "REPORT", "TEST"]):
                    decision["agent"] = "CLINICAL_DOCS"
                    decision["confidence"] = 0.7
                    
        except Exception as e:
            decision["reasoning"] = f"Parsing error: {str(e)}, using fallback routing"
            
        return decision
    
    def _create_error_response(self, state: AgentState, error_message: str) -> AgentState:
        """Create error response state"""
        return {
            **state,
            "current_agent": "supervisor",
            "next_agent": "END",
            "requires_human_review": True,
            "messages": state.get("messages", []) + [AIMessage(
                content=f"Supervisor Error: {error_message}. Please contact support."
            )],
            "session_context": {
                **state.get("session_context", {}),
                "error": error_message
            }
        }