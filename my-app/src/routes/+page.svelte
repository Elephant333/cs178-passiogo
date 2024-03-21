<script>
    import { onMount } from "svelte";
    import maplibregl from "maplibre-gl";
    import Accordion, { Panel, Header, Content } from "@smui-extra/accordion";
    import IconButton, { Icon } from "@smui/icon-button";
    import Switch from "@smui/switch";
    // import Timetable from "./Timetable.svelte";

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
    let closestETATimes;
    let scheduleTimes;
    let closestScheduleTimes;
    let allEtasAfterClosest;
    let accordionItems = [];
    let toggledRoute = null; // track which routes to show, default to all
    let showAllRoutes = true; // show all routes by default
    let showDeveoper = false; // hide debug stuff by default

    let map;

    let timetableData = [];

    // Reactive statement to call updateNearestStopAnnouncement
    // whenever closestETATimes changes.
    $: if (closestETATimes?.length > 0) updateNearestStopAnnouncement();

    // This function updates the announcement for screen readers
    function updateNearestStopAnnouncement() {
        const announcementElement = document.getElementById("stopAnnouncement");
        if (announcementElement) {
            const nearestStop = closestETATimes[0].etaTimes[0];
            const etaMins = Math.floor(
                (nearestStop.etaTime * 1000 - Date.now()) / (1000 * 60),
            );
            const scheduleMins = Math.floor(
                (nearestStop.scheduledTime * 1000 - Date.now()) / (1000 * 60),
            );
            // console.log(closestETATimes[0])
            announcementElement.textContent = `Your nearest stop is ${stop_dict[nearestStop.stopId].stop_name} on route ${closestETATimes[0].routeName} , ETA is ${etaMins} mins away. Due to uncertainty, it could be betweenit ${etaMins} and ${scheduleMins} mins.`;
        }
    }

    onMount(() => {
        map = new maplibregl.Map({
            container: "map",
            style: "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
            center: [-71.1189, 42.3735],
            zoom: 13.75,
        });

        console.log("Loading arrow icon...");

        map.loadImage("/data/arrow-icon.png", (error, image) => {
            if (error) {
                console.error("Failed to load the arrow icon:", error);
                return;
            }
            console.log("Arrow icon loaded successfully.");
            map.addImage("arrow-icon", image);
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
            filterEtasAfterClosestEtas();
            createAccordionItems();
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

        async function fetchScheduleTimes() {
            try {
                const response = await fetch(
                    "/data/trip_allScheduleTimes.json",
                );
                scheduleTimes = await response.json();
            } catch (error) {
                console.error("Error fetching schedule data:", error);
            }
        }

        fetchData();
        fetchStops();
        fetchRoutes();
        fetchTripToRoute();
        fetchRouteToName();
        fetchStopToName();
        fetchScheduleTimes();

        const interval = setInterval(fetchData, 1000);

        return () => clearInterval(interval);
    });

    function displayRoutes() {
        routesData.forEach((route, index) => {
            const routeId = `route-${route.route_id}`;
            const arrowLayerId = `${routeId}-arrows`; // ID for the arrow layer

            // Remove existing arrow layer first
            if (map.getLayer(arrowLayerId)) {
                map.removeLayer(arrowLayerId);
            }

            // Remove existing route layer
            if (map.getLayer(routeId)) {
                map.removeLayer(routeId);
            }

            // Now, it's safe to remove the source as no layers are using it
            if (map.getSource(routeId)) {
                map.removeSource(routeId);
            }

            // Only display the route if its name matches the clicked route name
            if (
                route.route_long_name === toggledRoute ||
                (toggledRoute === null && showAllRoutes) ||
                (toggledRoute === null &&
                    !showAllRoutes &&
                    allETATimes.some(
                        (et) => et.routeName === route.route_long_name,
                    ))
            ) {
                // create a unique color for each route.
                const color = `hsl(${((index * 360) / routesData.length) % 360}, 100%, 50%)`;
                // Add the source for the new route
                map.addSource(routeId, {
                    type: "geojson",
                    data: {
                        type: "Feature",
                        properties: {},
                        geometry: {
                            type: "LineString",
                            coordinates: route.path,
                        },
                    },
                });

                // Add the route line layer
                map.addLayer({
                    id: routeId,
                    type: "line",
                    source: routeId,
                    layout: {
                        "line-join": "round",
                        "line-cap": "round",
                    },
                    paint: {
                        "line-color": color,
                        "line-width": 4,
                    },
                });

                // Add a symbol layer for arrows with the matching color
                map.addLayer({
                    id: arrowLayerId,
                    type: "symbol",
                    source: routeId, // Use the same source as the route line
                    layout: {
                        "symbol-placement": "line",
                        "symbol-spacing": 200, // Adjust as we need to avoid overlapping
                        "icon-image": "arrow-icon",
                        "icon-size": 0.5,
                        "icon-rotate": 0,
                        "icon-allow-overlap": false,
                        "icon-rotation-alignment": "map",
                        "icon-ignore-placement": true,
                        "icon-padding": 0,
                    },
                    paint: {
                        "icon-color": color, // Use the same color as the route line
                    },
                });
            }
        });
    }

    function routeClicked(routeName) {
        if (routeName === toggledRoute) {
            toggledRoute = null;
        } else {
            toggledRoute = routeName;
        }

        displayRoutes();
    }

    function toggleRoutes() {
        showAllRoutes = !showAllRoutes;
        displayRoutes();
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
                const tripId = entity.vehicle.trip.trip_id;
                const routeId = trip_to_route[tripId];
                const routeName = route_to_name[routeId];
                busIcon.title = routeName;

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
                navigator.geolocation.getCurrentPosition((position) => {
                    userCoordinates = [
                        position.coords.longitude,
                        position.coords.latitude,
                    ];
                });
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

            const uniqueETAs = {};
            entity?.trip_update?.stop_time_update?.forEach((stop) => {
                const stopId = stop.stop_id;
                const etaTime = stop.arrival.time;

                // Check if this ETA is a duplicate because the data is crappy
                const key = tripId + "-" + stopId;
                if (!uniqueETAs[key]) {
                    uniqueETAs[key] = true;
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

                    // Find scheduled time
                    let scheduledTime = etaTime + 2 * 60; // by default +2 if no other scheduled time is found
                    let scheduledTimeInSeconds;
                    const routeSchedule = scheduleTimes.find(
                        (schedule) => schedule.routeName === routeName,
                    );
                    const scheduleTimeEntry = routeSchedule?.scheduleTimes.find(
                        (schedule) =>
                            schedule.stopId === stopId &&
                            schedule.tripId === tripId,
                    ); // need to match both the trip ID and stop ID
                    // convert time string to timestamp
                    if (scheduleTimeEntry && scheduleTimeEntry.scheduleTime) {
                        scheduledTimeInSeconds =
                            convertScheduledTimeToTimestamp(
                                scheduleTimeEntry.scheduleTime,
                            );
                    }
                    if (scheduledTimeInSeconds > etaTime) {
                        scheduledTime = scheduledTimeInSeconds;
                    }
                    allETATimes[routeName].push({
                        stopId: stopId,
                        etaTime: etaTime,
                        tripId: tripId,
                        distanceToUser: distance,
                        scheduledTime: scheduledTime,
                    });
                }
            });
        });

        allETATimes = Object.entries(allETATimes).map(
            ([routeName, etaTimes]) => ({
                routeName,
                etaTimes,
            }),
        );
    }

    function formatTime(timestamp) {
        // Create a date object from the timestamp
        const date = new Date(timestamp * 1000);
        // Format it to local time string
        return date.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
            hour12: true,
        });
    }

    function filterClosestStopsToUser() {
        closestETATimes = [];

        const currentTimeInSeconds = Math.floor(Date.now() / 1000);

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

            // Filter out ETA times more than 2 minutes past the current time
            closestStopsETA = closestStopsETA.filter(
                (etaTime) => etaTime.etaTime - currentTimeInSeconds >= -2 * 60,
            );

            if (closestStopsETA.length > 0) {
                closestStopsETA.sort((a, b) => a.etaTime - b.etaTime);

                closestETATimes.push({
                    routeName: routeETA.routeName,
                    etaTimes: closestStopsETA,
                });
            }
        });
    }

    // helper function for console logging
    function logValue(label, value) {
        console.log(`${label}:`, value);
        return value;
    }

    function filterEtasAfterClosestEtas() {
        allEtasAfterClosest = [];

        allETATimes.forEach((routeETAs) => {
            closestETATimes.forEach((closestETA) => {
                const routeName = closestETA.routeName;
                const closestEta = closestETA.etaTimes[0];
                const tripId = closestETA.etaTimes[0].tripId;

                let etasAfterClosest = [];
                if (routeETAs.routeName === routeName) {
                    routeETAs.etaTimes.forEach((etaTime) => {
                        if (
                            etaTime.tripId === tripId &&
                            etaTime.etaTime > closestEta.etaTime
                        ) {
                            etasAfterClosest.push(etaTime);
                        }
                    });
                    etasAfterClosest.sort((a, b) => a.etaTime - b.etaTime);

                    allEtasAfterClosest.push({
                        routeName: routeName,
                        etaTimes: etasAfterClosest,
                    });
                }
            });
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

    function createAccordionItems() {
        accordionItems = closestETATimes.map((routeETA) => {
            const routeName = routeETA.routeName;
            const closestEtaTimes = routeETA.etaTimes.map((etaTime) => ({
                stopName: stop_dict[etaTime.stopId].stop_name,
                etaTime: etaTime.etaTime,
                scheduledTime: etaTime.scheduledTime,
            }));
            const allEtasAfterClosestTimes =
                allEtasAfterClosest
                    .find((item) => item.routeName === routeName)
                    ?.etaTimes.map((etaTime) => ({
                        stopName: stop_dict[etaTime.stopId].stop_name,
                        etaTime: etaTime.etaTime,
                    })) || [];

            return {
                routeName: routeName,
                closestEtaTimes: closestEtaTimes,
                allEtasAfterClosestTimes: allEtasAfterClosestTimes,
            };
        });
    }

    // handle inappropriate data of scheduledTimes
    function convertScheduledTimeToTimestamp(scheduledTime) {
        if (typeof scheduledTime === "string") {
            const [hours, minutes, seconds] = scheduledTime
                .split(":")
                .map(Number);
            const now = new Date();
            now.setHours(hours, minutes, seconds, 0);
            return now.getTime() / 1000; // from milliseconds to seconds
        } else {
            // Return a default timestamp (e.g., current time + 2 minutes) if scheduledTime is not a valid string
            // can be modified
            return Date.now() + 2 * 60 * 1000;
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
        <link
            href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap"
            rel="stylesheet"
        />
    </head>
    <body>
        <div class="container">
            <div class="sidebar">
                <div class="accordion-container">
                    <div
                        aria-live="polite"
                        class="visually-hidden"
                        id="stopAnnouncement"
                    ></div>
                    <div class="toggler">
                        <p>All Routes</p>
                        <Switch on:click={() => toggleRoutes()} icons={false} />
                        <p>Active Routes</p>
                    </div>
                    <h2>ETAs Nearest to You</h2>
                    <Accordion>
                        {#each accordionItems as item, index}
                            <Panel key={index}>
                                <Header
                                    on:click={() =>
                                        routeClicked(item.routeName)}
                                >
                                    <div class="panel-header">
                                        <span><strong>{item.routeName}</strong></span>
                                        <span
                                            >{item.closestEtaTimes[0]
                                                .stopName}</span
                                        >
                                        <span
                                            >{new Date(
                                                item.closestEtaTimes[0]
                                                    .etaTime * 1000,
                                            ).toLocaleTimeString([], {
                                                hour: "2-digit",
                                                minute: "2-digit",
                                            })}</span
                                        >
                                        <span>
                                            {Math.floor(
                                                (item.closestEtaTimes[0]
                                                    .etaTime *
                                                    1000 -
                                                    Date.now()) /
                                                    (1000 * 60),
                                            )} mins ({Math.floor(
                                                (item.closestEtaTimes[0]
                                                    .etaTime *
                                                    1000 -
                                                    Date.now()) /
                                                    (1000 * 60),
                                            )} -
                                            {Math.floor(
                                                (item.closestEtaTimes[0]
                                                    ?.scheduledTime *
                                                    1000 -
                                                    Date.now()) /
                                                    (1000 * 60),
                                            )} mins)
                                        </span>
                                    </div>
                                    <IconButton slot="icon">
                                        <Icon class="material-icons"
                                            >expand</Icon
                                        >
                                    </IconButton>
                                </Header>
                                <Content>
                                    <h3>Closest ETAs</h3>
                                    <ul>
                                        {#each item.closestEtaTimes as etaTime, index2}
                                            <li key={index2}>
                                                {etaTime.stopName} - {new Date(
                                                    etaTime.etaTime * 1000,
                                                ).toLocaleTimeString([], {
                                                    hour: "2-digit",
                                                    minute: "2-digit",
                                                })}
                                            </li>
                                        {/each}
                                    </ul>
                                    <h3>Subsequent Stops</h3>
                                    <ul>
                                        {#each item.allEtasAfterClosestTimes as etaTime, index2}
                                            <li key={index2}>
                                                {etaTime.stopName} - {new Date(
                                                    etaTime.etaTime * 1000,
                                                ).toLocaleTimeString([], {
                                                    hour: "2-digit",
                                                    minute: "2-digit",
                                                })}
                                            </li>
                                        {/each}
                                    </ul>
                                </Content>
                            </Panel>
                        {/each}
                    </Accordion>
                    <div class="toggler">
                        <Switch
                            on:click={() => (showDeveoper = !showDeveoper)}
                            icons={false}
                        />
                        <p>Developer Mode</p>
                    </div>
                </div>
                {#if showDeveoper}
                    <h2>ETAs Nearest to You</h2>
                    {#if trip_to_route && route_to_name && stop_dict}
                        {#each closestETATimes as routeETA}
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
                    <h2>ETAs After Closest</h2>
                    {#if trip_to_route && route_to_name && stop_dict}
                        {#each allEtasAfterClosest as routeETA}
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
                    <h2>All ETAs</h2>
                    {#if trip_to_route && route_to_name && stop_dict}
                        {#each allETATimes as routeETA}
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
                {/if}
            </div>
            <div id="map"></div>
        </div>
        <em>The numbers next to each bus indicate how recently the data was updated.</em>
        <!-- Timetable rendering -->
        <table>
            <thead>
                <tr>
                    <th>Stop</th>
                    <th>Live ETAs</th>
                    <th>Schedules</th>
                </tr>
            </thead>
            <tbody>
                {#each allETATimes as { routeName, etaTimes }}
                    <tr>
                        <td colspan="3"><strong>{routeName}</strong></td>
                    </tr>
                    {#each etaTimes as { stopId, etaTime, scheduledTime, tripId, distanceToUser }}
                        <tr>
                            <td>{stop_dict[stopId].stop_name}</td>
                            <td>{formatTime(etaTime)}</td>
                            <td>{formatTime(scheduledTime)}</td>
                        </tr>
                    {/each}
                {/each}
            </tbody>
        </table>
        {#if showDeveoper}
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
        {/if}
    </body>
</main>

<style>
    table {
        font-size: 0.8rem;
        width: 1420px;
        border-collapse: collapse;
    }

    /* Reduce padding in table cells */
    th,
    td {
        padding: 0.3rem;
        border: 1px solid #ccc;
        text-align: left;
    }

    /* table header styles */
    th {
        background-color: #f5f5f5;
    }

    /* table alternating rows */
    tr:nth-child(even) {
        background-color: #f2f2f2;
    }

    body {
        font-family: "Roboto", sans-serif;
    }

    .container {
        display: flex;
    }

    .sidebar {
        padding-left: 10px;
        padding-right: 10px;
        padding-top: 10px;
        width: 600px;
        height: 700px;
        background-color: lightgray;
        overflow-y: auto;
    }

    #map {
        width: 800px;
        height: 700px;
    }

    .panel-header {
        display: grid;
        grid-template-columns: 1fr 1fr;
        grid-template-rows: 1fr 1fr;
        grid-auto-flow: column;
    }

    .toggler {
        display: flex;
    }

    .visually-hidden {
        position: absolute;
        width: 1px;
        height: 1px;
        margin: -1px;
        padding: 0;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        border: 0;
    }
</style>
