
# Define scatter plot configurations
scatter_configs = {
    'Support vote rate': {
        'upper': 'legislator_rate',
        'lower': 'against_recall_rate'
    },
    'Support vote': {
        'upper': 'legislator_vote',
        'lower': 'against_recall_vote'
    },
    'Voting Rate': {
        'upper': 'legislator_voting_rate',
        'lower': 'recall_voting_rate'
    },
    'Total Voter': {
        'upper': 'legislator_total_voter_count',
        'lower': 'recall_vote_total_voter_count'
    }
}

def get_axis_title(column_name):
    """
    Generate appropriate axis title based on column name.
    
    Args:
        column_name (str): Column name
    
    Returns:
        str: Formatted axis title
    """
    title_mapping = {
        'legislator_rate': '2024 立委得票率',
        'against_recall_rate': '2025 反罷免得票率',
        'legislator_vote': '2024 立委得票數',
        'against_recall_vote': '2025 反罷免得票數',
        'legislator_voting_rate': '2024 立委投票率',
        'recall_voting_rate': '2025 罷免投票率',
        'legislator_total_voter_count': '2024 立委投票人數',
        'recall_vote_total_voter_count': '2025 罷免投票人數',
        'legislator_total_voter_density': '2024 人口密度 (人/平方公里)',
        'recall_vote_total_voter_density': '2025 人口密度 (人/平方公里)',
        "region": "鄉鎮",
        "area_name": "村里",
        "legislator_total_vote": "2024 立委選舉有效票數",
        "legislator_invalid_vote": "2024 立委選舉無效票數",
        "recall_vote_total_vote": "2025 罷免案有效票數",
        "recall_vote_invalid_vote": "2025 罷免案無效票數",
        "recall_invalid_rate": "2025 罷免案無效票率",
        "recall_rate": "2025 罷免得票率",
        "recall_vote": "2025 罷免得票數",
        "recall_vote_count": "2025 罷免投票人數",
        "legislator_invalid_rate": "2024 立委無效票率",
        "area_sq_km": "面積 (平方公里)",
        "village_neighborhood": "投開票里鄰",
        "Support vote rate": "支持率",
        "Support vote": "支持票數",
        "Voting Rate": "投票率",
        "Total Voter": "投票人數"
    }
    
    return title_mapping.get(column_name, column_name.replace('_', ' ').title())


