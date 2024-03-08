import pandas as pd

def all_to_json():
    gtfs_files = {
        "routes": "../data/routes.txt",
        "shapes": "../data/shapes.txt",
        "stop_times": "../data/stop_times.txt",
        "stops": "../data/stops.txt",
        "trips": "../data/trips.txt"
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


routes_df = pd.read_csv('../data/routes.txt')
trips_df = pd.read_csv('../data/trips.txt')
shapes_df = pd.read_csv('../data/shapes.txt')
stops_df = pd.read_csv('../data/stops.txt')


def get_route_path():
    # merge trips with routes to link each trip with its corresponding route
    trips_routes_df = pd.merge(trips_df, routes_df, on='route_id')

    # get unique shape_ids for each route
    unique_shapes = trips_routes_df[['route_id', 'shape_id']].drop_duplicates()
    shapes_grouped = shapes_df.groupby('shape_id')

    routes_json = []

    for _, row in unique_shapes.iterrows():
        route_id = row['route_id']
        shape_id = row['shape_id']
        route_info = routes_df.loc[routes_df['route_id'] == route_id].iloc[0]
        shape_points = shapes_grouped.get_group(shape_id)[['shape_pt_lon', 'shape_pt_lat']].values.tolist() # should be this order!!
        
        route_obj = {
            "route_id": int(route_id),
            "route_short_name": route_info['route_short_name'],
            "route_long_name": route_info['route_long_name'],
            "path": shape_points
        }
        routes_json.append(route_obj)

    output_path = '../data/json/route_paths.json'
    pd.Series(routes_json).to_json(output_path, orient="values", indent=4)

    print(f"Generated routesLine.json at {output_path}")

def get_stops_geo():
    stops_json = stops_df.apply(lambda x: {
        "lngLat": [x['stop_lon'], x['stop_lat']],
        "name": x['stop_name']
    }, axis=1).tolist()

    # Save stops to JSON
    stops_output_path = '../data/json/stops_geo.json'
    pd.Series(stops_json).to_json(stops_output_path, orient="values", indent=4)
    print(f"Generated stops.json at {stops_output_path}")

get_route_path()