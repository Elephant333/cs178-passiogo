<script>
    import { MapLibre } from "svelte-maplibre";
    import { onMount } from "svelte";

    let jsonData;
    let bus_loc;

    onMount(() => {
        async function fetchData() {
            try {
                const response = await fetch(
                    "https://passio3.com/harvard/passioTransit/gtfs/realtime/vehiclePositions.json",
                );
                jsonData = await response.json();
                bus_loc = jsonData.entity[0].vehicle.position;
                bus_loc = [bus_loc.longitude, bus_loc.latitude];
            } catch (error) {
                console.error("Error fetching JSON data:", error);
            }
        }

        const interval = setInterval(fetchData, 3000);
        fetchData();

        return () => clearInterval(interval);
    });
</script>

<main>
    <MapLibre
        center={[-71.1189, 42.3735]}
        zoom={13}
        class="map"
        standardControls
        style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
    >
    </MapLibre>
    {#if jsonData}
        <p>{bus_loc}</p>
        <div>
            <!-- Render your JSON data here -->
            <pre>{JSON.stringify(jsonData, null, 2)}</pre>
        </div>
    {:else}
        <p>Loading...</p>
    {/if}
</main>

<style>
    :global(.map) {
        height: 500px;
        width: 1000px;
    }
</style>
