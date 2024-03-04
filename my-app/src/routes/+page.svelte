<script>
    let jsonData;

    async function fetchData() {
        try {
            const response = await fetch(
                "https://passio3.com/harvard/passioTransit/gtfs/realtime/vehiclePositions.json",
            );
            jsonData = await response.json();
        } catch (error) {
            console.error("Error fetching JSON data:", error);
        }
    }

    fetchData();
</script>

<main>
    <head>
        <link
            rel="stylesheet"
            href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css"
        />
    </head>
    <div id="map"></div>
    <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
    <script>
        // Map initialization
        var map = L.map('map').setView([51.505, -0.09], 13);
        L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
            maxZoom: 19,
            attribution:
                '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        }).addTo(map);
    </script>
    {#if jsonData}
        <div>
            <!-- Render your JSON data here -->
            <pre>{JSON.stringify(jsonData, null, 2)}</pre>
        </div>
    {:else}
        <p>Loading...</p>
    {/if}
</main>

<style>
    #map {
        height: 500px;
    }
</style>
