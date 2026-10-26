import assert from "node:assert/strict";
import { test } from "node:test";
import { createDataClient } from "./dataClient.js";

function setup(t) {
    t.mock.timers.enable({ apis: ["setTimeout"] });
    const changes = [];
    const client = createDataClient(new Map(), {
        backendBaseUrl: "https://backend.example/",
        onBackendDelayChange: (delayed) => changes.push(delayed),
    });
    t.after(() => client.dispose());
    return { client, changes };
}

const response = (value) => ({ ok: true, json: async () => value });

const operations = [
    ["catalog", (client) => client.loadCoursesPage(0), "/api/v1/courses?limit=200&offset=0"],
    ["detail", (client) => client.fetchBackendCourseDetail("CMSC433"), "/api/v1/courses/CMSC433"],
    ["schedules", (client) => client.generateSchedules({ required_courses: ["CMSC433"] }), "/api/v1/schedules"],
];

for (const [name, run, path] of operations) {
    test(`${name}: shows the notice at 3 seconds and clears it on completion`, async (t) => {
        const { client, changes } = setup(t);
        const pending = Promise.withResolvers();
        const fetch = t.mock.method(globalThis, "fetch", () => pending.promise);
        const request = run(client);
        assert.equal(fetch.mock.calls[0].arguments[0], `https://backend.example${path}`);
        if (name === "schedules") {
            const init = fetch.mock.calls[0].arguments[1];
            assert.equal(init.method, "POST");
            assert.equal(init.headers["Content-Type"], "application/json");
            assert.deepEqual(JSON.parse(init.body), { required_courses: ["CMSC433"] });
        }
        t.mock.timers.tick(2999);
        assert.deepEqual(changes, []);
        t.mock.timers.tick(1);
        assert.deepEqual(changes, [true]);
        pending.resolve(response([]));
        assert.deepEqual(await request, []);
        assert.deepEqual(changes, [true, false]);
        t.mock.timers.tick(3000);
        assert.deepEqual(changes, [true, false]);
    });
}

test("fast responses never show a delayed notice", async (t) => {
    const { client, changes } = setup(t);
    const pending = Promise.withResolvers();
    t.mock.method(globalThis, "fetch", () => pending.promise);
    const request = client.loadCoursesPage(0);
    t.mock.timers.tick(2999);
    pending.resolve(response([]));
    await request;
    t.mock.timers.tick(3000);
    assert.deepEqual(changes, []);
});

test("tracking includes reading the response body", async (t) => {
    const { client, changes } = setup(t);
    const body = Promise.withResolvers();
    t.mock.method(globalThis, "fetch", async () => ({ ok: true, json: () => body.promise }));
    const request = client.loadCoursesPage(0);
    await Promise.resolve();
    t.mock.timers.tick(3000);
    assert.deepEqual(changes, [true]);
    body.resolve([]);
    await request;
    assert.deepEqual(changes, [true, false]);
});

test("concurrent slow requests share one notice until the last one finishes", async (t) => {
    const { client, changes } = setup(t);
    const first = Promise.withResolvers();
    const second = Promise.withResolvers();
    const queue = [first, second];
    t.mock.method(globalThis, "fetch", () => queue.shift().promise);
    const catalog = client.loadCoursesPage(0);
    const detail = client.fetchBackendCourseDetail("CMSC433");
    t.mock.timers.tick(3000);
    assert.deepEqual(changes, [true]);
    first.resolve(response([]));
    await catalog;
    assert.deepEqual(changes, [true]);
    second.resolve(response({ course_code: "CMSC433" }));
    await detail;
    assert.deepEqual(changes, [true, false]);
});

test("a fast request cannot close the notice for a slow request", async (t) => {
    const { client, changes } = setup(t);
    const slow = Promise.withResolvers();
    t.mock.method(globalThis, "fetch", () => slow.promise);
    const request = client.loadCoursesPage(0);
    t.mock.timers.tick(3000);
    globalThis.fetch = async () => response({ course_code: "CMSC433" });
    await client.fetchBackendCourseDetail("CMSC433");
    assert.deepEqual(changes, [true]);
    slow.resolve(response([]));
    await request;
    assert.deepEqual(changes, [true, false]);
});

for (const failure of ["network", "json"]) {
    test(`${failure} failures clear the delayed notice`, async (t) => {
        const { client, changes } = setup(t);
        const pending = Promise.withResolvers();
        t.mock.method(globalThis, "fetch", () => pending.promise);
        const request = client.loadCoursesPage(0);
        const rejected = assert.rejects(request, /broken/);
        t.mock.timers.tick(3000);
        if (failure === "network") pending.reject(new Error("broken network"));
        else pending.resolve({ ok: true, json: async () => { throw new Error("broken JSON"); } });
        await rejected;
        assert.deepEqual(changes, [true, false]);
    });
}

test("HTTP errors keep the schedule detail and existing fallback messages", async (t) => {
    const { client, changes } = setup(t);
    t.mock.method(globalThis, "fetch", async () => ({
        ok: false, status: 422, json: async () => ({ detail: "Invalid credit range" }),
    }));
    await assert.rejects(client.generateSchedules({}), /Invalid credit range/);
    await assert.rejects(client.loadCoursesPage(0), /Failed to load courses \(status 422\)/);
    await assert.rejects(client.fetchBackendCourseDetail("CMSC433"), /Failed to load course details \(status 422\)/);
    globalThis.fetch = async () => ({ ok: false, status: 503, json: async () => { throw new Error("not JSON"); } });
    await assert.rejects(client.generateSchedules({}), /Failed to generate schedules \(status 503\)/);
    t.mock.timers.tick(3000);
    assert.deepEqual(changes, []);
});

test("cached course details and catalog reads do not start requests or timers", async (t) => {
    const { client, changes } = setup(t);
    const detail = { course_code: "CMSC433" };
    const fetch = t.mock.method(globalThis, "fetch", async () => response(detail));
    await client.fetchBackendCourseDetail("CMSC433");
    assert.deepEqual(await client.fetchBackendCourseDetail("CMSC433"), detail);
    client.writeCourseCatalogCache([detail]);
    assert.deepEqual(client.readCourseCatalogCache(), [detail]);
    assert.equal(fetch.mock.callCount(), 1);
    t.mock.timers.tick(3000);
    assert.deepEqual(changes, []);
});

test("slow PlanetTerp calls do not show the backend notice", async (t) => {
    const { client, changes } = setup(t);
    const pending = Promise.withResolvers();
    t.mock.method(globalThis, "fetch", () => pending.promise);
    const requests = [
        client.fetchProfessorRating("Professor"),
        client.fetchProfessorCourseGradeCounts("Professor", "CMSC433"),
        client.fetchCourseAverageGpa("CMSC433"),
    ];
    t.mock.timers.tick(3000);
    assert.deepEqual(changes, []);
    pending.resolve(response([]));
    await Promise.all(requests);
    assert.deepEqual(changes, []);
});

for (const alreadySlow of [false, true]) {
    test(`dispose clears timers and suppresses later callbacks (slow=${alreadySlow})`, async (t) => {
        const { client, changes } = setup(t);
        const pending = Promise.withResolvers();
        t.mock.method(globalThis, "fetch", () => pending.promise);
        const request = client.loadCoursesPage(0);
        if (alreadySlow) t.mock.timers.tick(3000);
        client.dispose();
        const before = [...changes];
        t.mock.timers.tick(3000);
        pending.resolve(response([]));
        await request;
        assert.deepEqual(changes, before);
        await client.loadCoursesPage(200);
        t.mock.timers.tick(3000);
        assert.deepEqual(changes, before);
    });
}
