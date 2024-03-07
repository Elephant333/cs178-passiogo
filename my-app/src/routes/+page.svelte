<script>
    import { onMount } from "svelte";
    import maplibregl from "maplibre-gl";

    let jsonData; 
    let stopsData; 
    let markers = []; // keep track of live vehicle markers
    let stopsMarkers = []; 

    let map;

    onMount(() => {
        map = new maplibregl.Map({
            container: "map",
            style: "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
            center: [-71.1189, 42.3735],
            zoom: 14,
        });

        async function fetchData() {
            try {
                const response = await fetch(
                    "https://passio3.com/harvard/passioTransit/gtfs/realtime/vehiclePositions.json",
                );
                jsonData = await response.json();
                updateMarkers();
            } catch (error) {
                console.error("Error fetching JSON data:", error);
            }
        }

        async function fetchStops() {
            try {
                const response = await fetch('/data/stops_geo.json'); // data was placed under static/data
                stopsData = await response.json();
                displayStops();
            } catch (error) {
                console.error("Error fetching stops data:", error);
            }
        }
       
        fetchData();
        fetchStops();

        const interval = setInterval(fetchData, 3000);

        return () => clearInterval(interval);
    });

    function updateMarkers() {
        if (jsonData && jsonData.entity) {
            markers.forEach((marker) => marker.remove());
            markers = [];

            jsonData.entity.forEach((entity) => {
                var busIcon = document.createElement("div");
                busIcon.style.width = "25px";
                busIcon.style.height = "25px";
                busIcon.style.backgroundSize = "contain";
                busIcon.style.backgroundImage =
                "url(https://upload.wikimedia.org/wikipedia/commons/thumb/c/c0/Eo_circle_green_arrow-up.svg/2048px-Eo_circle_green_arrow-up.svg.png)";
                busIcon.style.cursor = "pointer";
                const bus_loc = entity.vehicle.position;
                const lngLat = [bus_loc.longitude, bus_loc.latitude];
                const marker = new maplibregl.Marker({ element: busIcon })
                    .setLngLat(lngLat)
                    .addTo(map);
                marker.setRotation(bus_loc.bearing);
                markers.push(marker);
            });
        }
    }

    function displayStops() {
        if (stopsData) {
            stopsData.forEach((stop) => {
                var stopIcon = document.createElement("div");
                stopIcon.style.width = "15px";
                stopIcon.style.height = "15px";
                stopIcon.style.borderRadius = "50%";
                stopIcon.style.backgroundColor = "pink";
                stopIcon.title = stop.name; 
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
        <div id="map" style="width: 800px; height: 700px;"></div>
        <script>
            var map = new maplibregl.Map({
                container: "map",
                style: "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json", // stylesheet location
                center: [-71.1189, 42.3735], // starting position [lng, lat]
                zoom: 14, // starting zoom
            });
        </script>
        {#if jsonData}
            <div>
                <!-- Render your JSON data here -->
                <pre>{JSON.stringify(jsonData, null, 2)}</pre>
            </div>
        {:else}
            <p>Loading...</p>
        {/if}
    </body>
</main>
