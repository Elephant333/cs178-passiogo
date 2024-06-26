import pandas as pd
import json


def all_to_json():
    gtfs_files = {
        "routes": "../data/routes.txt",
        "shapes": "../data/shapes.txt",
        "stop_times": "../data/stop_times.txt",
        "stops": "../data/stops.txt",
        "trips": "../data/trips.txt",
    }

    # Define the output directory for the JSON files
    output_dir = "../data/json/"

    def convert_to_json(file_path, output_path):
        df = pd.read_csv(file_path)
        df.to_json(output_path, orient="records", lines=False)

    # Iterate over the GTFS files and convert each to JSON
    for file_type, file_path in gtfs_files.items():
        output_path = f"{output_dir}{file_type}.json"
        convert_to_json(file_path, output_path)
        print(f"Converted {file_type} to JSON at {output_path}")


routes_df = pd.read_csv("../data/routes.txt")
trips_df = pd.read_csv("../data/trips.txt")
shapes_df = pd.read_csv("../data/shapes.txt")
stops_df = pd.read_csv("../data/stops.txt")


def get_route_path():
    # merge trips with routes to link each trip with its corresponding route
    trips_routes_df = pd.merge(trips_df, routes_df, on="route_id")

    # get unique shape_ids for each route
    unique_shapes = trips_routes_df[["route_id", "shape_id"]].drop_duplicates()
    shapes_grouped = shapes_df.groupby("shape_id")

    routes_json = []

    for _, row in unique_shapes.iterrows():
        route_id = row["route_id"]
        shape_id = row["shape_id"]
        route_info = routes_df.loc[routes_df["route_id"] == route_id].iloc[0]
        shape_points = shapes_grouped.get_group(shape_id)[
            ["shape_pt_lon", "shape_pt_lat"]
        ].values.tolist()  # should be this order!!

        route_obj = {
            "route_id": int(route_id),
            "route_short_name": route_info["route_short_name"],
            "route_long_name": route_info["route_long_name"],
            "path": shape_points,
        }
        routes_json.append(route_obj)

    output_path = "../data/json/route_paths.json"
    pd.Series(routes_json).to_json(output_path, orient="values", indent=4)

    print(f"Generated routesLine.json at {output_path}")


def get_stops_geo():
    stops_json = stops_df.apply(
        lambda x: {"lngLat": [x["stop_lon"], x["stop_lat"]], "name": x["stop_name"]},
        axis=1,
    ).tolist()

    # Save stops to JSON
    stops_output_path = "../data/json/stops_geo.json"
    pd.Series(stops_json).to_json(stops_output_path, orient="values", indent=4)
    print(f"Generated stops.json at {stops_output_path}")


def trip_to_routeId():
    f = open("../data/json/trips.json")
    data = json.load(f)
    output_path = "../data/json/trip_to_routeId.json"
    trip_route_dict = {item["trip_id"]: item["route_id"] for item in data}
    with open(output_path, "w") as outfile:
        json.dump(trip_route_dict, outfile, indent=4)


def routeId_to_name():
    f = open("../data/json/routes.json")
    data = json.load(f)
    output_path = "../data/json/routeId_to_name.json"
    route_name_dict = {item["route_id"]: item["route_long_name"] for item in data}
    with open(output_path, "w") as outfile:
        json.dump(route_name_dict, outfile, indent=4)


def stopId_to_name():
    f = open("../data/json/stops.json")
    data = json.load(f)
    output_path = "../data/json/stop_dict.json"
    stop_dict = {
        item["stop_id"]: {
            "stop_name": item["stop_name"],
            "latitude": item["stop_lat"],
            "longitude": item["stop_lon"],
        }
        for item in data
    }
    with open(output_path, "w") as outfile:
        json.dump(stop_dict, outfile, indent=4)

trip_to_route = json.load(open("../static/data/trip_to_routeId.json"))
route_to_name = json.load(open("../static/data/routeId_to_name.json"))

def extract_scheduled_stop_times(trip_to_route, route_to_name):
    allScheduledTimes = {}

    with open("../data/stop_times.txt", 'r') as file:
        next(file)  # Skip header line
        for line in file:
            parts = line.strip().split(',')
            trip_id, arrival_time, _, stop_id = parts[:4]
            # print(type(trip_id)) str
            
            routeName = route_to_name.get(str(trip_to_route.get(trip_id)))
            # print(routeName)
            if routeName is None:
                continue  # Skip if routeName or trip_to_route mapping is missing
            
            if routeName not in allScheduledTimes:
                allScheduledTimes[routeName] = []
            
            allScheduledTimes[routeName].append({
                'stopId': stop_id,
                'scheduleTime': arrival_time,
                'tripId': trip_id,
            })
    
    # Converting to a list of dictionaries for each route
    allScheduledTimesList = [{'routeName': key, 'scheduleTimes': value} for key, value in allScheduledTimes.items()]
    output_path = "../static/data/trip_allScheduleTimes.json"
    with open(output_path, "w") as outfile:
        json.dump(allScheduledTimesList, outfile, indent=4)



# get_route_path()
# get_stops_geo()
# trip_to_routeId()
# routeId_to_name()
# stopId_to_name()
extract_scheduled_stop_times(trip_to_route, route_to_name)