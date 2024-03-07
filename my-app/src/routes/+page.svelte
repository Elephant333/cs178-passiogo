<script>
    import { onMount } from "svelte";
    import maplibregl from "maplibre-gl";

    let jsonData;
    let markers = [];

    onMount(() => {
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

        const interval = setInterval(fetchData, 3000);
        fetchData();

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
                // Explicitly set scaleFactor=2 in the call
                // and backgroundSize=contain to get better
                // Marker Icon quality with MapLibre GL
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
