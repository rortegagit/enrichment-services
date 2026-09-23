import os
from collections import defaultdict

import requests


def aggregate_doc_results(results):
    global_results = defaultdict(list)
    for res in results:
        for k, v in res["response"].items():
            for e in v:
                e.pop('appearances', None)
            global_results[k].extend(v)
    ro_results = defaultdict(list)

    # TOPICS DOMAINS
    elems = global_results["topic_domains"]
    if len(elems) == 0:
        ro_results["topic_domains"] = []
    else:
        elem_set = set([x["topic"] for x in elems])
        for e in elem_set:
            scores = [x["score"] for x in elems if x["topic"] == e]
            norm_scores = [x["normScore"] for x in elems if x["topic"] == e]
            ro_results["topic_domains"].append(
                {
                    "topic": e,
                    "score": sum(scores) / len(scores),
                    "normScore": sum(norm_scores) / len(norm_scores),
                }
            )

    # TOPIC_NASA, TOPIC_FORS...
    for elem_key in ["topic_fors", "topic_nasa"]:
        elems = global_results[elem_key]
        topic_dict = defaultdict(list)
        for e in elems:
            topic = e["topic"]
            for subtopic in e["subtopics"]:
                if subtopic not in topic_dict[topic]:
                    topic_dict[topic].append(subtopic)
        for topic, subtopics in topic_dict.items():
            ro_results[elem_key].append(
                {
                    "topic": topic,
                    "subtopics": subtopics,
                }
            )
    # KES
    for elem_key in [
        "ke_sentences",
        "ke_lemmas",
        "ke_phrases",
        "ke_concepts",
    ]:
        elems = global_results[elem_key]
        if len(elems) == 0:
            ro_results[elem_key] = []
        else:
            elem_set = set([x["key_element"] for x in elems])
            for e in elem_set:
                scores = [x["score"] for x in elems if x["key_element"] == e]
                norm_scores = [x["normScore"] for x in elems if x["key_element"] == e]
                ro_results[elem_key].append(
                    {
                        "key_element": e,
                        "score": sum(scores) / len(scores),
                        "normScore": sum(norm_scores) / len(norm_scores),
                    }
                )

    # TOPIC_IPTCS, ENTITIES...
    for elem_key in [
        "topic_iptcs",
        "entity_organizations",
        "entity_locations",
        "entity_timerefs",
        "entity_people",
        "entity_datacubes",
    ]:
        elems = global_results[elem_key]
        if len(elems) == 0:
            ro_results[elem_key] = []
        else:
            for e in elems:
                if e not in ro_results[elem_key]:
                    ro_results[elem_key].append(e)

    # TAGS
    for elem_key in ["tags_fcid"]:
        elems = global_results[elem_key]
        if len(elems) == 0:
            ro_results[elem_key] = []
        else:
            tag_dict = defaultdict(list)
            for e in elems:
                if e["value"] not in tag_dict[e["tag"]]:
                    tag_dict[e["tag"]].append(e["value"])
            for tag_type, values in tag_dict.items():
                ro_results[elem_key].append({"tag": tag_type, "values": values})
    return {k: v for k, v in sorted(ro_results.items())}


def ro_enrichment(ro_uri, rohub_endpoint, doc_enrichment_endpoint):
    title_desc = get_title_desc_as_file(ro_uri, rohub_endpoint)
    resources = get_resources(ro_uri, rohub_endpoint)
    filenames = [title_desc] + resources
    results = []
    processed_resources = []
    for i, filename in enumerate(filenames):
        print(f"Processing document {i+1}/{len(filenames)}: {filename}...")
        with open(filename, "rb") as f:
            payload = {}
            files = [("file", (filename, f, "text/plain"))]
            headers = {}
            response = requests.request(
                "POST",
                doc_enrichment_endpoint,
                headers=headers,
                data=payload,
                files=files,
            )
            document_annotation = response.json()
        results.append(document_annotation)
        processed_resources.append(
            {"filename": filename, "status_code": document_annotation["status_code"]}
        )
        os.remove(filename)
    ro_results = aggregate_doc_results(results)
    return {"results": ro_results, "processed_resources": processed_resources}


def get_title_desc_as_file(ro_uri, rohub_endpoint):
    ro_id = ro_uri.split("/")[-1]
    filename = f"{ro_id}_titledesc.txt"
    ro_endpoint = rohub_endpoint + ro_id
    title_desc_str = get_title_desc(ro_endpoint)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(title_desc_str)
    return filename


def get_title_desc(ro_endpoint):
    print(ro_endpoint)
    r = requests.get(ro_endpoint)
    response = r.json()
    title_desc_str = response["title"] + " " + response["description"]
    return title_desc_str


def get_resources(ro_uri, rohub_endpoint):
    ro_id = ro_uri.split("/")[-1]
    r = requests.get(rohub_endpoint + ro_id + "/resources")
    response = r.json()
    filenames = []
    for resource in response["results"]:
        download_url = resource["download_url"]
        if download_url.startswith("https://www.github.com/"):
            download_url = download_url.replace(
                "https://www.github.com/", "https://raw.githubusercontent.com/"
            )
            download_url = download_url + "/master/README.md"
        if download_url.startswith("https://box.everest.psnc.pl"):
            download_url = download_url + "?dl=1"
        r2 = requests.get(download_url)
        headers = r2.headers
        if "Content-Disposition" in headers:
            filename = (
                headers["Content-Disposition"].split("filename=")[1].replace('"', "")
            )
            if filename.split(".")[-1] in {
                ".doc",
                ".docx",
                ".pptx",
                ".pdf",
                ".txt",
                ".md",
                ".ipynb",
            }:
                filenames.append(filename)
                print(f"Downloading {filename}...")
                with open(filename, "wb") as f:
                    f.write(r2.content)
    return filenames


def get_bearer_token(callback):
    if callback.startswith("https://rohub2020-devel.apps.bst2.paas.psnc.pl"):
        base_url = "https://keycloak-dev.apps.paas-dev.psnc.pl/auth/realms/rohub/protocol/openid-connect/token"
        username = os.environ.get("API_USER")
        password = os.environ.get("API_PASSWORD_DEV")
    else:
        base_url = (
            "https://login.rohub.org/auth/realms/rohub/protocol/openid-connect/token"
        )
        username = os.environ.get("API_USER")
        password = os.environ.get("API_PASSWORD")
    data = (
        "client_id="
        + username
        + "&client_secret="
        + password
        + "&grant_type=client_credentials"
    )
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }
    response = requests.post(url=base_url, data=data, headers=headers)
    return response.json()["access_token"]
