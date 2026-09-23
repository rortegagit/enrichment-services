import requests

from ro_aggregator.utils import get_title_desc


def get_extracted_claims(ro_uri, rohub_endpoint, claim_extraction_endpoint):
    ro_id = ro_uri.split("/")[-1]
    ro_endpoint = rohub_endpoint + ro_id
    title_desc = get_title_desc(ro_endpoint)
    print(title_desc)
    payload = {"text": title_desc}
    response = requests.request(
        "POST", claim_extraction_endpoint, json=payload
    )
    result = response.json()
    formatted_result = [x["claim"] for x in result]
    return formatted_result


def claim_analysis(ro_uri, rohub_endpoint, claim_analysis_endpoint, verification_index_name):
    ro_id = ro_uri.split("/")[-1]
    ro_endpoint = rohub_endpoint + ro_id
    title_desc = get_title_desc(ro_endpoint)
    print(title_desc)
    payload = {"text": title_desc, "index_name": verification_index_name}
    response = requests.request(
        "POST", claim_analysis_endpoint, json=payload
    )
    result = response.json()
    return result
