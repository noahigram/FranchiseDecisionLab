import json
import random
import requests
from typing import List, Dict, Any
import streamlit as st
import time

class HeuristicsModel:
    def __init__(self, model_path: str):
        """Initialize the heuristics model from a JSON file."""
        with open(model_path, 'r') as f:
            data = json.load(f)
            self.heuristics = data.get('heuristics', {})

    def get_relevant_heuristics(self, scenario_description: str, choice_description: str) -> List[Dict[str, Any]]:
        """
        Select the most relevant heuristics for a given scenario and choice.
        Returns a list of relevant heuristics with their descriptions and applicability.
        """
        relevant_heuristics = []
        
        # Create a prompt to evaluate heuristic relevance
        evaluation_prompt = f"""Given this business scenario and decision:

Scenario: {scenario_description}
Decision: {choice_description}

Evaluate which of these heuristics are most relevant and would provide valuable insights:

{self._format_heuristics_for_prompt()}

Return only the IDs of the 2-3 most relevant heuristics that would best help analyze this decision's impact.
Format: comma-separated list of heuristic IDs (e.g., "workhard_testing_heuristic,capital_follows_opportunity_principle")"""

        # Use the LLM to select relevant heuristics
        try:
            # Make API request to get relevant heuristic IDs
            url = "https://api.protobots.ai/proto_bots/generate_v2"
            headers = {
                "Authorization": f"Bearer {st.secrets['PROTOBOTS_API_KEY']}"
            }
            data = {
                "_id": "64f9ec54981dcfe5b966e5a3",
                "stream": "false",
                "message.assistant.0": "I will analyze which heuristics are most relevant for this business decision.",
                "message.user.1": evaluation_prompt
            }
            
            response = requests.post(url, headers=headers, data=data)
            if response.status_code == 200:
                heuristic_ids = response.json().get('object', '').strip().split(',')
                
                # Get the selected heuristics
                for heuristic_id in heuristic_ids:
                    heuristic_id = heuristic_id.strip()
                    if heuristic_id in self.heuristics:
                        relevant_heuristics.append({
                            'id': heuristic_id,
                            'name': self.heuristics[heuristic_id]['name'],
                            'description': self.heuristics[heuristic_id]['description'],
                            'applicability': self.heuristics[heuristic_id]['applicability'],
                            'limitations': self.heuristics[heuristic_id]['limitations']
                        })
            
        except Exception as e:
            print(f"Error selecting heuristics: {str(e)}")
            # Fallback: randomly select 2-3 heuristics
            selected_heuristics = random.sample(list(self.heuristics.keys()), k=min(3, len(self.heuristics)))
            for heuristic_id in selected_heuristics:
                relevant_heuristics.append({
                    'id': heuristic_id,
                    'name': self.heuristics[heuristic_id]['name'],
                    'description': self.heuristics[heuristic_id]['description'],
                    'applicability': self.heuristics[heuristic_id]['applicability'],
                    'limitations': self.heuristics[heuristic_id]['limitations']
                })
        
        return relevant_heuristics

    def calculate_metric_impacts(self, scenario_description: str, choice_description: str, relevant_heuristics: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate the impact on business metrics based on the scenario, choice, and relevant heuristics."""
        # Format heuristics for the prompt
        heuristics_text = "\n\n".join([
            f"Heuristic: {h['name']}\nDescription: {h['description']}\nApplicability: {h['applicability']}"
            for h in relevant_heuristics
        ])
        
        base_prompt = f"""Analyze this business decision using relevant entrepreneurial heuristics:

Scenario: {scenario_description}
Decision: {choice_description}

Relevant Heuristics:
{heuristics_text}

Based on these heuristics and the decision made, determine the impact on key business metrics.
Consider how the decision aligns with or contradicts each heuristic's principles.

Return ONLY a JSON object with these exact keys and value ranges:
{{
    "cash_flow": <integer between -50000 and 25000>,
    "customer_satisfaction": <integer between -25 and 25>,
    "growth_potential": <integer between -25 and 25>,
    "risk_level": <integer between -25 and 25>
}}

Ensure the response is valid JSON and includes all four metrics. For cash flow, consider typical franchise operations where most investments and impacts are moderate in scale."""

        # Try up to 3 times with different prompt variations
        for attempt in range(3):
            try:
                # Add a perspective variation on retry attempts
                if attempt > 0:
                    prompt_prefix = random.choice([
                        "As an experienced franchise consultant, ",
                        "Taking the role of a business strategist, ",
                        "From the perspective of a seasoned entrepreneur, "
                    ])
                    prompt = prompt_prefix + base_prompt
                else:
                    prompt = base_prompt
                
                # Make API request
                url = "https://api.protobots.ai/proto_bots/generate_v2"
                headers = {"Authorization": f"Bearer {st.secrets['PROTOBOTS_API_KEY']}"}
                data = {
                    "_id": "64f9ec54981dcfe5b966e5a3",
                    "stream": "false",
                    "message.assistant.0": "I will analyze the business decision and calculate metric impacts.",
                    "message.user.1": prompt
                }
                
                response = requests.post(url, headers=headers, data=data)
                
                if response.status_code == 200:
                    response_json = response.json()
                    result = response_json.get('object', '')
                    
                    if result:
                        # Clean the response text
                        result = result.replace('```json', '').replace('```', '').strip()
                        
                        # Parse JSON
                        impacts = json.loads(result)
                        
                        # Validate all required keys are present
                        required_keys = ['cash_flow', 'customer_satisfaction', 'growth_potential', 'risk_level']
                        if not all(key in impacts for key in required_keys):
                            raise ValueError("Missing required metrics in response")
                        
                        # Validate value ranges with new cash flow limits
                        if not (-50000 <= impacts['cash_flow'] <= 25000):
                            impacts['cash_flow'] = max(-50000, min(25000, impacts['cash_flow']))
                        
                        for metric in ['customer_satisfaction', 'growth_potential', 'risk_level']:
                            if not (-25 <= impacts[metric] <= 25):
                                impacts[metric] = max(-25, min(25, impacts[metric]))
                        
                        return impacts
                
            except json.JSONDecodeError:
                pass
            except Exception:
                pass
            
            time.sleep(1)
        
        return self._calculate_fallback_impacts(scenario_description, choice_description, relevant_heuristics)

    def _calculate_fallback_impacts(self, scenario_description: str, choice_description: str, relevant_heuristics: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate fallback impacts when the API fails."""
        # Initialize base impacts
        impacts = {
            'cash_flow': 0,
            'customer_satisfaction': 0,
            'growth_potential': 0,
            'risk_level': 0
        }
        
        # Look for keywords in the choice description to determine impacts
        choice_lower = choice_description.lower()
        
        # Cash flow impacts with more moderate ranges
        if any(word in choice_lower for word in ['invest', 'purchase', 'buy', 'spend']):
            impacts['cash_flow'] = random.randint(-25000, -10000)
        elif any(word in choice_lower for word in ['save', 'reduce cost', 'minimize']):
            impacts['cash_flow'] = random.randint(5000, 15000)
        
        # Customer satisfaction impacts
        if any(word in choice_lower for word in ['customer', 'service', 'experience', 'quality']):
            impacts['customer_satisfaction'] = random.randint(5, 15)
        
        # Growth potential impacts
        if any(word in choice_lower for word in ['expand', 'grow', 'improve', 'upgrade']):
            impacts['growth_potential'] = random.randint(5, 15)
        
        # Risk level impacts
        if any(word in choice_lower for word in ['safe', 'secure', 'protect']):
            impacts['risk_level'] = random.randint(-15, -5)
        elif any(word in choice_lower for word in ['risky', 'aggressive', 'ambitious']):
            impacts['risk_level'] = random.randint(5, 15)
        
        return impacts

    def generate_decision_analysis(self, scenario_description: str, choice_description: str, impacts: Dict[str, int], relevant_heuristics: List[Dict[str, Any]]) -> str:
        """
        Generate an analysis of the decision incorporating the relevant heuristics and their insights.
        """
        analysis_prompt = f"""Analyze this business decision using entrepreneurial heuristics:

Scenario: {scenario_description}
Decision: {choice_description}

Relevant Heuristics and Their Insights:
{self._format_heuristics_for_analysis(relevant_heuristics)}

Impact on Metrics:
- Cash Flow: ${impacts['cash_flow']}
- Customer Satisfaction: {impacts['customer_satisfaction']}%
- Growth Potential: {impacts['growth_potential']}%
- Risk Level: {impacts['risk_level']}%

Provide a brief analysis (3-4 sentences) that:
1. Evaluates how well the decision aligns with the relevant heuristics
2. Explains the resulting impacts based on heuristic principles
3. Suggests potential future considerations based on the heuristics

Keep the analysis concise and focused on practical business implications."""

        try:
            # Make API request to get analysis
            url = "https://api.protobots.ai/proto_bots/generate_v2"
            headers = {
                "Authorization": f"Bearer {st.secrets['PROTOBOTS_API_KEY']}"
            }
            data = {
                "_id": "64f9ec54981dcfe5b966e5a3",
                "stream": "false",
                "message.assistant.0": "I will analyze the business decision using relevant heuristics.",
                "message.user.1": analysis_prompt
            }
            
            response = requests.post(url, headers=headers, data=data)
            if response.status_code == 200:
                return response.json().get('object', '').strip()
                
        except Exception as e:
            print(f"Error generating analysis: {str(e)}")
            return "Unable to generate detailed analysis. Please review the impacts and make your own assessment."

    def _format_heuristics_for_prompt(self) -> str:
        """Format all heuristics for the evaluation prompt."""
        formatted = []
        for heuristic_id, heuristic in self.heuristics.items():
            formatted.append(f"""ID: {heuristic_id}
Name: {heuristic['name']}
Description: {heuristic['description']}
Applicability: {heuristic['applicability']}""")
        return "\n\n".join(formatted)

    def _format_heuristics_for_analysis(self, heuristics: List[Dict[str, Any]]) -> str:
        """Format the relevant heuristics for analysis prompts."""
        formatted = []
        for heuristic in heuristics:
            formatted.append(f"""Heuristic: {heuristic['name']}
Principle: {heuristic['description']}
Application: {heuristic['applicability']}
Limitations: {heuristic['limitations']}""")
        return "\n\n".join(formatted)

    def generate_final_analysis(self, decision_history: List[Dict], final_metrics: Dict[str, int]) -> str:
        """Generate a comprehensive final analysis of all decisions and their cumulative impact."""
        # Format the decision history
        decisions_text = "\n\n".join([
            f"Decision {i+1}: {decision['topic']}\n"
            f"Choice: {decision['choice']}\n"
            f"Impact: Cash Flow (${decision['impacts']['cash_flow']:+}), "
            f"Customer Satisfaction ({decision['impacts']['customer_satisfaction']:+}%), "
            f"Growth ({decision['impacts']['growth_potential']:+}%), "
            f"Risk ({decision['impacts']['risk_level']:+}%)"
            for i, decision in enumerate(decision_history)
        ])

        # Create the analysis prompt
        analysis_prompt = f"""Analyze this franchise's decision journey and provide a comprehensive strategic assessment:

Decision History:
{decisions_text}

Final Business State:
- Cash Flow: ${final_metrics['cash_flow']}
- Customer Satisfaction: {final_metrics['customer_satisfaction']}%
- Growth Potential: {final_metrics['growth_potential']}%
- Risk Level: {final_metrics['risk_level']}%

Provide a comprehensive analysis that:
1. Identifies key patterns and strategic themes across the decisions
2. Evaluates the overall effectiveness of the decision-making approach
3. Assesses how well the decisions balanced different business priorities
4. Suggests strategic recommendations for future decision-making
5. Highlights potential opportunities and challenges based on the current business state

Format the response with clear sections and bullet points where appropriate."""

        try:
            # Make API request
            url = "https://api.protobots.ai/proto_bots/generate_v2"
            headers = {"Authorization": f"Bearer {st.secrets['PROTOBOTS_API_KEY']}"}
            data = {
                "_id": "64f9ec54981dcfe5b966e5a3",
                "stream": "false",
                "message.assistant.0": "I will provide a comprehensive analysis of the franchise's decision journey.",
                "message.user.1": analysis_prompt
            }
            
            response = requests.post(url, headers=headers, data=data)
            if response.status_code == 200:
                return response.json().get('object', '').strip()
                
        except Exception:
            return ("Unable to generate comprehensive analysis. Please review the decision history "
                   "and metrics to assess the overall journey.") 