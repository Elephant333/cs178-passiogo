<script>
    import { MapLibre } from "svelte-maplibre";
</script>

<main>
    <MapLibre
        center={[-71.1189, 42.3735]}
        zoom={13}
        class="map"
        standardControls
        style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
    />
</main>

<style>
    :global(.map) {
        height: 500px;
        width: 1000px;
    }
</style>
