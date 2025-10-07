import asyncio
import time
from typing import Any, Dict, List, Literal

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from models.state import AgentState


@tool
def patient_education_tool(topic: str, urgency_level: str = "routine") -> Dict[str, Any]:
    """Provide patient education materials for cardiac health topics"""
    
    education_content = {
        "heart_healthy_lifestyle": {
            "title": "Heart-Healthy Lifestyle",
            "content": [
                "Aim for 150 minutes of moderate exercise weekly",
                "Follow a Mediterranean-style diet",
                "Limit sodium intake to less than 2,300mg daily",
                "Maintain a healthy weight (BMI 18.5-24.9)",
                "Don't smoke and limit alcohol consumption",
                "Manage stress through relaxation techniques"
            ],
            "confidence": 0.95
        },
        "medication_management": {
            "title": "Cardiac Medication Management",
            "content": [
                "Take medications exactly as prescribed",
                "Don't skip doses or stop without consulting your doctor",
                "Use pill organizers to track daily medications",
                "Know the names and purposes of all your medications",
                "Report side effects to your healthcare provider",
                "Keep an updated medication list with you"
            ],
            "confidence": 0.9
        },
        "symptom_monitoring": {
            "title": "Cardiac Symptom Monitoring",
            "content": [
                "Monitor blood pressure regularly if prescribed",
                "Track daily weight if heart failure history",
                "Note changes in exercise tolerance",
                "Watch for new or worsening shortness of breath",
                "Monitor for chest pain or discomfort patterns",
                "Keep a symptom diary for doctor visits"
            ],
            "confidence": 0.85
        },
        "emergency_recognition": {
            "title": "When to Seek Emergency Care",
            "content": [
                "Severe chest pain or pressure lasting >5 minutes",
                "Chest pain with nausea, sweating, or shortness of breath",
                "Sudden severe shortness of breath",
                "Loss of consciousness or near-fainting",
                "Rapid or irregular heartbeat with symptoms",
                "Call 911 immediately - don't drive yourself"
            ],
            "confidence": 0.98
        }
    }
    
    # Select appropriate content based on topic and urgency
    if topic in education_content:
        content = education_content[topic]
    elif urgency_level in ["emergency", "urgent"]:
        content = education_content["emergency_recognition"]
    else:
        content = education_content["heart_healthy_lifestyle"]
    
    return {
        "topic": topic,
        "title": content["title"],
        "educational_content": content["content"],
        "urgency_level": urgency_level,
        "confidence": content["confidence"],
        "follow_up_recommended": urgency_level in ["urgent", "moderate"]
    }


@tool
def lifestyle_recommendation_tool(patient_profile: Dict[str, Any]) -> Dict[str, Any]:
    """Generate personalized lifestyle recommendations"""
    
    risk_factors = patient_profile.get("risk_factors", [])
    current_symptoms = patient_profile.get("symptoms", [])
    
    recommendations = []
    
    # Exercise recommendations
    if "sedentary" in risk_factors or "obesity" in risk_factors:
        recommendations.append({
            "category": "exercise",
            "recommendation": "Start with 10-15 minutes daily walking, gradually increase",
            "priority": "high"
        })
    else:
        recommendations.append({
            "category": "exercise", 
            "recommendation": "Maintain 150 minutes moderate exercise weekly",
            "priority": "medium"
        })
    
    # Diet recommendations
    if "diabetes" in risk_factors or "hypertension" in risk_factors:
        recommendations.append({
            "category": "diet",
            "recommendation": "Follow DASH diet: low sodium, high fruits/vegetables",
            "priority": "high"
        })
    
    # Medication adherence
    if "medication_nonadherence" in risk_factors:
        recommendations.append({
            "category": "medication",
            "recommendation": "Use pill organizer and set daily reminders",
            "priority": "high"
        })
    
    return {
        "personalized_recommendations": recommendations,
        "assessment_confidence": 0.8,
        "follow_up_needed": len([r for r in recommendations if r["priority"] == "high"]) > 0
    }


@tool
def wellness_tracking_tool(tracking_goals: List[str]) -> Dict[str, Any]:
    """Provide wellness tracking guidance and tools"""
    
    tracking_methods = {
        "blood_pressure": {
            "frequency": "Daily if prescribed, weekly otherwise",
            "target_range": "Less than 130/80 mmHg for most adults",
            "tracking_tips": ["Same time daily", "Sit quietly 5 min before", "Use properly sized cuff"]
        },
        "weight": {
            "frequency": "Daily if heart failure, weekly otherwise", 
            "tracking_tips": ["Same time daily", "After bathroom, before breakfast", "Same scale and clothing"]
        },
        "exercise": {
            "frequency": "Daily activity logging",
            "tracking_tips": ["Note duration and intensity", "Track how you feel", "Include any symptoms"]
        },
        "symptoms": {
            "frequency": "As needed, daily if concerning",
            "tracking_tips": ["Rate severity 1-10", "Note triggers", "Include timing and duration"]
        }
    }
    
    relevant_methods = {goal: tracking_methods.get(goal, tracking_methods["symptoms"]) 
                       for goal in tracking_goals}
    
    return {
        "tracking_guidance": relevant_methods,
        "recommended_apps": ["MyFitnessPal", "Blood Pressure Monitor", "Heart Rate Tracker"],
        "tracking_confidence": 0.9
    }


class VirtualAssistantAgent:
    """Real LangGraph Virtual Assistant Agent with StateGraph for patient education"""
    
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.3)
        self.name = "virtual_assistant_agent"
        self.tools = [patient_education_tool, lifestyle_recommendation_tool, wellness_tracking_tool]
        
        # Build the LangGraph workflow
        self.graph = self._build_assistant_workflow()
    
    def _build_assistant_workflow(self) -> StateGraph:
        """Build the LangGraph StateGraph for virtual assistant"""
        
        # Create the StateGraph
        workflow = StateGraph(AgentState)
        
        # Add nodes for assistant workflow
        workflow.add_node("analyze_context", self._analyze_context_node)
        workflow.add_node("provide_education", self._provide_education_node)
        workflow.add_node("generate_recommendations", self._generate_recommendations_node)
        workflow.add_node("setup_tracking", self._setup_tracking_node)
        workflow.add_node("create_summary", self._create_summary_node)
        workflow.add_node("handle_error", self._handle_assistant_error_node)
        
        # Set entry point
        workflow.set_entry_point("analyze_context")
        
        # Define conditional routing
        workflow.add_conditional_edges(
            "analyze_context",
            self._route_after_context_analysis,
            {
                "provide_education": "provide_education",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "provide_education",
            self._route_after_education,
            {
                "generate_recommendations": "generate_recommendations",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "generate_recommendations", 
            self._route_after_recommendations,
            {
                "setup_tracking": "setup_tracking",
                "create_summary": "create_summary",
                "error": "handle_error"
            }
        )
        
        # Terminal routing
        workflow.add_edge("setup_tracking", "create_summary")
        workflow.add_edge("create_summary", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    def _analyze_context_node(self, state: AgentState) -> AgentState:
        """LangGraph Node: Analyze patient context and determine educational needs"""
        
        start_time = time.time()
        
        # Extract context from state
        urgency_level = state.get("urgency_level", "routine")
        triage_result = state.get("triage_result", {})
        patient_id = state.get("patient_id")
        
        # Determine educational priorities based on context
        if urgency_level in ["emergency", "urgent"]:
            education_focus = "emergency_recognition"
            priority_level = "high"
        elif urgency_level == "moderate":
            education_focus = "symptom_monitoring"
            priority_level = "medium"
        else:
            education_focus = "heart_healthy_lifestyle"
            priority_level = "routine"
        
        # Analyze recent messages for specific topics
        recent_messages = state.get("messages", [])[-3:] if state.get("messages") else []
        
        context_analysis = {
            "urgency_level": urgency_level,
            "education_focus": education_focus,
            "priority_level": priority_level,
            "patient_concerns": self._extract_patient_concerns(recent_messages),
            "educational_needs": self._determine_educational_needs(triage_result, urgency_level)
        }
        
        processing_time = time.time() - start_time
        
        return {
            **state,
            "context_analysis": context_analysis,
            "current_agent": "virtual_assistant_agent",
            "processing_time": processing_time,
            "next_action": "provide_education",
            "messages": state["messages"] + [AIMessage(
                content=f"Analyzing your needs... Focus area: {education_focus}"
            )]
        }
    
    def _provide_education_node(self, state: AgentState) -> AgentState:
        """LangGraph Node: Provide targeted patient education"""
        
        context_analysis = state.get("context_analysis", {})
        education_focus = context_analysis.get("education_focus", "heart_healthy_lifestyle")
        urgency_level = context_analysis.get("urgency_level", "routine")
        
        try:
            # Use patient education tool
            education_result = patient_education_tool.invoke({
                "topic": education_focus,
                "urgency_level": urgency_level
            })
            
            # Format educational content
            education_content = f"""
{education_result['title'].upper()}

Key Points:
{chr(10).join([f'• {point}' for point in education_result['educational_content']])}

Priority Level: {urgency_level.upper()}
            """
            
            return {
                **state,
                "education_provided": education_result,
                "educational_content": education_content,
                "tools_used": state.get("tools_used", []) + ["patient_education_tool"],
                "next_action": "generate_recommendations",
                "messages": state["messages"] + [AIMessage(content=education_content.strip())]
            }
            
        except Exception as e:
            return {
                **state,
                "error": f"Education provision failed: {str(e)}",
                "next_action": "error"
            }
    
    def _generate_recommendations_node(self, state: AgentState) -> AgentState:
        """LangGraph Node: Generate personalized recommendations"""
        
        context_analysis = state.get("context_analysis", {})
        triage_result = state.get("triage_result", {})
        
        # Create patient profile for recommendations
        patient_profile = {
            "urgency_level": context_analysis.get("urgency_level", "routine"),
            "risk_factors": triage_result.get("risk_factors", []),
            "symptoms": triage_result.get("identified_symptoms", []),
            "concerns": context_analysis.get("patient_concerns", [])
        }
        
        try:
            # Use lifestyle recommendation tool
            recommendations_result = lifestyle_recommendation_tool.invoke({
                "patient_profile": patient_profile
            })
            
            # Format recommendations
            recommendations_text = "PERSONALIZED RECOMMENDATIONS\n\n"
            for rec in recommendations_result["personalized_recommendations"]:
                priority_icon = "🔴" if rec["priority"] == "high" else "🟡"
                recommendations_text += f"{priority_icon} {rec['category'].title()}: {rec['recommendation']}\n"
            
            # Determine if tracking is needed
            needs_tracking = (context_analysis.get("priority_level") in ["high", "medium"] or 
                            recommendations_result.get("follow_up_needed", False))
            
            return {
                **state,
                "recommendations_provided": recommendations_result,
                "recommendations_text": recommendations_text,
                "needs_tracking": needs_tracking,
                "tools_used": state.get("tools_used", []) + ["lifestyle_recommendation_tool"],
                "next_action": "setup_tracking" if needs_tracking else "create_summary",
                "messages": state["messages"] + [AIMessage(content=recommendations_text.strip())]
            }
            
        except Exception as e:
            return {
                **state,
                "error": f"Recommendation generation failed: {str(e)}",
                "next_action": "error"
            }
    
    def _setup_tracking_node(self, state: AgentState) -> AgentState:
        """LangGraph Node: Setup wellness tracking guidance"""
        
        context_analysis = state.get("context_analysis", {})
        recommendations = state.get("recommendations_provided", {})
        
        # Determine tracking goals based on recommendations and urgency
        tracking_goals = ["symptoms"]  # Always track symptoms
        
        urgency_level = context_analysis.get("urgency_level", "routine")
        if urgency_level in ["urgent", "moderate"]:
            tracking_goals.extend(["blood_pressure", "weight"])
        
        # Add exercise tracking if exercise recommendations provided
        if any(rec["category"] == "exercise" for rec in recommendations.get("personalized_recommendations", [])):
            tracking_goals.append("exercise")
        
        try:
            # Use wellness tracking tool
            tracking_result = wellness_tracking_tool.invoke({
                "tracking_goals": tracking_goals
            })
            
            # Format tracking guidance
            tracking_text = "WELLNESS TRACKING PLAN\n\n"
            for goal, guidance in tracking_result["tracking_guidance"].items():
                tracking_text += f"{goal.replace('_', ' ').title()}:\n"
                tracking_text += f"  Frequency: {guidance['frequency']}\n"
                if "target_range" in guidance:
                    tracking_text += f"  Target: {guidance['target_range']}\n"
                tracking_text += f"  Tips: {', '.join(guidance['tracking_tips'])}\n\n"
            
            tracking_text += f"Recommended Apps: {', '.join(tracking_result['recommended_apps'])}"
            
            return {
                **state,
                "tracking_setup": tracking_result,
                "tracking_guidance": tracking_text,
                "tools_used": state.get("tools_used", []) + ["wellness_tracking_tool"],
                "next_action": "create_summary",
                "messages": state["messages"] + [AIMessage(content=tracking_text.strip())]
            }
            
        except Exception as e:
            return {
                **state,
                "error": f"Tracking setup failed: {str(e)}",
                "next_action": "error"
            }
    
    def _create_summary_node(self, state: AgentState) -> AgentState:
        """LangGraph Node: Create session summary and next steps"""
        
        context_analysis = state.get("context_analysis", {})
        education_provided = state.get("education_provided", {})
        urgency_level = context_analysis.get("urgency_level", "routine")
        
        # Create comprehensive summary
        summary = f"""
SESSION SUMMARY

Focus Area: {education_provided.get('title', 'General Cardiology')}
Priority Level: {urgency_level.upper()}
Tools Used: {len(state.get('tools_used', []))} educational tools

NEXT STEPS:
"""
        
        if urgency_level in ["emergency", "urgent"]:
            summary += "• Follow up with cardiology as directed\n"
            summary += "• Monitor symptoms closely\n"
            summary += "• Contact emergency services if symptoms worsen\n"
        elif urgency_level == "moderate":
            summary += "• Schedule follow-up appointment\n"
            summary += "• Continue monitoring as recommended\n"
            summary += "• Implement lifestyle changes\n"
        else:
            summary += "• Continue heart-healthy practices\n"
            summary += "• Regular preventive care\n"
            summary += "• Contact doctor with any concerns\n"
        
        summary += "\n💙 Take care of your heart health!"
        
        return {
            **state,
            "session_summary": summary,
            "workflow_complete": True,
            "virtual_assistant_complete": True,
            "next_agent": "END",
            "confidence_scores": {
                **state.get("confidence_scores", {}),
                "education_confidence": education_provided.get("confidence", 0.8)
            },
            "messages": state["messages"] + [AIMessage(content=summary.strip())]
        }
    
    def _handle_assistant_error_node(self, state: AgentState) -> AgentState:
        """LangGraph Node: Handle virtual assistant errors"""
        
        error_message = state.get("error", "Unknown assistant error")
        
        error_response = f"""
VIRTUAL ASSISTANT ERROR

{error_message}

GENERAL HEART HEALTH REMINDERS:
• Take medications as prescribed
• Follow a heart-healthy diet
• Exercise regularly as approved by your doctor
• Monitor your symptoms
• Keep regular doctor appointments

For immediate medical concerns, contact your healthcare provider.
For emergencies, call 911.
        """
        
        return {
            **state,
            "error_handled": True,
            "workflow_complete": True,
            "next_agent": "END",
            "messages": state["messages"] + [AIMessage(content=error_response.strip())]
        }
    
    def _extract_patient_concerns(self, messages: List) -> List[str]:
        """Extract patient concerns from recent messages"""
        concerns = []
        for msg in messages:
            if hasattr(msg, 'content'):
                content = msg.content.lower()
                if any(word in content for word in ["worried", "concerned", "scared", "anxious"]):
                    concerns.append("emotional_support_needed")
                if any(word in content for word in ["pain", "hurt", "ache"]):
                    concerns.append("pain_management")
                if any(word in content for word in ["breath", "breathing"]):
                    concerns.append("breathing_difficulty")
        return concerns
    
    def _determine_educational_needs(self, triage_result: Dict, urgency_level: str) -> List[str]:
        """Determine specific educational needs"""
        needs = ["general_cardiology"]
        
        if urgency_level in ["emergency", "urgent"]:
            needs.append("emergency_recognition")
        
        symptoms = triage_result.get("identified_symptoms", [])
        if "chest symptoms" in symptoms:
            needs.append("chest_pain_education")
        if "dyspnea" in symptoms:
            needs.append("breathing_techniques")
        
        return needs
    
    def _route_after_context_analysis(self, state: AgentState) -> Literal["provide_education", "error"]:
        """Route after context analysis"""
        return "error" if state.get("error") else "provide_education"
    
    def _route_after_education(self, state: AgentState) -> Literal["generate_recommendations", "error"]:
        """Route after education provision"""
        return "error" if state.get("error") else "generate_recommendations"
    
    def _route_after_recommendations(self, state: AgentState) -> Literal["setup_tracking", "create_summary", "error"]:
        """Route after recommendations"""
        if state.get("error"):
            return "error"
        elif state.get("needs_tracking"):
            return "setup_tracking"
        else:
            return "create_summary"
    
    async def process_assistant_workflow(self, state: AgentState) -> AgentState:
        """Execute the LangGraph virtual assistant workflow"""
        try:
            result = await self.graph.ainvoke(state)
            return result
        except Exception as e:
            return self._handle_assistant_error_node({
                **state,
                "error": f"Assistant workflow execution failed: {str(e)}"
            })
    
    def __call__(self, state: AgentState) -> AgentState:
        """Synchronous entry point for the LangGraph virtual assistant agent"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.process_assistant_workflow(state))
                return result
            finally:
                loop.close()
        except Exception as e:
            return self._handle_assistant_error_node({
                **state,
                "error": f"Virtual assistant execution failed: {str(e)}"
            })