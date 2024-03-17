<!-- Timetable.svelte -->
<script>
    export let timetableData = [];

    // You can include the formatTime function here or import it if it's defined elsewhere
</script>

<table>
    <thead>
        <tr>
            <th>Stop</th>
            <th colspan="100%">Times</th>
        </tr>
    </thead>
    <tbody>
        {#each timetableData as route}
            <tr>
                <td colspan="100%"><strong>{route.routeName}</strong></td>
            </tr>
            {#each route.stops as stop (stop.stopId)}
                <tr>
                    <td>{stopNameFromId(stop.stopId)}</td>
                    <td>{stop.formattedTime}</td>
                    <!-- Additional times here if needed -->
                </tr>
            {/each}
        {/each}
    </tbody>
</table>

<style>
    /* Your styles for the table here */
    table {
        width: 100%;
        border-collapse: collapse;
    }
    th, td {
        padding: 0.5rem;
        text-align: left;
        border: 1px solid #ddd;
    }
    th {
        background-color: #f5f5f5;
    }
</style>
