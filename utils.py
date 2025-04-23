import streamlit as st
from typing import Dict, List, Tuple, Optional

# Initial business metrics
INITIAL_METRICS = {
    'cash_flow': 100000,
    'customer_satisfaction': 50,
    'growth_potential': 50,
    'risk_level': 30
}

def apply_custom_css():
    """Apply custom CSS styling to the app."""
    st.markdown("""
    <style>
    .main {
        background-color: #f5f5f5;
    }
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .metric-card {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .decision-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        border-left: 4px solid #2196F3;
    }
    .impact-analysis {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-top: 1rem;
    }
    .navigation-button {
        background-color: #2196F3;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 0.25rem;
        text-decoration: none;
        display: inline-block;
        margin: 0.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

def display_business_metrics(metrics: Dict[str, int], changes: Optional[Dict[str, int]] = None):
    """Display the current business metrics."""
    st.markdown("### Business Health")
    
    # Create metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Cash",
            f"${metrics['cash_flow']:,}",
            f"{changes['cash_flow']:+,}" if changes and 'cash_flow' in changes else None
        )
    
    with col2:
        st.metric(
            "Customer Satisfaction",
            f"{metrics['customer_satisfaction']}%",
            delta=None
        )
        st.progress(metrics['customer_satisfaction']/100)
    
    with col3:
        st.metric(
            "Growth Potential",
            f"{metrics['growth_potential']}%",
            delta=None
        )
        st.progress(metrics['growth_potential']/100)
    
    with col4:
        st.metric(
            "Risk Level",
            f"{metrics['risk_level']}%",
            delta=None
        )
        st.progress(metrics['risk_level']/100)

def apply_metric_impacts(current_metrics: Dict[str, int], impacts: Dict[str, int]) -> Dict[str, int]:
    """Apply the calculated impacts to the current metrics."""
    updated_metrics = current_metrics.copy()
    
    for metric, impact in impacts.items():
        updated_metrics[metric] += impact
        
        # Ensure percentage metrics stay within bounds
        if metric != 'cash_flow':
            updated_metrics[metric] = max(0, min(100, updated_metrics[metric]))
    
    return updated_metrics

def display_metric_changes(consequences):
    """Display changes to metrics with visual indicators"""
    cols = st.columns(4)
    metrics = ['cash_flow', 'customer_satisfaction', 'growth_potential', 'risk_level']
    icons = {'increase': '↑', 'decrease': '↓', 'neutral': '↔'}
    
    for i, metric in enumerate(metrics):
        value = consequences[metric]
        with cols[i]:
            metric_name = metric.replace('_', ' ').title()
            prefix = "$" if metric == "cash_flow" else ""
            suffix = "%" if metric != "cash_flow" else ""
            
            if value > 0 and metric != 'risk_level':
                st.markdown(f"<div style='color:#4CAF50'><b>{metric_name}</b>: {icons['increase']} {prefix}{abs(value)}{suffix}</div>", unsafe_allow_html=True)
            elif value < 0 and metric != 'risk_level':
                st.markdown(f"<div style='color:#FF5252'><b>{metric_name}</b>: {icons['decrease']} {prefix}{abs(value)}{suffix}</div>", unsafe_allow_html=True)
            elif value > 0 and metric == 'risk_level':
                st.markdown(f"<div style='color:#FF5252'><b>{metric_name}</b>: {icons['increase']} {prefix}{abs(value)}{suffix}</div>", unsafe_allow_html=True)
            elif value < 0 and metric == 'risk_level':
                st.markdown(f"<div style='color:#4CAF50'><b>{metric_name}</b>: {icons['decrease']} {prefix}{abs(value)}{suffix}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='color:#e1e1e1'><b>{metric_name}</b>: {icons['neutral']} {prefix}{abs(value)}{suffix}</div>", unsafe_allow_html=True)

def calculate_business_health(metrics: Dict[str, int]) -> int:
    """Calculate overall business health score."""
    health_score = (
        (0.4 * min(metrics['cash_flow'] / 100000, 1)) +
        (0.3 * (metrics['customer_satisfaction'] / 100)) +
        (0.2 * (metrics['growth_potential'] / 100)) -
        (0.1 * (metrics['risk_level'] / 100))
    )
    return int(max(0, min(100, health_score * 100)))

def get_business_status(health_score: int) -> Tuple[str, str]:
    """Get business status description based on health score."""
    if health_score >= 80:
        return "Thriving", "Your franchise is in excellent condition with strong financials and growth."
    elif health_score >= 60:
        return "Stable", "Your franchise is performing well with good prospects."
    elif health_score >= 40:
        return "Challenged", "Your franchise faces some challenges but remains viable."
    elif health_score >= 20:
        return "Struggling", "Your franchise is experiencing significant difficulties and needs attention."
    else:
        return "Critical", "Your franchise is in critical condition and at risk of failure." 