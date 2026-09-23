import os

from flask import Flask, jsonify, request

from ro_claims.utils import get_extracted_claims, claim_analysis
from ro_recommender.utils import get_recommendation_query, get_related_ros
from ro_aggregator.tasks import process_ro

# App Config
app = Flask(__name__)
app.config["DEBUG"] = False


# Parameter Init
DOC_ENRICHMENT_ENDPOINT = os.getenv("DOC_ENRICHMENT_ENDPOINT")
CLAIM_EXTRACTION_ENDPOINT = os.getenv("CLAIM_EXTRACTION_ENDPOINT")
CLAIM_ANALYSIS_ENDPOINT = os.getenv("CLAIM_ANALYSIS_ENDPOINT")
VERIFICATION_INDEX_NAME = os.getenv("VERIFICATION_INDEX_NAME")


@app.route("/healthcheck", methods=["GET"])
def healthcheck():
    return "<h1>The answer is 42</h1>"


@app.route("/ro_analysis", methods=["POST"])
def ro_analysis():
    data = request.get_json(force=True)

    required_fields = ["ro_uri", "callback", "nonce"]
    missing = [field for field in required_fields if field not in data]

    if missing:
        return (
            jsonify({"error": "Missing required fields", "missing_fields": missing}),
            400,
        )

    ro_uri = data["ro_uri"]
    callback = data["callback"]
    nonce = data["nonce"]

    process_ro.delay(
        ro_uri=ro_uri,
        callback=callback,
        nonce=nonce,
        doc_enrichment_endpoint=DOC_ENRICHMENT_ENDPOINT,
    )
    return (
        jsonify(
            {"status": "queued", "ro_uri": ro_uri, "callback": callback, "nonce": nonce}
        ),
        202,
    )


@app.route("/ro_recommendation", methods=["POST"])
def recommendation():
    data = request.get_json(force=True)

    required_fields = ["ros", "scientists"]
    missing = [field for field in required_fields if field not in data]

    if missing:
        return (
            jsonify({"error": "Missing required fields", "missing_fields": missing}),
            400,
        )

    ros = data["ros"]
    authors = data["scientists"]
    rohub_endpoint = "https://api.rohub.org/api/"

    concepts, places = get_recommendation_query(
        ros=ros,
        authors=authors,
        rohub_endpoint=rohub_endpoint,
    )

    if len(concepts) <= 0 and len(places) <= 0:
        return jsonify({"error": "Not enriched or not valid ROs in the request"})

    response = get_related_ros(
        concepts=concepts, places=places, rohub_endpoint=rohub_endpoint
    )
    return jsonify(response), 200


@app.route("/ro_recommendation_dev", methods=["POST"])
def recommendation_dev():
    data = request.get_json(force=True)

    required_fields = ["ros", "scientists"]
    missing = [field for field in required_fields if field not in data]

    if missing:
        return (
            jsonify({"error": "Missing required fields", "missing_fields": missing}),
            400,
        )

    ros = data["ros"]
    authors = data["scientists"]
    rohub_endpoint = "https://rohub2020-devel.apps.bst2.paas.psnc.pl/api/"

    concepts, places = get_recommendation_query(
        ros=ros,
        authors=authors,
        rohub_endpoint=rohub_endpoint,
    )

    if len(concepts) <= 0 and len(places) <= 0:
        return jsonify({"error": "Not enriched or not valid ROs in the request"})

    response = get_related_ros(
        concepts=concepts, places=places, rohub_endpoint=rohub_endpoint
    )
    return jsonify(response), 200


@app.route("/ro_claim_extraction", methods=["POST"])
def ro_claim_extraction():
    data = request.get_json(force=True)

    required_fields = ["ro_uri"]
    missing = [field for field in required_fields if field not in data]

    if missing:
        return (
            jsonify({"error": "Missing required fields", "missing_fields": missing}),
            400,
        )

    ro_uri = data["ro_uri"]
    rohub_endpoint = "https://api.rohub.org/api/ros/"

    claims = get_extracted_claims(
        ro_uri=ro_uri,
        rohub_endpoint=rohub_endpoint,
        claim_extraction_endpoint=CLAIM_EXTRACTION_ENDPOINT,
    )
    return jsonify(claims), 200


@app.route("/ro_claim_extraction_dev", methods=["POST"])
def ro_claim_extraction_dev():
    data = request.get_json(force=True)

    required_fields = ["ro_uri"]
    missing = [field for field in required_fields if field not in data]

    if missing:
        return (
            jsonify({"error": "Missing required fields", "missing_fields": missing}),
            400,
        )

    ro_uri = data["ro_uri"]
    rohub_endpoint = "https://rohub2020-devel.apps.bst2.paas.psnc.pl/api/ros/"

    claims = get_extracted_claims(
        ro_uri=ro_uri,
        rohub_endpoint=rohub_endpoint,
        claim_extraction_endpoint=CLAIM_EXTRACTION_ENDPOINT,
    )
    return jsonify(claims), 200


@app.route("/ro_claim_analysis", methods=["POST"])
def ro_claim_analysis():
    data = request.get_json(force=True)

    required_fields = ["ro_uri"]
    missing = [field for field in required_fields if field not in data]

    if missing:
        return (
            jsonify({"error": "Missing required fields", "missing_fields": missing}),
            400,
        )

    ro_uri = data["ro_uri"]
    rohub_endpoint = "https://api.rohub.org/api/ros/"

    ca_report = claim_analysis(
        ro_uri=ro_uri,
        rohub_endpoint=rohub_endpoint,
        claim_analysis_endpoint=CLAIM_ANALYSIS_ENDPOINT,
        verification_index_name=VERIFICATION_INDEX_NAME,
    )
    return jsonify(ca_report), 200


@app.route("/ro_claim_analysis_dev", methods=["POST"])
def ro_claim_analysis_dev():
    data = request.get_json(force=True)

    required_fields = ["ro_uri"]
    missing = [field for field in required_fields if field not in data]

    if missing:
        return (
            jsonify({"error": "Missing required fields", "missing_fields": missing}),
            400,
        )

    ro_uri = data["ro_uri"]
    rohub_endpoint = "https://rohub2020-devel.apps.bst2.paas.psnc.pl/api/ros/"

    ca_report = claim_analysis(
        ro_uri=ro_uri,
        rohub_endpoint=rohub_endpoint,
        claim_analysis_endpoint=CLAIM_ANALYSIS_ENDPOINT,
        verification_index_name=VERIFICATION_INDEX_NAME,
    )
    return jsonify(ca_report), 200
