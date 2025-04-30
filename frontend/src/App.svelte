<script>
    import { Router, Route } from "svelte-routing";
    import Home from "./routes/+page.svelte";
    import "./styles/page.css";
</script>

<Router>
    <div class="app">
        <Route path="/" component={Home} />
        <!-- Add more routes as needed -->
    </div>
</Router>

<style>
    :global(html, body) {
        width: 100%;
        height: 100%;
        margin: 0;
        padding: 0;
        font-family:
            "Afacad Flux",
            system-ui,
            -apple-system,
            BlinkMacSystemFont,
            "Segoe UI",
            Roboto,
            Oxygen,
            Ubuntu,
            Cantarell,
            "Open Sans",
            "Helvetica Neue",
            sans-serif;
    }

    .app {
        width: 100%;
        height: 100%;
    }
</style>
