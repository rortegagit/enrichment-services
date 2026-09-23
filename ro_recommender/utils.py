import requests


def get_recommendation_query(ros, authors, rohub_endpoint):
    ro_ids = []
    for ro in ros:
        if ro.endswith("/"):
            ro = ro[:-1]
        ro_ids.append(ro.split("/")[-1])
    for author in authors:
        author_ro_ids = get_ros_from_author(author, rohub_endpoint)
        for ro_id in author_ro_ids:
            if ro_id not in ros:
                ro_ids.append(ro_id)

    context_concepts = []
    context_places = []
    for ro_id in ro_ids:
        try:
            ro_info = get_ro_metadata(ro_id, rohub_endpoint)
        except KeyError:
            print(f"Not valid RO: {ro_id}")
            continue
        for concept in ro_info["concepts"]:
            if concept not in context_concepts:
                context_concepts.append(concept["name"])
        for place in ro_info["locations"]:
            if place not in context_places:
                context_places.append(place["name"])
    return context_concepts, context_places


def get_ros_from_author(author, rohub_endpoint):
    user_id = requests.get(rohub_endpoint + "search/users/?username=" + author).json()[
        "results"
    ][0]["identifier"]
    results = requests.get(rohub_endpoint + "users/" + user_id + "/ros/").json()[
        "results"
    ]
    return [x["identifier"] for x in results]


def get_ro_metadata(ro_id, rohub_endpoint):
    response = requests.get(rohub_endpoint + "ros/" + ro_id + "/full")
    return response.json()["metadata"]


def get_related_ros(concepts, places, rohub_endpoint):
    query = rohub_endpoint + "search/ros/?"
    for place in places:
        query = query + "locations=" + place + "&"
    for concept in concepts:
        query = query + "keywords=" + concept + "&"
    query = query + "use_or_operator=true&minimum_matched_objects=3"
    results = requests.get(query).json()["results"]
    return [x["shared_link"] for x in results][:10]
