<script>
    import { onMount } from "svelte";
    import maplibregl from "maplibre-gl";

    let jsonGPSData;
    let jsonETAData;
    let stopsData;
    let markers = []; // keep track of live vehicle markers
    let stopsMarkers = [];
    let routesData;
    let userCoordinates = [-71.12559, 42.36344]; // SEC coordinates
    let allETATimes = [];
    let trip_to_route;
    let route_to_name;
    let stop_dict;
    let filteredETATimes;

    let map;

    onMount(() => {
        map = new maplibregl.Map({
            container: "map",
            style: "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
            center: [-71.1189, 42.3735],
            zoom: 13.75,
        });

        // Old Maplibre user location button
        // let geolocate = new maplibregl.GeolocateControl({
        //     positionOptions: {
        //         enableHighAccuracy: true,
        //     },
        //     trackUserLocation: true,
        // });
        // map.addControl(geolocate);
        // geolocate.on("geolocate", function (event) {
        //     userCoordinates = [event.coords.longitude, event.coords.latitude];
        // });

        async function fetchGPSData() {
            try {
                const response = await fetch(
                    "https://passio3.com/harvard/passioTransit/gtfs/realtime/vehiclePositions.json",
                );
                jsonGPSData = await response.json();
            } catch (error) {
                console.error("Error fetching GPS JSON data:", error);
            }
        }

        async function fetchETAData() {
            try {
                const response = await fetch(
                    "https://passio3.com/harvard/passioTransit/gtfs/realtime/tripUpdates.json",
                );
                jsonETAData = await response.json();
            } catch (error) {
                console.error("Error fetching ETA JSON data:", error);
            }
        }

        async function fetchData() {
            fetchGPSData();
            fetchETAData();
            updateMarkers();
            extractStopETATimes();
            filterClosestStopsToUser();
        }

        async function fetchStops() {
            try {
                const response = await fetch("/data/stops_geo.json"); // data was placed under static/data
                stopsData = await response.json();
                displayStops();
            } catch (error) {
                console.error("Error fetching stops data:", error);
            }
        }

        async function fetchRoutes() {
            try {
                const response = await fetch("/data/route_paths.json");
                routesData = await response.json();
                displayRoutes();
            } catch (error) {
                console.error("Error fetching routes data:", error);
            }
        }

        async function fetchTripToRoute() {
            try {
                const response = await fetch("/data/trip_to_routeId.json");
                trip_to_route = await response.json();
            } catch (error) {
                console.error("Error fetching trip to route data:", error);
            }
        }

        async function fetchRouteToName() {
            try {
                const response = await fetch("/data/routeId_to_name.json");
                route_to_name = await response.json();
            } catch (error) {
                console.error("Error fetching route to name data:", error);
            }
        }

        async function fetchStopToName() {
            try {
                const response = await fetch("/data/stop_dict.json");
                stop_dict = await response.json();
            } catch (error) {
                console.error("Error fetching stop to name data:", error);
            }
        }

        fetchData();
        fetchStops();
        fetchRoutes();
        fetchTripToRoute();
        fetchRouteToName();
        fetchStopToName();

        const interval = setInterval(fetchData, 1000);

        return () => clearInterval(interval);
    });

    function displayRoutes() {
        routesData.forEach((route, index) => {
            const routeId = `route-${route.route_id}`;

            // check if the layer already exists
            if (map.getLayer(routeId)) {
                // if it does, remove the layer and its source
                map.removeLayer(routeId);
                map.removeSource(routeId); // also remove the source
            }

            // create a unique color for each route.
            const color = `hsl(${((index * 360) / routesData.length) % 360}, 100%, 50%)`;
            map.addLayer({
                id: routeId,
                type: "line",
                source: {
                    type: "geojson",
                    data: {
                        type: "Feature",
                        properties: {},
                        geometry: {
                            type: "LineString",
                            coordinates: route.path,
                        },
                    },
                },
                layout: {
                    "line-join": "round",
                    "line-cap": "round",
                },
                paint: {
                    "line-color": color,
                    "line-width": 4,
                },
            });
        });
    }

    function updateMarkers() {
        if (jsonGPSData && jsonGPSData.entity) {
            markers.forEach((marker) => marker.remove());
            markers = [];

            const currentTime = Date.now() / 1000;

            jsonGPSData.entity.forEach((entity) => {
                var busIcon = document.createElement("div");
                busIcon.style.width = "20px";
                busIcon.style.height = "20px";
                busIcon.style.backgroundSize = "contain";
                busIcon.style.backgroundImage = "url(/data/../uparrow.png)"; // confusued why this /../ is needed
                busIcon.style.cursor = "pointer";

                const dataTimestamp = entity.vehicle.timestamp;

                const freshness = Math.max(
                    0,
                    Math.floor(currentTime - dataTimestamp),
                );

                var freshnessText = document.createElement("div");
                freshnessText.textContent = freshness + "s";
                freshnessText.style.fontSize = "12px";
                freshnessText.style.color = "black";
                freshnessText.style.textAlign = "center";
                freshnessText.style.marginLeft = "20px";

                const bus_loc = entity.vehicle.position;
                const lngLat = [bus_loc.longitude, bus_loc.latitude];

                const busMarker = new maplibregl.Marker({ element: busIcon })
                    .setLngLat(lngLat)
                    .addTo(map);
                busMarker.setRotation(bus_loc.bearing);
                markers.push(busMarker);

                const textMarker = new maplibregl.Marker({
                    element: freshnessText,
                })
                    .setLngLat(lngLat)
                    .addTo(map);
                markers.push(textMarker);
            });

            if (navigator.geolocation) {
                // navigator.geolocation.getCurrentPosition((position) => {
                //     userCoordinates = [
                //         position.coords.longitude,
                //         position.coords.latitude,
                //     ];
                // });
                var largerCircleIcon = document.createElement("div");
                largerCircleIcon.style.width = "20px";
                largerCircleIcon.style.height = "20px";
                largerCircleIcon.style.borderRadius = "50%";
                largerCircleIcon.style.backgroundColor = "lightblue";
                largerCircleIcon.style.opacity = "0.5"; // Lighter opacity
                largerCircleIcon.style.pointerEvents = "none"; // To avoid interaction

                const largerCircleMarker = new maplibregl.Marker({
                    element: largerCircleIcon,
                })
                    .setLngLat(userCoordinates)
                    .addTo(map);
                markers.push(largerCircleMarker);

                var userLocationIcon = document.createElement("div");
                userLocationIcon.style.width = "10px";
                userLocationIcon.style.height = "10px";
                userLocationIcon.style.borderRadius = "50%";
                userLocationIcon.style.backgroundColor = "blue";
                largerCircleIcon.style.opacity = "0.75"; // Lighter opacity
                userLocationIcon.style.cursor = "pointer";

                const userLocationMarker = new maplibregl.Marker({
                    element: userLocationIcon,
                })
                    .setLngLat(userCoordinates)
                    .addTo(map);
                markers.push(userLocationMarker);
            }
        }
    }

    function extractStopETATimes() {
        allETATimes = [];

        jsonETAData?.entity?.forEach((entity) => {
            const tripId = entity.trip_update.trip.trip_id;
            const routeName = route_to_name[trip_to_route[tripId]];
            if (!allETATimes[routeName]) {
                allETATimes[routeName] = [];
            }

            entity?.trip_update?.stop_time_update?.forEach((stop) => {
                const stopId = stop.stop_id;
                const etaTime = stop.arrival.time;
                const stopCoordinates = [
                    stop_dict[stopId].longitude,
                    stop_dict[stopId].latitude,
                ];
                if (!stopCoordinates) return; // Skip if coordinates not found
                const [stopLng, stopLat] = stopCoordinates;
                const [userLng, userLat] = userCoordinates;
                // Calculate distance between user and stop
                const distance = Math.sqrt(
                    Math.pow(stopLng - userLng, 2) +
                        Math.pow(stopLat - userLat, 2),
                );
                allETATimes[routeName].push({
                    stopId: stopId,
                    etaTime: etaTime,
                    tripId: tripId,
                    distanceToUser: distance,
                });
            });
        });

        allETATimes = Object.entries(allETATimes).map(
            ([routeName, etaTimes]) => ({
                routeName,
                etaTimes,
            }),
        );
    }

    function filterClosestStopsToUser() {
        filteredETATimes = [];

        allETATimes.forEach((routeETA) => {
            let closestStopsETA = [];
            let closestStopDistance = Infinity;

            routeETA.etaTimes.forEach((etaTime) => {
                if (etaTime.distanceToUser < closestStopDistance) {
                    closestStopDistance = etaTime.distanceToUser;
                    closestStopsETA = [etaTime];
                } else if (etaTime.distanceToUser === closestStopDistance) {
                    closestStopsETA.push(etaTime);
                }
            });

            if (closestStopsETA.length > 0) {
                filteredETATimes.push({
                    routeName: routeETA.routeName,
                    etaTimes: closestStopsETA,
                });
            }
        });
    }

    function displayStops() {
        if (stopsData) {
            stopsData.forEach((stop) => {
                var stopIcon = document.createElement("div");
                stopIcon.style.width = "15px";
                stopIcon.style.height = "15px";
                stopIcon.style.borderRadius = "50%";
                stopIcon.style.backgroundColor = "gray";
                stopIcon.title = stop.name;
                stopIcon.style.cursor = "pointer";
                const marker = new maplibregl.Marker({ element: stopIcon })
                    .setLngLat(stop.lngLat)
                    .addTo(map);
                stopsMarkers.push(marker);
            });
        }
    }
</script>

<main>
    <head>
        <script
            src="https://unpkg.com/maplibre-gl@latest/dist/maplibre-gl.js"
        ></script>
        <link
            href="https://unpkg.com/maplibre-gl@latest/dist/maplibre-gl.css"
            rel="stylesheet"
        />
    </head>
    <body>
        <div class="container">
            <div class="sidebar">
                <h2>Stop ETA Times</h2>
                {#if trip_to_route && route_to_name && stop_dict}
                    {#each filteredETATimes as routeETA}
                        <h3>{routeETA.routeName}</h3>
                        <ul>
                            {#each routeETA.etaTimes as etaTime}
                                <li>
                                    {stop_dict[etaTime.stopId].stop_name} - {new Date(
                                        etaTime.etaTime * 1000,
                                    ).toLocaleTimeString([], {
                                        hour: "2-digit",
                                        minute: "2-digit",
                                    })}
                                </li>
                            {/each}
                        </ul>
                    {/each}
                {:else}
                    <p>Loading...</p>
                {/if}
            </div>
            <div id="map"></div>
        </div>
        <h2>User Coordinates</h2>
        {#if userCoordinates}
            <p>Longitude: {userCoordinates[0]}</p>
            <p>Latitude: {userCoordinates[1]}</p>
        {:else}
            <p>Click the GPS button...</p>
        {/if}
        <h2>ETA Data</h2>
        {#if jsonETAData}
            <div>
                <!-- Render your JSON data here -->
                <pre>{JSON.stringify(jsonETAData, null, 2)}</pre>
            </div>
        {:else}
            <p>Loading...</p>
        {/if}
        <h2>GPS Data</h2>
        {#if jsonGPSData}
            <div>
                <!-- Render your JSON data here -->
                <pre>{JSON.stringify(jsonGPSData, null, 2)}</pre>
            </div>
        {:else}
            <p>Loading...</p>
        {/if}
    </body>
</main>

<style>
    .container {
        display: flex;
    }

    .sidebar {
        padding-left: 20px;
        width: 400px;
        height: 700px;
        background-color: lightgray;
        overflow-y: auto;
    }

    #map {
        width: 800px;
        height: 700px;
    }
</style>
