import streamlit as st
import requests
import random
import json
from typing import Dict, List, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_random_prompt_variation() -> Dict[str, str]:
    """Get random variations for prompts to increase response diversity"""
    perspective_variations = [
        "As an experienced franchise consultant,",
        "Taking the role of a business strategist,",
        "From the perspective of a seasoned entrepreneur,",
        "As a franchise industry expert,",
        "With years of business advisory experience,"
    ]
    
    context_variations = [
        "considering the current market dynamics,",
        "taking into account industry trends,",
        "analyzing the business landscape,",
        "evaluating the competitive environment,",
        "examining the operational context,"
    ]
    
    style_variations = [
        "provide insights on",
        "analyze and suggest",
        "evaluate and recommend",
        "assess and determine",
        "review and propose"
    ]
    
    return {
        'perspective': random.choice(perspective_variations),
        'context': random.choice(context_variations),
        'style': random.choice(style_variations)
    }

def generate_scenario_topics(business_profile: str, heuristics_model=None) -> List[str]:
    """Generate relevant scenario topics based on the business profile and heuristics."""
    logger.info("Attempting to generate scenario topics via API...")
    
    # Get random variations for the prompt
    variations = get_random_prompt_variation()
    
    # Get relevant heuristics if model is provided
    heuristics_text = ""
    if heuristics_model:
        relevant_heuristics = heuristics_model.get_relevant_heuristics(business_profile)
        if relevant_heuristics:
            heuristics_text = "\n\nRelevant Business Frameworks:\n" + "\n".join([
                f"- {h['name']}: {h['description']}"
                for h in relevant_heuristics[:3]  # Use top 3 most relevant heuristics
            ])
    
    prompt = f"""{variations['perspective']} {variations['context']} {variations['style']} relevant scenario topics for this business:

Business Profile:
{business_profile}{heuristics_text}

Generate a list of scenario topics that:
1. Are specific to the business's industry and situation
2. Cover different aspects of business management (operations, finance, marketing, etc.)
3. Include both immediate challenges and long-term opportunities
4. Are realistic and actionable
5. Would have significant impact on business metrics (cash, customer satisfaction, growth potential, and risk level)
6. Align with the provided business frameworks and their principles
7. Create opportunities to apply these decision-making frameworks

Format your response as a simple list of topics, one per line, with no numbers or bullet points. Keep each topic concise (2-4 words)."""

    try:
        # Make API request to generate topics
        url = "https://api.protobots.ai/proto_bots/generate_v2"
        headers = {"Authorization": f"Bearer {st.secrets['PROTOBOTS_API_KEY']}"}
        data = {
            "_id": "67e6b4348602548f55512135",
            "stream": "true",
            "message.assistant.0": "I am a business scenario generator. I will create relevant scenario topics based on the business profile and frameworks.",
            "message.user.1": prompt
        }
        
        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code == 200:
            # Split the response into data chunks
            chunks = [line for line in response.text.split('\n') if line.startswith('data:')]
            topics_text = ''
            
            if chunks:
                # Get the last complete data chunk (ignoring loader messages)
                for chunk in reversed(chunks):
                    try:
                        # Remove 'data: ' prefix and parse JSON
                        data = json.loads(chunk[5:].strip())
                        # Skip loader messages
                        if 'message' in data and ('loader' in data['message'] or data['message'] == '[DONE]'):
                            continue
                        if 'message' in data:
                            topics_text = data['message']
                            break
                        if 'object' in data:
                            topics_text = data['object']
                            break
                    except json.JSONDecodeError:
                        continue
            else:
                topics_text = response.text
            
            if topics_text:
                # Clean and parse the response
                topics = [
                    topic.strip().lstrip('0123456789. -•*')
                    for topic in topics_text.split('\n')
                    if topic.strip()
                ]
                topics = [t for t in topics if t and not t.startswith('data:')][:7]  # Limit to 7 topics
                if topics:
                    logger.info("Successfully generated scenario topics via API")
                    return topics
        
        logger.warning("API call failed or returned invalid response for scenario topics")
        return generate_fallback_topics(heuristics_model, business_profile)
        
    except Exception as e:
        logger.error(f"Error generating topics via API: {str(e)}")
        # Return fallback topics
        return generate_fallback_topics(heuristics_model, business_profile)

def generate_fallback_topics(heuristics_model, business_profile: str) -> List[str]:
    """Generate fallback topics considering heuristics if available."""
    logger.info("Using fallback topic generation")
    base_topics = [
        "Staff Management",
        "Marketing Strategy",
        "Financial Planning",
        "Customer Service",
        "Technology Implementation"
    ]
    
    if heuristics_model:
        try:
            # Get relevant heuristics
            relevant_heuristics = heuristics_model.get_relevant_heuristics(business_profile)
            if relevant_heuristics:
                # Add topics based on heuristic names
                heuristic_topics = []
                for h in relevant_heuristics[:2]:  # Use top 2 heuristics
                    name = h['name'].replace("Heuristic", "").replace("Framework", "").strip()
                    if "Decision" in name:
                        topic = name.replace("Decision", "Strategy")
                    else:
                        topic = name + " Initiative"
                    heuristic_topics.append(topic)
                logger.info("Generated fallback topics with heuristics")
                return heuristic_topics + base_topics[:5-len(heuristic_topics)]
        except Exception as e:
            logger.error(f"Error generating heuristic-based topics: {str(e)}")
    
    logger.info("Generated basic fallback topics")
    return base_topics

def make_api_call(prompt: str, system_message: str, max_retries: int = 3) -> Optional[str]:
    """Make an API call with retry logic."""
    url = "https://api.protobots.ai/proto_bots/generate_v2"
    headers = {"Authorization": f"Bearer {st.secrets['PROTOBOTS_API_KEY']}"}
    
    for attempt in range(max_retries):
        try:
            logger.info(f"API call attempt {attempt + 1} of {max_retries}")
            
            data = {
                "_id": "67e6b4348602548f55512135",
                "stream": "true",
                "message.assistant.0": system_message,
                "message.user.1": prompt
            }
            
            response = requests.post(url, headers=headers, data=data)
            
            if response.status_code == 200:
                # Split the response into data chunks
                chunks = [line for line in response.text.split('\n') if line.startswith('data:')]
                
                if not chunks:
                    return response.text
                
                # Get the last complete data chunk (ignoring loader messages)
                for chunk in reversed(chunks):
                    try:
                        # Remove 'data: ' prefix and parse JSON
                        data = json.loads(chunk[5:].strip())
                        # Skip loader messages
                        if 'message' in data and ('loader' in data['message'] or data['message'] == '[DONE]'):
                            continue
                        if 'message' in data:
                            return data['message'].strip()
                        if 'object' in data:
                            return data['object'].strip()
                    except json.JSONDecodeError:
                        continue
            
            logger.warning(f"API call attempt {attempt + 1} failed with status {response.status_code}")
            
        except Exception as e:
            logger.error(f"API call attempt {attempt + 1} failed with error: {str(e)}")
        
        # Vary the prompt slightly for the next attempt
        if attempt < max_retries - 1:
            prompt = f"{get_random_prompt_variation()['perspective']}\n{prompt}"
    
    logger.error("All API call attempts failed")
    return None

def generate_scenario_options(topic: str, business_profile: str) -> Dict:
    """Generate two distinct decision options for a given scenario topic."""
    base_prompt = f"""create a specific scenario and decision options for this business situation:

Topic: {topic}
Business Profile: {business_profile}

Create a scenario that specifically addresses {topic} and provides two distinct approaches to handling it. The scenario should be directly relevant to the topic and the business profile.

The response must follow this exact JSON structure:
{{
    "description": "A brief description of the situation that specifically relates to {topic} (1-2 sentences)",
    "option_a": {{
        "title": "A short title for the first {topic} option (3-5 words)",
        "description": "Brief description of how this approach addresses {topic} (1-2 sentences)"
    }},
    "option_b": {{
        "title": "A short title for the second {topic} option (3-5 words)",
        "description": "Brief description of how this approach addresses {topic} (1-2 sentences)"
    }}
}}

Guidelines:
1. The scenario description must directly address {topic}
2. Both options should be specific ways to handle the {topic} situation
3. Options should be distinct but both potentially viable
4. Make options realistic for the business profile
5. Consider how each option might affect:
   - Cash and financial metrics
   - Customer satisfaction and experience
   - Growth potential and scalability
   - Risk level and business stability
6. Avoid generic solutions - make them specific to {topic}"""

    system_message = f"I will create a specific scenario and options for the topic: {topic}"
    
    result = make_api_call(base_prompt, system_message)
    
    if result:
        try:
            scenario = json.loads(result)
            # Validate that the scenario is topic-specific
            if any(word.lower() in scenario['description'].lower() for word in topic.split()):
                return scenario
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing scenario JSON: {str(e)}")
    
    # If all retries failed or validation failed, use fallback
    return generate_fallback_scenario(topic)

def generate_fallback_scenario(topic: str, step: int = 1) -> Dict:
    """Generate a fallback scenario based on the topic and step number."""
    logger.info(f"Using fallback scenario generation for topic '{topic}' step {step}")
    topic_lower = topic.lower()
    
    # Define step-specific aspects for common topics
    if "fleet" in topic_lower or "vehicle" in topic_lower:
        aspects = [
            ("Route Optimization", "Implement new routing software vs. Enhance current system", "Fleet Efficiency Planning"),
            ("Maintenance Schedule", "Preventive maintenance program vs. As-needed repairs", "Vehicle Maintenance Strategy"),
            ("Vehicle Acquisition", "Purchase new vehicles vs. Lease with maintenance", "Fleet Expansion Decisions"),
            ("Driver Training", "Comprehensive safety program vs. Basic compliance training", "Team Development Focus"),
            ("Fuel Efficiency", "Invest in fuel monitoring vs. Driver incentive program", "Resource Management Planning")
        ]
    elif "staff" in topic_lower or "employee" in topic_lower:
        aspects = [
            ("Training Program", "Structured training vs. On-the-job learning", "Staff Development Framework"),
            ("Compensation", "Performance bonuses vs. Higher base pay", "Team Compensation Strategy"),
            ("Scheduling", "Fixed shifts vs. Flexible hours", "Workforce Schedule Planning"),
            ("Development", "Career advancement vs. Skill specialization", "Career Growth Initiatives"),
            ("Team Building", "Regular events vs. Project-based collaboration", "Team Culture Building")
        ]
    elif "market" in topic_lower:
        aspects = [
            ("Target Analysis", "Focus on core demographic vs. Market expansion", "Market Research Phase"),
            ("Promotion Strategy", "Digital marketing vs. Local partnerships", "Marketing Channel Selection"),
            ("Pricing Model", "Premium positioning vs. Competitive pricing", "Price Strategy Development"),
            ("Service Offering", "Specialized services vs. Broad coverage", "Service Portfolio Planning"),
            ("Growth Plan", "Intensive local growth vs. Geographic expansion", "Expansion Strategy Design")
        ]
    else:
        aspects = [
            ("Initial Strategy", "Aggressive approach vs. Gradual implementation", "Strategic Foundation Setting"),
            ("Resource Allocation", "Heavy investment vs. Measured spending", "Resource Planning Phase"),
            ("Process Implementation", "Complete overhaul vs. Phased rollout", "Implementation Approach"),
            ("Team Structure", "Specialized roles vs. Cross-training", "Organizational Design"),
            ("Future Planning", "Short-term results vs. Long-term development", "Growth Strategy Planning")
        ]
    
    # Get the appropriate aspect for this step (0-based index)
    aspect = aspects[min(step - 1, len(aspects) - 1)]
    
    return {
        "sub_module_name": aspect[2],
        "description": f"Your franchise needs to make decisions about {topic} focusing on {aspect[0]}.",
        "option_a": {
            "title": f"Comprehensive {aspect[0]}",
            "description": f"Implement a full-scale approach to {aspect[0]} with significant resource allocation."
        },
        "option_b": {
            "title": f"Focused {aspect[0]}",
            "description": f"Take a targeted approach to {aspect[0]} with minimal disruption to current operations."
        }
    }

def generate_decision_analysis(scenario_description: str, choice_title: str, impacts: Dict[str, int], relevant_heuristics: List[Dict]) -> str:
    """Generate an analysis of the decision and its impacts, using heuristics as frameworks."""
    # Format the heuristics and impacts
    heuristics_text = "\n\n".join([
        f"Heuristic: {h['name']}\nDescription: {h['description']}\nApplication: {h['applicability']}"
        for h in relevant_heuristics
    ])
    
    impacts_text = "\n".join([
        f"{metric.replace('_', ' ').title()}: {value:+}"
        for metric, value in impacts.items()
    ])
    
    base_prompt = f"""analyze this business decision using the provided heuristics as frameworks:

Scenario: {scenario_description}
Choice Made: {choice_title}

Relevant Business Heuristics:
{heuristics_text}

Observed Impacts:
{impacts_text}

Please provide an analysis that:
1. Explains how each relevant heuristic framework applies to this decision
2. Uses the heuristics to justify why specific impacts occurred
3. Connects the principles from the heuristics to the observed outcomes
4. Provides insights about the long-term implications based on these frameworks

Format the analysis to explicitly reference the heuristics and explain how their principles support the observed impacts. Keep the total analysis under 250 words."""

    system_message = "I will analyze this business decision using the provided heuristic frameworks."
    
    result = make_api_call(base_prompt, system_message)
    
    if result:
        return result
    
    # If all retries failed, use fallback
    return generate_fallback_analysis(scenario_description, choice_title, impacts, relevant_heuristics)

def generate_fallback_analysis(scenario_description: str, choice_title: str, impacts: Dict[str, int], relevant_heuristics: List[Dict]) -> str:
    """Generate a fallback analysis using templates and heuristics."""
    analysis_parts = []
    
    # Start with a general overview
    analysis_parts.append(f"Analysis of the decision to {choice_title.lower()}:")
    
    # Add analysis based on each relevant heuristic
    for heuristic in relevant_heuristics:
        heuristic_analysis = f"\n\nApplying the {heuristic['name']}: "
        
        # Add specific analysis based on the heuristic type
        if "risk" in heuristic['name'].lower():
            if impacts['risk_level'] > 0:
                heuristic_analysis += f"According to this framework, the increased risk level ({impacts['risk_level']:+}%) suggests {heuristic['applicability']}. "
            else:
                heuristic_analysis += f"This framework supports the reduced risk level ({impacts['risk_level']:+}%) through {heuristic['applicability']}. "
        
        elif "growth" in heuristic['name'].lower():
            if impacts['growth_potential'] > 0:
                heuristic_analysis += f"This decision aligns with the framework's emphasis on {heuristic['applicability']}, leading to increased growth potential ({impacts['growth_potential']:+}%). "
            else:
                heuristic_analysis += f"The framework suggests that the reduced growth potential ({impacts['growth_potential']:+}%) may be due to deviation from {heuristic['applicability']}. "
        
        elif "customer" in heuristic['name'].lower():
            if impacts['customer_satisfaction'] > 0:
                heuristic_analysis += f"Following this framework's principles about {heuristic['applicability']} has positively impacted customer satisfaction ({impacts['customer_satisfaction']:+}%). "
            else:
                heuristic_analysis += f"The decrease in customer satisfaction ({impacts['customer_satisfaction']:+}%) indicates a potential misalignment with the framework's guidance on {heuristic['applicability']}. "
        
        elif "financial" in heuristic['name'].lower() or "cash" in heuristic['name'].lower():
            if impacts['cash_flow'] > 0:
                heuristic_analysis += f"The positive cash impact (${impacts['cash_flow']:+,}) aligns with the framework's principles regarding {heuristic['applicability']}. "
            else:
                heuristic_analysis += f"The framework suggests that the cash reduction (${impacts['cash_flow']:+,}) may be justified if {heuristic['applicability']}. "
        
        else:
            # Generic analysis for other types of heuristics
            heuristic_analysis += f"This framework suggests that {heuristic['applicability']} will influence the observed impacts on business metrics. "
        
        analysis_parts.append(heuristic_analysis)
    
    # Add a forward-looking conclusion
    total_impact = sum(impacts.values())
    if total_impact > 0:
        analysis_parts.append("\n\nBased on these frameworks, this decision appears well-aligned with established business principles and should contribute positively to long-term success.")
    else:
        analysis_parts.append("\n\nWhile the immediate impacts may be challenging, these frameworks suggest the decision could provide valuable learning opportunities and potential for future adaptation.")
    
    return "".join(analysis_parts)

def parse_streaming_response(response_text: str) -> str:
    """Parse a streaming response to extract the actual content."""
    # Split the response into data chunks
    chunks = [line for line in response_text.split('\n') if line.startswith('data:')]
    
    if not chunks:
        return response_text
    
    # Get the last complete data chunk (ignoring loader messages)
    content = ''
    for chunk in reversed(chunks):
        try:
            # Remove 'data: ' prefix and parse JSON
            data = json.loads(chunk[5:].strip())
            # Skip loader messages
            if 'message' in data and ('loader' in data['message'] or data['message'] == '[DONE]'):
                continue
            if 'message' in data:
                content = data['message']
                break
            if 'object' in data:
                content = data['object']
                break
        except json.JSONDecodeError:
            continue
    
    return content.strip()

def generate_topic_scenario(topic: str, business_profile: str, step: int) -> Dict:
    """Generate a scenario for a specific step within a topic's learning journey."""
    logger.info(f"Attempting to generate scenario for step {step} via API...")
    
    # Get random variations for the prompt
    variations = get_random_prompt_variation()
    
    base_prompt = f"""{variations['perspective']} create a specific scenario for step {step} of 5 in this learning journey:

Topic: {topic}
Business Profile: {business_profile}
Step: {step} of 5

First, create a brief name (3-5 words) for this specific part of the {topic} journey that describes its focus.
Then create a scenario that:
1. Addresses a specific aspect or challenge within {topic}
2. Builds upon the overall topic but can stand independently
3. Represents a realistic business situation
4. Requires strategic decision-making
5. Has meaningful impact on business metrics (cash, customer satisfaction, growth potential, and risk level)

The response must follow this exact JSON structure:
{{
    "sub_module_name": "Brief name for this specific part (3-5 words)",
    "description": "A specific situation related to {topic} (2-3 sentences)",
    "option_a": {{
        "title": "A short title for the first option (3-5 words)",
        "description": "Brief description of this approach (1-2 sentences)"
    }},
    "option_b": {{
        "title": "A short title for the second option (3-5 words)",
        "description": "Brief description of this approach (1-2 sentences)"
    }}
}}"""

    system_message = f"I will create a specific scenario for step {step} of the {topic} learning journey"
    
    result = make_api_call(base_prompt, system_message)
    
    if result:
        try:
            scenario = json.loads(result)
            # Validate that the scenario is topic-specific
            if any(word.lower() in scenario['description'].lower() for word in topic.split()):
                logger.info(f"Successfully generated scenario for step {step} via API")
                return scenario
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error parsing scenario JSON: {str(e)}")
    
    # If all retries failed or validation failed, use fallback
    logger.warning(f"Using fallback scenario generation for step {step}")
    return generate_fallback_scenario(topic, step) 