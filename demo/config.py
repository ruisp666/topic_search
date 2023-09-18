DOCKER = False
SECTIONS_TITLE = [f'Section{s}' for s in ['1', '1A', '7']]
SECTIONS_DESCRIPTION = {'Section1': 'Business: requires a description of the company’s business, including its main '
                                    'products and services, what subsidiaries it owns, and what markets it operates '
                                    'in. This section may also include information about recent events, competition '
                                    'the company faces, regulations that apply to it, labor issues, special operating '
                                    'costs, or seasonal factors. This is a good place to start to understand how the '
                                    'company operates.',
                        'Section1A': 'Risk Factors: includes information about the most significant risks that apply '
                                     'to the company or to its securiies. Companies generally list the risk factors '
                                     'in order of their importance. In practice, this section focuses on the risks '
                                     'themselves, not how the company addresses those risks. Some risks may be true '
                                     'for the entire economy, some may apply only to the company’s in- dustry sector '
                                     'or geographic region, and some may be unique to the company.',

                        'Section7': 'Management’s Discussion and Analysis of Financial Condition and Results of '
                                    'Operations: gives the company’s perspective on the business results of the past '
                                    'financial year. This section, known as the MD&A for short, allows company '
                                    'management to tell its story in its own words.'}

FED_TOPIC_MAPPINGS = {
    '1309_lending practices_prudential standards_fdic nccob_banking': 'lending practices regulation',
    '1751_ccpa_cfpb 8217_consumer financial_enforcement': 'consumer protection enforcement',
    '178_bearing liabilities_net income_deposits borrowings_loans securities': 'bearing liabilities earnings',
    '2013_cares act_programs facilities_provisions cares_consolidated appropriations': 'cares act provisions',
    '2573_aenb_qualifying collateral_charge trust_lending trust': 'collateralized lending facility',
    '3_libor_sofr_reference rates_usd libor': 'libor reference rates',
    '557_funds rate_federal funds_federal reserve_actions federal': 'federal funds rate',
    '786_spoe_spoe strategy_parent company_support agreement': 'parent support strategy',
    '2462_secured funding_collateralized financings_gs bank_financings consolidated': 'collateralized financing assets',
    '44_federal reserve_capital liquidity_regulatory capital_basel iii': 'capital liquidity regulation',
    '846_backed securities_fasb financial_rmbs residential_capital financial': 'mortgage-backed securities',
    '86_fdic_reserve fdic_submit resolution_orderly resolution': 'fdic resolution planning',
    '878_monetary policy_monetary policies_instruments monetary_fiscal policies': 'monetary policy actions'
}