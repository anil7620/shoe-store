import boto3

wafv2 = boto3.client('wafv2')

def configure_waf(lb_arn, lb_name):
    setup_waf = input("Do you want to set up WAF? (yes/no): ")
    if setup_waf.lower() == 'yes':
        print("WAF Options:")
        print("1. Rate limiting")
        print("2. Geo restriction")
        waf_option = input("Select an option (1 or 2): ")
        
        waf_acl = wafv2.create_web_acl(
            Name=f"{lb_name}-acl",
            Scope='REGIONAL',
            DefaultAction={'Allow': {}},
            VisibilityConfig={'SampledRequestsEnabled': True, 'CloudWatchMetricsEnabled': True, 'MetricName': 'WebACL'}
        )
        waf_arn = waf_acl['Summary']['ARN']
        
        if waf_option == '1':
            rate_limit = int(input("Enter rate limit (requests per 5 minutes): "))
            rate_based_rule = {
                'Name': 'RateBasedRule',
                'Priority': 1,
                'Action': {'Block': {}},
                'Statement': {'RateBasedStatement': {'Limit': rate_limit, 'AggregateKeyType': 'IP'}},
                'VisibilityConfig': {'SampledRequestsEnabled': True, 'CloudWatchMetricsEnabled': True, 'MetricName': 'RateBasedRule'}
            }
            wafv2.update_web_acl(
                Scope='REGIONAL',
                Id=waf_arn,
                LockToken=wafv2.get_web_acl(Scope='REGIONAL', Name=f"{lb_name}-acl")['LockToken'],
                DefaultAction={'Allow': {}},
                Rules=[rate_based_rule]
            )
        elif waf_option == '2':
            country_codes = input("Enter country codes (comma-separated, e.g., US,CA): ").split(',')
            geo_match_statement = {'GeoMatchStatement': {'CountryCodes': country_codes}}
            geo_based_rule = {
                'Name': 'GeoBasedRule',
                'Priority': 1,
                'Action': {'Block': {}},
                'Statement': geo_match_statement,
                'VisibilityConfig': {'SampledRequestsEnabled': True, 'CloudWatchMetricsEnabled': True, 'MetricName': 'GeoBasedRule'}
            }
            wafv2.update_web_acl(
                Scope='REGIONAL',
                Id=waf_arn,
                LockToken=wafv2.get_web_acl(Scope='REGIONAL', Name=f"{lb_name}-acl")['LockToken'],
                DefaultAction={'Allow': {}},
                Rules=[geo_based_rule]
            )
        wafv2.associate_web_acl(WebACLArn=waf_arn, ResourceArn=lb_arn)
        print("WAF setup complete.")
