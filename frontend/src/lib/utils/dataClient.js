import { runtimeConfig } from "../config/runtimeConfig.js";

const COURSE_PAGE_SIZE = 200;
const PLANETTERP_COURSE_URL = "https://planetterp.com/api/v1/course";
const PLANETTERP_PROFESSOR_URL = "https://planetterp.com/api/v1/professor";
const PLANETTERP_GRADES_URL = "https://planetterp.com/api/v1/grades";
const LOCAL_CACHE_PREFIX = "umdscheduler-cache-v1";
const CACHE_TTL_COURSE_CATALOG_MS = 6 * 60 * 60 * 1000;
const CACHE_TTL_COURSE_DETAIL_MS = 60 * 60 * 1000;
const CACHE_TTL_PLANETTERP_PROFESSOR_MS = 24 * 60 * 60 * 1000;
const CACHE_TTL_PLANETTERP_GRADES_MS = 24 * 60 * 60 * 1000;
const CACHE_TTL_PLANETTERP_COURSE_MS = 24 * 60 * 60 * 1000;

/**
 * @typedef {{ timestamp: number, value: any }} CacheEntry
 * @typedef {{ backendBaseUrl?: string }} DataClientOptions
 */

/**
 * @param {Map<string, CacheEntry>} memoryCache
 * @param {DataClientOptions} [options]
 */
export function createDataClient(memoryCache, options = {}) {
    const backendBaseUrl = String(
        options.backendBaseUrl ?? runtimeConfig.backendBaseUrl,
    ).replace(
        /\/+$/,
        "",
    );

    /** @param {...string} parts */
    function createCacheKey(...parts) {
        return `${LOCAL_CACHE_PREFIX}:${parts.join(":")}`;
    }

    /**
     * @param {string} cacheKey
     * @param {number} ttlMs
     * @returns {any}
     */
    function safeReadCache(cacheKey, ttlMs) {
        const now = Date.now();
        const memoryEntry = memoryCache.get(cacheKey);

        if (
            memoryEntry &&
            typeof memoryEntry.timestamp === "number" &&
            now - memoryEntry.timestamp <= ttlMs
        ) {
            return memoryEntry.value;
        }

        if (typeof localStorage === "undefined") return null;

        try {
            const serialized = localStorage.getItem(cacheKey);
            if (!serialized) return null;

            const parsed = JSON.parse(serialized);
            if (
                !parsed ||
                typeof parsed.timestamp !== "number" ||
                now - parsed.timestamp > ttlMs
            ) {
                localStorage.removeItem(cacheKey);
                return null;
            }

            memoryCache.set(cacheKey, parsed);
            return parsed.value;
        } catch {
            return null;
        }
    }

    /**
     * @param {string} cacheKey
     * @param {any} value
     */
    function safeWriteCache(cacheKey, value) {
        const payload = {
            timestamp: Date.now(),
            value,
        };

        memoryCache.set(cacheKey, payload);

        if (typeof localStorage === "undefined") return;

        try {
            localStorage.setItem(cacheKey, JSON.stringify(payload));
        } catch {
            // If storage is full or unavailable, in-memory cache still helps.
        }
    }

    /**
     * @template T
     * @param {string} cacheKey
     * @param {number} ttlMs
     * @param {() => Promise<T>} fetcher
     * @returns {Promise<T>}
     */
    async function fetchWithLocalCache(cacheKey, ttlMs, fetcher) {
        const cachedValue = safeReadCache(cacheKey, ttlMs);
        if (cachedValue !== null) return cachedValue;

        const freshValue = await fetcher();
        if (freshValue !== null && typeof freshValue !== "undefined") {
            safeWriteCache(cacheKey, freshValue);
        }

        return freshValue;
    }

    function readCourseCatalogCache() {
        const catalogCacheKey = createCacheKey("backend", "course-catalog");
        return safeReadCache(catalogCacheKey, CACHE_TTL_COURSE_CATALOG_MS);
    }

    /** @param {Array<any>} normalizedCatalog */
    function writeCourseCatalogCache(normalizedCatalog) {
        const catalogCacheKey = createCacheKey("backend", "course-catalog");
        safeWriteCache(catalogCacheKey, normalizedCatalog);
    }

    /** @param {number} offset @param {number} [pageSize] */
    async function loadCoursesPage(offset, pageSize = COURSE_PAGE_SIZE) {
        const response = await fetch(
            `${backendBaseUrl}/api/v1/courses?limit=${pageSize}&offset=${offset}`,
        );

        if (!response.ok) {
            throw new Error(`Failed to load courses (status ${response.status})`);
        }

        return response.json();
    }

    /** @param {string} professorName */
    async function fetchProfessorRating(professorName) {
        const professorCacheKey = createCacheKey(
            "planetterp",
            "professor",
            professorName,
        );

        return fetchWithLocalCache(
            professorCacheKey,
            CACHE_TTL_PLANETTERP_PROFESSOR_MS,
            async () => {
                try {
                    const response = await fetch(
                        `${PLANETTERP_PROFESSOR_URL}?name=${encodeURIComponent(professorName)}`,
                    );

                    if (!response.ok) return { rating: null, slug: null };
                    const payload = await response.json();
                    if (payload?.error) return { rating: null, slug: null };

                    return {
                        rating:
                            typeof payload.average_rating === "number"
                                ? payload.average_rating
                                : null,
                        slug: typeof payload.slug === "string" ? payload.slug : null,
                    };
                } catch {
                    return { rating: null, slug: null };
                }
            },
        );
    }

    /** @param {string} professorName @param {string} courseCode */
    async function fetchProfessorCourseGradeCounts(professorName, courseCode) {
        const gradesCacheKey = createCacheKey(
            "planetterp",
            "grades",
            professorName,
            courseCode,
        );

        return fetchWithLocalCache(
            gradesCacheKey,
            CACHE_TTL_PLANETTERP_GRADES_MS,
            async () => {
                try {
                    const response = await fetch(
                        `${PLANETTERP_GRADES_URL}?professor=${encodeURIComponent(professorName)}&course=${encodeURIComponent(courseCode)}`,
                    );

                    if (!response.ok) return null;

                    const gradesData = await response.json();
                    if (!Array.isArray(gradesData)) return null;

                    const possibleGrades = [
                        "A+",
                        "A",
                        "A-",
                        "B+",
                        "B",
                        "B-",
                        "C+",
                        "C",
                        "C-",
                        "D+",
                        "D",
                        "D-",
                        "F",
                        "W",
                        "Other",
                    ];

                    const gradeCounts = Object.fromEntries(
                        possibleGrades.map((grade) => [grade, 0]),
                    );

                    for (const semesterData of gradesData) {
                        if (semesterData?.course !== courseCode) continue;
                        if (semesterData?.professor !== professorName) continue;

                        for (const grade of possibleGrades) {
                            const count = Number(semesterData?.[grade] ?? 0);
                            if (Number.isFinite(count) && count > 0) {
                                gradeCounts[grade] += count;
                            }
                        }
                    }

                    return gradeCounts;
                } catch {
                    return null;
                }
            },
        );
    }

    /** @param {string} courseCode */
    async function fetchCourseAverageGpa(courseCode) {
        const courseGpaCacheKey = createCacheKey(
            "planetterp",
            "course",
            courseCode,
        );

        return fetchWithLocalCache(
            courseGpaCacheKey,
            CACHE_TTL_PLANETTERP_COURSE_MS,
            async () => {
                try {
                    const response = await fetch(
                        `${PLANETTERP_COURSE_URL}?name=${encodeURIComponent(courseCode)}&reviews=false`,
                    );

                    if (!response.ok) return null;
                    const payload = await response.json();
                    if (payload?.error) return null;

                    return typeof payload.average_gpa === "number"
                        ? payload.average_gpa
                        : null;
                } catch {
                    return null;
                }
            },
        );
    }

    /** @param {string} courseCode */
    async function fetchBackendCourseDetail(courseCode) {
        const backendCourseCacheKey = createCacheKey(
            "backend",
            "course-detail",
            courseCode,
        );

        return fetchWithLocalCache(
            backendCourseCacheKey,
            CACHE_TTL_COURSE_DETAIL_MS,
            async () => {
                const response = await fetch(
                    `${backendBaseUrl}/api/v1/courses/${encodeURIComponent(courseCode)}`,
                );

                if (!response.ok) {
                    throw new Error(
                        `Failed to load course details (status ${response.status})`,
                    );
                }

                return response.json();
            },
        );
    }

    return {
        coursePageSize: COURSE_PAGE_SIZE,
        backendBaseUrl,
        readCourseCatalogCache,
        writeCourseCatalogCache,
        loadCoursesPage,
        fetchProfessorRating,
        fetchProfessorCourseGradeCounts,
        fetchCourseAverageGpa,
        fetchBackendCourseDetail,
    };
}
