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
    {#if jsonData}
        <div>
            <!-- Render your JSON data here -->
            {#each Object.keys(jsonData) as key}
                <p>{key}: {JSON.stringify(jsonData[key])}</p>
            {/each}
        </div>
    {:else}
        <p>Loading...</p>
    {/if}
</main>
