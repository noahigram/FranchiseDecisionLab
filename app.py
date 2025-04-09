import streamlit as st
from typing import Dict, List, Optional
import os

# Import custom modules
from utils import (
    apply_custom_css,
    display_business_metrics,
    apply_metric_impacts,
    display_metric_changes,
    calculate_business_health,
    get_business_status,
    INITIAL_METRICS
)
from generator import (
    generate_scenario_topics,
    generate_scenario_options,
    generate_decision_analysis
)
from heuristics import HeuristicsModel

# Set up Streamlit page configuration
st.set_page_config(
    page_title="Franchise Decision Lab",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize heuristics model
heuristics_model = HeuristicsModel("stephen_spinelli_model.json")

# Apply custom CSS
apply_custom_css()

# Initialize session state
if 'step' not in st.session_state:
    st.session_state.step = 0

if 'business_profile' not in st.session_state:
    st.session_state.business_profile = None

if 'scenario_topics' not in st.session_state:
    st.session_state.scenario_topics = []

if 'current_topic' not in st.session_state:
    st.session_state.current_topic = None

if 'decision_history' not in st.session_state:
    st.session_state.decision_history = []

if 'business_metrics' not in st.session_state:
    st.session_state.business_metrics = INITIAL_METRICS.copy()

if 'current_scenario' not in st.session_state:
    st.session_state.current_scenario = None

if 'topics_generated' not in st.session_state:
    st.session_state.topics_generated = False

if 'showing_decision_summary' not in st.session_state:
    st.session_state.showing_decision_summary = False

if 'current_analysis' not in st.session_state:
    st.session_state.current_analysis = None

if 'current_impacts' not in st.session_state:
    st.session_state.current_impacts = None

# Constants
MAX_DECISIONS = 5
EXAMPLE_PROFILE = """Fast-casual restaurant franchise in downtown area of a mid-sized city. 2,500 square feet with 30 seats. Target market is young professionals and families. Current challenges include high employee turnover and increasing competition. Looking to modernize operations and expand delivery service."""

def reset_simulation():
    """Reset the simulation to initial state."""
    st.session_state.step = 0
    st.session_state.business_profile = None
    st.session_state.scenario_topics = []
    st.session_state.current_topic = None
    st.session_state.decision_history = []
    st.session_state.business_metrics = INITIAL_METRICS.copy()
    st.session_state.current_scenario = None
    st.session_state.topics_generated = False
    st.session_state.showing_decision_summary = False
    st.session_state.current_analysis = None
    st.session_state.current_impacts = None

def display_decision_history():
    """Display the history of decisions and their impacts."""
    if st.session_state.decision_history:
        st.markdown("### Decision History")
        
        for i, decision in enumerate(st.session_state.decision_history):
            with st.expander(f"Step {i+1}: {decision['topic']}", expanded=False):
                st.markdown(f"**Choice:** {decision['choice']}")
                st.markdown(f"**Description:** {decision['description']}")
                
                # Display applied heuristics
                if 'heuristics' in decision:
                    st.markdown("**Relevant Heuristics:**")
                    for heuristic in decision['heuristics']:
                        with st.container():
                            st.markdown(f"""
                            <div style='background-color: rgba(78, 137, 174, 0.05); padding: 0.5rem; border-radius: 0.25rem; margin-bottom: 0.5rem;'>
                                <div style='font-weight: 500; color: #2c5282;'>{heuristic['name']}</div>
                                <div style='font-size: 0.9rem; color: #4a5568;'>{heuristic['description']}</div>
                            </div>
                            """, unsafe_allow_html=True)
                
                # Display impacts
                st.markdown("**Impacts:**")
                cols = st.columns(4)
                metrics = ['cash_flow', 'customer_satisfaction', 'growth_potential', 'risk_level']
                
                for j, metric in enumerate(metrics):
                    with cols[j]:
                        value = decision['impacts'][metric]
                        metric_name = metric.replace('_', ' ').title()
                        prefix = "$" if metric == "cash_flow" else ""
                        suffix = "%" if metric != "cash_flow" else ""
                        
                        if value > 0 and metric != 'risk_level':
                            st.markdown(f"**{metric_name}**: ↑ {prefix}{abs(value)}{suffix}")
                        elif value < 0 and metric != 'risk_level':
                            st.markdown(f"**{metric_name}**: ↓ {prefix}{abs(value)}{suffix}")
                        elif value > 0 and metric == 'risk_level':
                            st.markdown(f"**{metric_name}**: ↑ {prefix}{abs(value)}{suffix}")
                        elif value < 0 and metric == 'risk_level':
                            st.markdown(f"**{metric_name}**: ↓ {prefix}{abs(value)}{suffix}")
                        else:
                            st.markdown(f"**{metric_name}**: → {prefix}{abs(value)}{suffix}")
                            
                st.markdown("---")

def display_summary():
    """Display the final summary of the simulation."""
    # Display final metrics
    display_business_metrics(st.session_state.business_metrics)
    
    # Calculate and display overall health
    health_score = calculate_business_health(st.session_state.business_metrics)
    status, description = get_business_status(health_score)
    
    st.markdown(f"### Business Health Score: {health_score}%")
    st.markdown(f"**Status:** {status}")
    st.markdown(f"**Analysis:** {description}")
    
    # Get comprehensive analysis
    final_analysis = heuristics_model.generate_final_analysis(
        st.session_state.decision_history,
        st.session_state.business_metrics
    )
    
    # Display comprehensive analysis in an expander
    with st.expander("📊 View Comprehensive Analysis", expanded=True):
        st.markdown("### Strategic Assessment")
        st.markdown(final_analysis)
    
    # Display decision history
    display_decision_history()
    
    # Option to restart
    if st.button("Start New Simulation"):
        reset_simulation()
        st.rerun()

def display_business_metrics(metrics, changes=None):
    """Display the current business metrics with optional changes."""
    st.markdown("### Business Health")
    
    # Calculate health score
    health_score = calculate_business_health(metrics)
    status, description = get_business_status(health_score)
    
    # Display health score and status
    st.markdown(f"""
    <div style='padding: 1rem; border: 2px solid {get_status_color(status)}; border-radius: 0.5rem; margin-bottom: 1rem;'>
        <div style='display: flex; justify-content: space-between; margin-bottom: 0.5rem;'>
            <span style='font-weight: bold;'>Health Score: <span style='color: {get_status_color(status)};'>{health_score}%</span></span>
            <span style='font-weight: bold;'>Status: <span style='color: {get_status_color(status)};'>{status}</span></span>
        </div>
        <div style='font-style: italic;'>{description}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Create metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        value = metrics['cash_flow']
        change = changes['cash_flow'] if changes else None
        change_text = f" ({'+' if change > 0 else ''}{change:,})" if change else ""
        change_color = get_change_color(change) if change else "inherit"
        st.markdown(f"""
        <div style='padding: 1rem; border: 1px solid #4e89ae; border-radius: 0.5rem;'>
            <div style='font-weight: bold; margin-bottom: 0.5rem;'>Cash Flow</div>
            <div style='font-size: 1.2rem;'>${value:,}<span style='color: {change_color}; font-size: 0.9rem;'>{change_text}</span></div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        value = metrics['customer_satisfaction']
        change = changes['customer_satisfaction'] if changes else None
        change_text = f" ({'+' if change > 0 else ''}{change}%)" if change else ""
        change_color = get_change_color(change) if change else "inherit"
        st.markdown(f"""
        <div style='padding: 1rem; border: 1px solid #4e89ae; border-radius: 0.5rem;'>
            <div style='font-weight: bold; margin-bottom: 0.5rem;'>Customer Satisfaction</div>
            <div style='font-size: 1.2rem;'>{value}%<span style='color: {change_color}; font-size: 0.9rem;'>{change_text}</span></div>
        </div>
        """, unsafe_allow_html=True)
        st.progress(value/100)
    
    with col3:
        value = metrics['growth_potential']
        change = changes['growth_potential'] if changes else None
        change_text = f" ({'+' if change > 0 else ''}{change}%)" if change else ""
        change_color = get_change_color(change) if change else "inherit"
        st.markdown(f"""
        <div style='padding: 1rem; border: 1px solid #4e89ae; border-radius: 0.5rem;'>
            <div style='font-weight: bold; margin-bottom: 0.5rem;'>Growth Potential</div>
            <div style='font-size: 1.2rem;'>{value}%<span style='color: {change_color}; font-size: 0.9rem;'>{change_text}</span></div>
        </div>
        """, unsafe_allow_html=True)
        st.progress(value/100)
    
    with col4:
        value = metrics['risk_level']
        change = changes['risk_level'] if changes else None
        change_text = f" ({'+' if change > 0 else ''}{change}%)" if change else ""
        change_color = get_change_color(-change if change else None) if change else "inherit"  # Invert for risk
        st.markdown(f"""
        <div style='padding: 1rem; border: 1px solid #4e89ae; border-radius: 0.5rem;'>
            <div style='font-weight: bold; margin-bottom: 0.5rem;'>Risk Level</div>
            <div style='font-size: 1.2rem;'>{value}%<span style='color: {change_color}; font-size: 0.9rem;'>{change_text}</span></div>
        </div>
        """, unsafe_allow_html=True)
        st.progress(value/100)

def get_status_color(status):
    """Get color based on business status."""
    return {
        "Thriving": "#28a745",
        "Stable": "#17a2b8",
        "Challenged": "#ffc107",
        "Struggling": "#fd7e14",
        "Critical": "#dc3545"
    }.get(status, "#6c757d")

def get_change_color(change):
    """Get color based on metric change."""
    if not change:
        return "inherit"
    return "#28a745" if change > 0 else "#dc3545"

# Main app logic
def main():
    st.title("Franchise Decision Lab")
    
    # Step 0: Business Profile Input and Topic Selection
    if st.session_state.step == 0:
        # Introduction section
        st.markdown("""
        Welcome to the Franchise Decision Lab! This interactive tool helps you navigate complex business decisions 
        using expert entrepreneurial heuristics - proven decision-making frameworks derived from successful franchise operators.
        
        To begin your journey, describe your franchise business below or use our example profile.
        """)
        
        # Create a container for the OR section
        with st.container():
            col1, col2, col3, col4 = st.columns([1.2, 0.4, 1.2, 3.2])  # Adjusted ratios to move everything left
            
            with col1:
                st.markdown("<div style='font-size: 1.1rem; font-weight: 500; padding-top: 0.5rem;'>Describe your business</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown("<div style='text-align: center; color: #666; padding-top: 0.5rem;'>--OR--</div>", unsafe_allow_html=True)
            
            with col3:
                if st.button("Generate business profile", type="secondary"):
                    st.session_state.business_profile = EXAMPLE_PROFILE
                    st.rerun()
            
            # Empty column for spacing
            with col4:
                st.write("")
        
        # Profile input with example as placeholder
        business_profile = st.text_area(
            label="Business Profile",  # Add proper label
            label_visibility="collapsed",  # Hide the label
            value=st.session_state.business_profile if st.session_state.business_profile else "",
            height=150,
            placeholder=EXAMPLE_PROFILE
        )
        
        # Generate scenarios button
        if st.button("Generate Scenarios", type="primary"):
            if business_profile:
                with st.spinner("Generating scenario topics..."):
                    st.session_state.business_profile = business_profile
                    st.session_state.scenario_topics = generate_scenario_topics(business_profile)
                    st.session_state.topics_generated = True
                    st.rerun()
            else:
                st.error("Please enter a business profile to continue.")
        
        # Display topics if they've been generated
        if st.session_state.topics_generated and st.session_state.scenario_topics:
            st.markdown("---")
            st.markdown("### Select a Scenario Topic")
            st.markdown("Choose one of the following topics to begin your decision journey:")
            
            # Create a container for better spacing
            with st.container():
                # Display topics in a grid with styled buttons
                for i in range(0, len(st.session_state.scenario_topics), 3):
                    cols = st.columns(3)
                    for j in range(3):
                        if i + j < len(st.session_state.scenario_topics):
                            topic = st.session_state.scenario_topics[i + j]
                            with cols[j]:
                                if st.button(
                                    topic,
                                    key=f"topic_{i+j}",
                                    use_container_width=True,
                                ):
                                    st.session_state.current_topic = topic
                                    st.session_state.current_scenario = generate_scenario_options(
                                        topic,
                                        st.session_state.business_profile
                                    )
                                    st.session_state.step = 1
                                    st.rerun()
    
    # Steps 1-5: Decision Making
    elif isinstance(st.session_state.step, int) and 1 <= st.session_state.step <= MAX_DECISIONS:
        # Display current metrics with changes if a decision was just made
        display_business_metrics(
            st.session_state.business_metrics,
            st.session_state.current_impacts if st.session_state.showing_decision_summary else None
        )
        
        # Display current scenario
        st.markdown(f"### Decision {st.session_state.step} of {MAX_DECISIONS}: {st.session_state.current_topic}")
        
        if not st.session_state.showing_decision_summary:
            st.markdown(f"**Situation:** {st.session_state.current_scenario['description']}")
            
            # Display options
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                <div style='background-color: rgba(78, 137, 174, 0.1); border: 2px solid #4e89ae; border-radius: 0.5rem; padding: 1rem; height: 100%;'>
                    <h4>Option A: {st.session_state.current_scenario['option_a']['title']}</h4>
                    <p>{st.session_state.current_scenario['option_a']['description']}</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Choose Option A"):
                    # Calculate impacts using heuristics
                    relevant_heuristics = heuristics_model.get_relevant_heuristics(
                        st.session_state.current_scenario['description'],
                        st.session_state.current_scenario['option_a']['description']
                    )
                    impacts = heuristics_model.calculate_metric_impacts(
                        st.session_state.current_scenario['description'],
                        st.session_state.current_scenario['option_a']['description'],
                        relevant_heuristics
                    )
                    
                    # Update metrics immediately
                    st.session_state.business_metrics = apply_metric_impacts(
                        st.session_state.business_metrics,
                        impacts
                    )
                    
                    # Generate analysis
                    analysis = generate_decision_analysis(
                        st.session_state.current_scenario['description'],
                        st.session_state.current_scenario['option_a']['title'],
                        impacts,
                        relevant_heuristics
                    )
                    
                    # Store decision info
                    st.session_state.current_analysis = analysis
                    st.session_state.current_impacts = impacts
                    st.session_state.showing_decision_summary = True
                    st.session_state.last_choice = {
                        'topic': st.session_state.current_topic,
                        'choice': st.session_state.current_scenario['option_a']['title'],
                        'description': st.session_state.current_scenario['option_a']['description'],
                        'heuristics': relevant_heuristics  # Store the relevant heuristics
                    }
                    st.rerun()
            
            with col2:
                st.markdown(f"""
                <div style='background-color: rgba(78, 137, 174, 0.1); border: 2px solid #4e89ae; border-radius: 0.5rem; padding: 1rem; height: 100%;'>
                    <h4>Option B: {st.session_state.current_scenario['option_b']['title']}</h4>
                    <p>{st.session_state.current_scenario['option_b']['description']}</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Choose Option B"):
                    # Calculate impacts using heuristics
                    relevant_heuristics = heuristics_model.get_relevant_heuristics(
                        st.session_state.current_scenario['description'],
                        st.session_state.current_scenario['option_b']['description']
                    )
                    impacts = heuristics_model.calculate_metric_impacts(
                        st.session_state.current_scenario['description'],
                        st.session_state.current_scenario['option_b']['description'],
                        relevant_heuristics
                    )
                    
                    # Update metrics immediately
                    st.session_state.business_metrics = apply_metric_impacts(
                        st.session_state.business_metrics,
                        impacts
                    )
                    
                    # Generate analysis
                    analysis = generate_decision_analysis(
                        st.session_state.current_scenario['description'],
                        st.session_state.current_scenario['option_b']['title'],
                        impacts,
                        relevant_heuristics
                    )
                    
                    # Store decision info
                    st.session_state.current_analysis = analysis
                    st.session_state.current_impacts = impacts
                    st.session_state.showing_decision_summary = True
                    st.session_state.last_choice = {
                        'topic': st.session_state.current_topic,
                        'choice': st.session_state.current_scenario['option_b']['title'],
                        'description': st.session_state.current_scenario['option_b']['description'],
                        'heuristics': relevant_heuristics  # Store the relevant heuristics
                    }
                    st.rerun()
        
        else:
            # Show decision summary
            st.markdown("### Decision Summary")
            st.markdown(f"**Your Choice:** {st.session_state.last_choice['choice']}")
            st.markdown(f"**Description:** {st.session_state.last_choice['description']}")
            
            # Show impacts
            st.markdown("### Impact Analysis")
            display_metric_changes(st.session_state.current_impacts)
            
            # Show analysis
            st.markdown("### Expert Analysis")
            st.markdown(st.session_state.current_analysis)
            
            # Continue button
            button_text = "View Final Summary" if st.session_state.step == MAX_DECISIONS else "Continue Journey"
            if st.button(button_text, type="primary"):
                # Record the decision
                st.session_state.decision_history.append({
                    'topic': st.session_state.last_choice['topic'],
                    'choice': st.session_state.last_choice['choice'],
                    'description': st.session_state.last_choice['description'],
                    'impacts': st.session_state.current_impacts,
                    'heuristics': st.session_state.last_choice['heuristics']
                })
                
                # Reset summary state
                st.session_state.showing_decision_summary = False
                st.session_state.current_analysis = None
                st.session_state.current_impacts = None
                
                # Move to next step
                st.session_state.step += 1
                
                # Check if simulation is complete
                if st.session_state.step > MAX_DECISIONS:
                    st.session_state.step = 'summary'
                else:
                    # Generate next scenario
                    st.session_state.current_topic = st.session_state.scenario_topics[
                        st.session_state.step - 1
                    ]
                    st.session_state.current_scenario = generate_scenario_options(
                        st.session_state.current_topic,
                        st.session_state.business_profile
                    )
                
                st.rerun()
        
        # Display decision history
        st.markdown("---")
        display_decision_history()
        
        # Option to reset
        if st.button("Reset Simulation"):
            reset_simulation()
            st.rerun()
    
    # Summary
    elif st.session_state.step == 'summary':
        display_summary()

if __name__ == "__main__":
    main() 