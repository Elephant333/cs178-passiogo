<script>
    import L from "leaflet";
    var map = L.map("map").setView([51.505, -0.09], 13);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution:
            '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(map);

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
    <link
        rel="stylesheet"
        href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
        integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
        crossorigin=""
    />
    <!-- Make sure you put this AFTER Leaflet's CSS -->
    <script
        src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
        integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
        crossorigin=""
    ></script>
    <div id="map"></div>
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
        height: 180px;
    }
</style>
