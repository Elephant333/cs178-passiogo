<script>
    import { onMount } from "svelte";

    var jsonData;
    var bus_loc;

    onMount(() => {
        async function fetchData() {
            try {
                const response = await fetch(
                    "https://passio3.com/harvard/passioTransit/gtfs/realtime/vehiclePositions.json",
                );
                jsonData = await response.json();
                bus_loc = jsonData.entity[0].vehicle.position;
                bus_loc = [bus_loc.longitude, bus_loc.latitude];
                setMarker();
            } catch (error) {
                console.error("Error fetching JSON data:", error);
            }
        }

        const interval = setInterval(fetchData, 3000);
        fetchData();

        return () => clearInterval(interval);
    });

    function setMarker() {
        if (bus_loc) {
            var marker = new maplibregl.Marker().setLngLat(bus_loc).addTo(map);
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
        <div id="map" style="width: 1000px; height: 500px;"></div>
        <script>
            var map = new maplibregl.Map({
                container: "map",
                style: "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json", // stylesheet location
                center: [-71.1189, 42.3735], // starting position [lng, lat]
                zoom: 13, // starting zoom
            });
        </script>
        {#if jsonData}
            <p>{bus_loc}</p>
            <div>
                <!-- Render your JSON data here -->
                <pre>{JSON.stringify(jsonData, null, 2)}</pre>
            </div>
        {:else}
            <p>Loading...</p>
        {/if}
    </body>
</main>
