import requests
from requests import RequestException

from ro_aggregator.celery_worker import celery_app

from ro_aggregator.utils import ro_enrichment, get_bearer_token


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_ro(self, ro_uri, callback, nonce, doc_enrichment_endpoint):
    rohub_endpoint = callback.split("api/")[0] + "api/ros/"
    try:
        result = ro_enrichment(
            ro_uri=ro_uri,
            rohub_endpoint=rohub_endpoint,
            doc_enrichment_endpoint=doc_enrichment_endpoint,
        )
        result["ro_uri"] = ro_uri
        result["nonce"] = nonce

        bearer_token = get_bearer_token(callback)
        headers = {"Authorization": f"Bearer {bearer_token}", "Content-Type": "application/json"}

        print(f"Sending response to {callback}: {result}")
        response = requests.post(callback, json=result, headers=headers)
        response.raise_for_status()

    except RequestException as exc:
        raise self.retry(exc=exc)

    except Exception as e:
        print(f"Task failed: {e}")
