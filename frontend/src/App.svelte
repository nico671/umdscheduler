<script>
  import { onMount } from "svelte";
  import { SvelteMap } from "svelte/reactivity";
  import TopbarControls from "./lib/components/TopbarControls.svelte";
  import CourseListSection from "./lib/components/CourseListSection.svelte";
  import ScheduleCalendar from "./lib/components/ScheduleCalendar.svelte";
  import RestrictionModal from "./lib/components/RestrictionModal.svelte";
  import CourseDetailModal from "./lib/components/CourseDetailModal.svelte";
  import ScheduleEntryModal from "./lib/components/ScheduleEntryModal.svelte";
  import { createDataClient } from "./lib/utils/dataClient.js";
  import {
    buildScheduleSignature,
    getMeetingLocation,
    mapScheduleToCalendar,
  } from "./lib/utils/scheduleUtils.js";

  const weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
  const startHours = Array.from({ length: 12 }, (_, i) => i + 8);
  const maxCreditsOptions = Array.from({ length: 28 }, (_, i) => i + 3);

  let courseCatalog = $state([]);
  let query = $state("");
  let selectedCourses = $state([]);
  let optionalCourses = $state([]);
  let prohibitedProfessors = $state([]);
  let selectedRestrictedDays = $state([weekdays[0]]);
  let selectedRestrictedStartHours = $state([startHours[0]]);
  let restrictedTimes = $state([]);
  let isLoadingCourses = $state(false);
  let coursesLoadError = $state("");
  let isRestrictionModalOpen = $state(false);
  let isCourseModalOpen = $state(false);
  let activeCourseSummary = $state(null);
  let activeCourseDetail = $state(null);
  let isLoadingCourseDetail = $state(false);
  let isLoadingProfessorRatings = $state(false);
  let isSectionsExpanded = $state(false);
  let courseDetailError = $state("");
  let activeCourseAverageGpa = $state(null);
  let isLoadingActiveCourseAverageGpa = $state(false);
  let professorRatingsByName = $state({});
  let generatedSchedules = $state([]);
  let isLoadingSchedules = $state(false);
  let schedulesLoadError = $state("");
  let hasGeneratedSchedules = $state(false);
  let minCreditsInput = $state("none");
  let maxCreditsInput = $state("18");
  let onlyOpenSeatsSections = $state(true);
  let isScheduleEntryModalOpen = $state(false);
  let activeScheduleEntry = $state(null);
  let activeScheduleEntryCourseDetail = $state(null);
  let activeScheduleEntrySection = $state(null);
  let isLoadingScheduleEntryDetail = $state(false);
  let scheduleEntryDetailError = $state("");
  let activeScheduleEntrySectionGpa = $state(null);
  let isLoadingActiveScheduleEntrySectionGpa = $state(false);
  let scheduleEntryProfessorRatingsByName = $state({});
  let isLoadingScheduleEntryRatings = $state(false);
  const memoryCache = new SvelteMap();
  const dataClient = createDataClient(memoryCache);

  const normalizedQuery = $derived(query.trim().toLowerCase());
  const sortedCatalog = $derived(
    [...courseCatalog].sort((a, b) =>
      `${a.id} ${a.title}`.localeCompare(`${b.id} ${b.title}`),
    ),
  );
  const filteredCourses = $derived(
    normalizedQuery
      ? sortedCatalog.filter((course) => {
          const haystack =
            `${course.id} ${course.title} ${course.level} ${course.genedCodes.join(" ")}`.toLowerCase();
          return haystack.includes(normalizedQuery);
        })
      : sortedCatalog,
  );
  const selectedIds = $derived(
    new Set(selectedCourses.map((course) => course.id)),
  );
  const optionalIds = $derived(
    new Set(optionalCourses.map((course) => course.id)),
  );
  const blockedSearchIds = $derived(new Set([...selectedIds, ...optionalIds]));
  const searchDropdownCourses = $derived(
    filteredCourses
      .filter((course) => !blockedSearchIds.has(course.id))
      .slice(0, 50),
  );
  const activeCourseProfessors = $derived(
    activeCourseDetail
      ? Array.from(
          new Set(
            activeCourseDetail.sections
              .flatMap((section) => section.instructors ?? [])
              .filter((professor) => professor && professor.trim().length > 0),
          ),
        ).sort((a, b) => a.localeCompare(b))
      : [],
  );
  const sortedActiveCourseSections = $derived(
    activeCourseDetail?.sections
      ? [...activeCourseDetail.sections].sort((left, right) => {
          const leftOpenSeats = Number(left.open_seats ?? 0);
          const rightOpenSeats = Number(right.open_seats ?? 0);
          const leftIsFull = leftOpenSeats <= 0 ? 1 : 0;
          const rightIsFull = rightOpenSeats <= 0 ? 1 : 0;

          if (leftIsFull !== rightIsFull) {
            return leftIsFull - rightIsFull;
          }

          return String(left.section_code).localeCompare(
            String(right.section_code),
          );
        })
      : [],
  );
  const isActiveCourseRequired = $derived(
    activeCourseSummary ? selectedIds.has(activeCourseSummary.id) : false,
  );
  const isActiveCourseOptional = $derived(
    activeCourseSummary ? optionalIds.has(activeCourseSummary.id) : false,
  );
  const activeCourseGenedCodes = $derived.by(() => {
    if (activeCourseDetail?.gened_codes?.length) {
      return activeCourseDetail.gened_codes;
    }

    if (activeCourseSummary?.genedCodes?.length) {
      return activeCourseSummary.genedCodes;
    }

    return [];
  });
  const totalCredits = $derived(
    selectedCourses.reduce((sum, course) => sum + course.credits, 0),
  );
  const selectedRestrictionCount = $derived(
    selectedRestrictedDays.length * selectedRestrictedStartHours.length,
  );
  const totalAddedClassCount = $derived(
    selectedCourses.length + optionalCourses.length,
  );
  const selectedRestrictionLabel = $derived.by(() => {
    if (
      selectedRestrictedDays.length === 0 ||
      selectedRestrictedStartHours.length === 0
    ) {
      return "Choose at least one day and one time slot.";
    }

    const dayLabel =
      selectedRestrictedDays.length === 1
        ? selectedRestrictedDays[0]
        : `${selectedRestrictedDays.length} days`;

    const slotLabel =
      selectedRestrictedStartHours.length === 1
        ? `${formatHour(selectedRestrictedStartHours[0])} - ${formatHour(selectedRestrictedStartHours[0] + 1)}`
        : `${selectedRestrictedStartHours.length} time slots`;

    return `${dayLabel} × ${slotLabel} (${selectedRestrictionCount} combinations)`;
  });
  const canGenerateSchedules = $derived(
    totalAddedClassCount >= 2 && !isLoadingSchedules,
  );
  const activeScheduleEntrySummary = $derived.by(() => {
    if (!activeScheduleEntry) return null;

    const catalogMatch = courseCatalog.find(
      (course) => course.id === activeScheduleEntry.courseCode,
    );

    return {
      id: activeScheduleEntry.courseCode,
      title:
        activeScheduleEntryCourseDetail?.title ??
        catalogMatch?.title ??
        "Course details",
    };
  });
  const activeScheduleEntryProfessors = $derived(
    activeScheduleEntrySection?.instructors
      ? Array.from(
          new Set(
            activeScheduleEntrySection.instructors.filter(
              (name) => name && name.trim().length > 0,
            ),
          ),
        ).sort((a, b) => a.localeCompare(b))
      : [],
  );

  function formatHour(hour24) {
    const period = hour24 >= 12 ? "PM" : "AM";
    const hour12 = hour24 % 12 === 0 ? 12 : hour24 % 12;
    return `${hour12}:00 ${period}`;
  }

  function formatCompactHour(hour24) {
    const period = hour24 >= 12 ? "PM" : "AM";
    const hour12 = hour24 % 12 === 0 ? 12 : hour24 % 12;
    return `${hour12}${period}`;
  }

  function formatInterval(day, startHour) {
    const abbreviatedDay = day.slice(0, 3);
    return `${abbreviatedDay} ${formatCompactHour(startHour)}-${formatCompactHour(startHour + 1)}`;
  }

  function parseMaxCreditsInput(value) {
    const normalized = String(value ?? "").trim();
    if (normalized.length === 0) return 18;

    const parsed = Number(normalized);
    if (!Number.isInteger(parsed) || parsed < 3 || parsed > 30) {
      return 18;
    }

    return parsed;
  }

  function parseMinCreditsInput(value) {
    const normalized = String(value ?? "")
      .trim()
      .toLowerCase();
    if (normalized.length === 0 || normalized === "none") return null;

    const parsed = Number(normalized);
    if (!Number.isInteger(parsed) || parsed < 3 || parsed > 30) {
      return null;
    }

    return parsed;
  }

  function formatFloat2(value) {
    return typeof value === "number" ? value.toFixed(2) : null;
  }

  function formatScheduleAverageRating(value) {
    const formatted = formatFloat2(value);
    return formatted !== null ? `${formatted} / 5` : "No rating";
  }

  function hourToTimeString(hour24) {
    return `${String(hour24).padStart(2, "0")}:00`;
  }

  function mapRestrictionsForPayload() {
    return restrictedTimes.map((slot) => ({
      day: slot.day,
      start_time: hourToTimeString(slot.startHour),
      end_time: hourToTimeString(slot.startHour + 1),
    }));
  }

  function sortSchedulesByRating(schedules) {
    return [...schedules].sort((left, right) => {
      const leftRating =
        typeof left.average_professor_rating === "number"
          ? left.average_professor_rating
          : -1;
      const rightRating =
        typeof right.average_professor_rating === "number"
          ? right.average_professor_rating
          : -1;

      if (leftRating !== rightRating) return rightRating - leftRating;
      return (right.total_credits ?? 0) - (left.total_credits ?? 0);
    });
  }

  async function generateSchedules() {
    if (totalAddedClassCount < 2) return;

    isLoadingSchedules = true;
    schedulesLoadError = "";
    hasGeneratedSchedules = true;
    generatedSchedules = [];

    try {
      const parsedMinCredits = parseMinCreditsInput(minCreditsInput);
      const parsedMaxCredits = parseMaxCreditsInput(maxCreditsInput);
      const payload = {
        required_courses: selectedCourses.map((course) => course.id),
        optional_courses: optionalCourses.map((course) => course.id),
        excluded_profs: prohibitedProfessors,
        time_constraints: mapRestrictionsForPayload(),
        max_schedules: 100,
        min_credits: parsedMinCredits,
        max_credits: parsedMaxCredits,
        only_open_seats: onlyOpenSeatsSections,
      };

      const response = await fetch("http://localhost:8000/api/v1/schedules", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorPayload = await response.json().catch(() => null);
        const detail =
          typeof errorPayload?.detail === "string" ? errorPayload.detail : null;
        throw new Error(
          detail || `Failed to generate schedules (status ${response.status})`,
        );
      }

      const scheduleResults = await response.json();
      generatedSchedules = sortSchedulesByRating(scheduleResults).map(
        (schedule) => ({
          ...schedule,
          scheduleKey: buildScheduleSignature(schedule),
          calendar: mapScheduleToCalendar(schedule, { weekdays }),
        }),
      );
    } catch (error) {
      schedulesLoadError =
        error instanceof Error
          ? error.message
          : "Unexpected error while generating schedules.";
      generatedSchedules = [];
    } finally {
      isLoadingSchedules = false;
    }
  }

  function normalizeCourse(course) {
    const parsedCredits = Number.parseInt(course.credits ?? "0", 10);
    const normalizedGenedCodes = Array.isArray(course.gened_codes)
      ? course.gened_codes
      : [];

    return {
      id: course.course_code,
      title: course.title ?? "Untitled Course",
      credits: Number.isNaN(parsedCredits) ? 0 : parsedCredits,
      level: course.department_code ?? "General",
      genedCodes: normalizedGenedCodes,
    };
  }

  async function loadAllCourses() {
    isLoadingCourses = true;
    coursesLoadError = "";

    try {
      const cachedCatalog = dataClient.readCourseCatalogCache();

      if (Array.isArray(cachedCatalog) && cachedCatalog.length > 0) {
        courseCatalog = cachedCatalog;
        return;
      }

      let offset = 0;
      let keepFetching = true;
      let allCourses = [];

      while (keepFetching) {
        const page = await dataClient.loadCoursesPage(offset);
        allCourses = [...allCourses, ...page];

        if (page.length < dataClient.coursePageSize) {
          keepFetching = false;
        } else {
          offset += dataClient.coursePageSize;
        }
      }
      const normalizedCatalog = allCourses.map(normalizeCourse);
      courseCatalog = normalizedCatalog;
      dataClient.writeCourseCatalogCache(normalizedCatalog);
    } catch (error) {
      coursesLoadError =
        error instanceof Error
          ? error.message
          : "Unexpected error while loading courses.";
    } finally {
      isLoadingCourses = false;
    }
  }

  function addCourse(course) {
    optionalCourses = optionalCourses.filter((item) => item.id !== course.id);
    if (selectedIds.has(course.id)) return;
    selectedCourses = [...selectedCourses, course];
  }

  function addCourseFromSearch(course) {
    void openCourseModal(course);
  }

  function addCourseAsOptional(course) {
    if (selectedIds.has(course.id) || optionalIds.has(course.id)) return;
    optionalCourses = [...optionalCourses, course];
  }

  function removeCourse(courseId) {
    selectedCourses = selectedCourses.filter(
      (course) => course.id !== courseId,
    );
  }

  function removeOptionalCourse(courseId) {
    optionalCourses = optionalCourses.filter(
      (course) => course.id !== courseId,
    );
  }

  function prohibitProfessor(professorName) {
    if (prohibitedProfessors.includes(professorName)) return;
    prohibitedProfessors = [...prohibitedProfessors, professorName];
  }

  function allowProfessor(professorName) {
    prohibitedProfessors = prohibitedProfessors.filter(
      (name) => name !== professorName,
    );
  }

  async function fetchProfessorRating(professorName) {
    return dataClient.fetchProfessorRating(professorName);
  }

  async function loadProfessorRatings(professorNames) {
    if (professorNames.length === 0) {
      professorRatingsByName = {};
      return;
    }

    isLoadingProfessorRatings = true;
    try {
      const ratings = await Promise.all(
        professorNames.map(async (name) => [
          name,
          await fetchProfessorRating(name),
        ]),
      );
      professorRatingsByName = Object.fromEntries(ratings);
    } finally {
      isLoadingProfessorRatings = false;
    }
  }

  function formatProfessorRating(value) {
    const formatted = formatFloat2(value);
    return formatted !== null ? `${formatted} / 5` : "No rating yet";
  }

  function formatAverageGpa(value) {
    const formatted = formatFloat2(value);
    return formatted !== null ? formatted : "Unavailable";
  }

  async function fetchProfessorCourseGradeCounts(professorName, courseCode) {
    return dataClient.fetchProfessorCourseGradeCounts(
      professorName,
      courseCode,
    );
  }

  async function calculateWeightedSectionGpa(courseCode, professors) {
    if (!Array.isArray(professors) || professors.length === 0) {
      return null;
    }

    const gradeToPoints = {
      "A+": 4,
      A: 4,
      "A-": 3.7,
      "B+": 3.3,
      B: 3,
      "B-": 2.7,
      "C+": 2.3,
      C: 2,
      "C-": 1.7,
      "D+": 1.3,
      D: 1,
      "D-": 0.7,
      F: 0,
    };

    let totalWeightedSum = 0;
    let totalGradeCount = 0;

    for (const professor of professors) {
      if (!professor || !professor.trim()) continue;

      const gradeCounts = await fetchProfessorCourseGradeCounts(
        professor,
        courseCode,
      );
      if (!gradeCounts) continue;

      let professorWeightedSum = 0;
      let professorGradeCount = 0;

      for (const [grade, points] of Object.entries(gradeToPoints)) {
        const count = Number(gradeCounts?.[grade] ?? 0);
        if (!Number.isFinite(count) || count <= 0) continue;
        professorWeightedSum += count * points;
        professorGradeCount += count;
      }

      if (professorGradeCount > 0) {
        totalWeightedSum += professorWeightedSum;
        totalGradeCount += professorGradeCount;
      }
    }

    if (totalGradeCount === 0) return null;
    return totalWeightedSum / totalGradeCount;
  }

  async function fetchCourseAverageGpa(courseCode) {
    return dataClient.fetchCourseAverageGpa(courseCode);
  }

  async function fetchBackendCourseDetail(courseCode) {
    return dataClient.fetchBackendCourseDetail(courseCode);
  }

  async function loadActiveCourseAverageGpa(courseCode) {
    activeCourseAverageGpa = null;
    isLoadingActiveCourseAverageGpa = true;

    try {
      activeCourseAverageGpa = await fetchCourseAverageGpa(courseCode);
    } finally {
      isLoadingActiveCourseAverageGpa = false;
    }
  }

  async function loadActiveScheduleEntrySectionGpa(entry) {
    activeScheduleEntrySectionGpa = null;

    if (typeof entry?.avgProfGpaInClass === "number") {
      activeScheduleEntrySectionGpa = entry.avgProfGpaInClass;
      isLoadingActiveScheduleEntrySectionGpa = false;
      return;
    }

    isLoadingActiveScheduleEntrySectionGpa = true;

    try {
      activeScheduleEntrySectionGpa = await calculateWeightedSectionGpa(
        entry?.courseCode,
        entry?.instructors ?? [],
      );
    } finally {
      isLoadingActiveScheduleEntrySectionGpa = false;
    }
  }

  function getProfessorReviewUrl(professorName) {
    const slug = professorRatingsByName[professorName]?.slug;
    return slug ? `https://planetterp.com/professor/${slug}` : null;
  }

  function getScheduleEntryProfessorReviewUrl(professorName) {
    const slug = scheduleEntryProfessorRatingsByName[professorName]?.slug;
    return slug ? `https://planetterp.com/professor/${slug}` : null;
  }

  async function loadScheduleEntryProfessorRatings(professorNames) {
    if (professorNames.length === 0) {
      scheduleEntryProfessorRatingsByName = {};
      return;
    }

    isLoadingScheduleEntryRatings = true;
    try {
      const ratings = await Promise.all(
        professorNames.map(async (name) => [
          name,
          await fetchProfessorRating(name),
        ]),
      );
      scheduleEntryProfessorRatingsByName = Object.fromEntries(ratings);
    } finally {
      isLoadingScheduleEntryRatings = false;
    }
  }

  async function openScheduleEntryModal(entry) {
    activeScheduleEntry = entry;
    activeScheduleEntryCourseDetail = null;
    activeScheduleEntrySection = null;
    scheduleEntryDetailError = "";
    activeScheduleEntrySectionGpa = null;
    scheduleEntryProfessorRatingsByName = {};
    isLoadingScheduleEntryDetail = true;
    isLoadingActiveScheduleEntrySectionGpa = false;
    isLoadingScheduleEntryRatings = false;
    isScheduleEntryModalOpen = true;

    void loadActiveScheduleEntrySectionGpa(entry);

    try {
      const detail = await fetchBackendCourseDetail(entry.courseCode);
      activeScheduleEntryCourseDetail = detail;

      const section = detail.sections?.find(
        (item) => String(item.section_code) === String(entry.sectionCode),
      );

      if (!section) {
        scheduleEntryDetailError =
          "Section details are currently unavailable for this class.";
        return;
      }

      activeScheduleEntrySection = section;
      void loadScheduleEntryProfessorRatings(section.instructors ?? []);
    } catch (error) {
      scheduleEntryDetailError =
        error instanceof Error
          ? error.message
          : "Could not load section details at this time.";
    } finally {
      isLoadingScheduleEntryDetail = false;
    }
  }

  function closeScheduleEntryModal() {
    isScheduleEntryModalOpen = false;
    activeScheduleEntry = null;
    activeScheduleEntryCourseDetail = null;
    activeScheduleEntrySection = null;
    scheduleEntryDetailError = "";
    activeScheduleEntrySectionGpa = null;
    scheduleEntryProfessorRatingsByName = {};
  }

  async function openCourseModal(course) {
    activeCourseSummary = course;
    activeCourseDetail = null;
    courseDetailError = "";
    activeCourseAverageGpa = null;
    isCourseModalOpen = true;
    isLoadingCourseDetail = true;
    isLoadingActiveCourseAverageGpa = false;
    isLoadingProfessorRatings = false;
    isSectionsExpanded = false;
    professorRatingsByName = {};

    void loadActiveCourseAverageGpa(course.id);

    try {
      const detail = await fetchBackendCourseDetail(course.id);
      activeCourseDetail = detail;

      const professors = Array.from(
        new Set(
          detail.sections
            .flatMap((section) => section.instructors ?? [])
            .filter((name) => name && name.trim().length > 0),
        ),
      );
      void loadProfessorRatings(professors);
    } catch (error) {
      courseDetailError =
        error instanceof Error
          ? error.message
          : "Could not load class details at this time.";
    } finally {
      isLoadingCourseDetail = false;
    }
  }

  function closeCourseModal() {
    isCourseModalOpen = false;
    activeCourseSummary = null;
    activeCourseDetail = null;
    courseDetailError = "";
    activeCourseAverageGpa = null;
    isSectionsExpanded = false;
    professorRatingsByName = {};
  }

  function toggleSectionsExpanded() {
    isSectionsExpanded = !isSectionsExpanded;
  }

  function addActiveCourseAsRequired() {
    if (!activeCourseSummary) return;
    addCourse(activeCourseSummary);
    query = "";
    closeCourseModal();
  }

  function addActiveCourseAsOptional() {
    if (!activeCourseSummary) return;
    addCourseAsOptional(activeCourseSummary);
    query = "";
    closeCourseModal();
  }

  function toggleRestrictedDay(day) {
    if (selectedRestrictedDays.includes(day)) {
      selectedRestrictedDays = selectedRestrictedDays.filter(
        (item) => item !== day,
      );
      return;
    }

    selectedRestrictedDays = weekdays.filter((item) =>
      [...selectedRestrictedDays, day].includes(item),
    );
  }

  function toggleRestrictedStartHour(hour) {
    if (selectedRestrictedStartHours.includes(hour)) {
      selectedRestrictedStartHours = selectedRestrictedStartHours.filter(
        (item) => item !== hour,
      );
      return;
    }

    selectedRestrictedStartHours = [...selectedRestrictedStartHours, hour].sort(
      (left, right) => left - right,
    );
  }

  function activateRestriction() {
    if (
      selectedRestrictedDays.length === 0 ||
      selectedRestrictedStartHours.length === 0
    ) {
      return;
    }

    const existingKeys = restrictedTimes.map((slot) => slot.key);
    const nextRestrictions = [...restrictedTimes];

    for (const day of selectedRestrictedDays) {
      for (const startHour of selectedRestrictedStartHours) {
        const key = `${day}-${startHour}`;
        if (existingKeys.includes(key)) continue;

        nextRestrictions.push({
          key,
          day,
          startHour,
          label: formatInterval(day, startHour),
        });
        existingKeys.push(key);
      }
    }

    restrictedTimes = nextRestrictions;
  }

  function removeRestriction(key) {
    restrictedTimes = restrictedTimes.filter((slot) => slot.key !== key);
  }

  function openRestrictionModal() {
    isRestrictionModalOpen = true;
  }

  function closeRestrictionModal() {
    isRestrictionModalOpen = false;
  }

  onMount(() => {
    void loadAllCourses();
  });
</script>

<main class="page">
  <TopbarControls
    bind:query
    {normalizedQuery}
    {isLoadingCourses}
    {coursesLoadError}
    {searchDropdownCourses}
    {canGenerateSchedules}
    {isLoadingSchedules}
    onOpenRestrictionModal={openRestrictionModal}
    onGenerateSchedules={generateSchedules}
    onSelectCourse={addCourseFromSearch}
  />

  <section class="dashboard-grid" aria-label="Scheduler dashboard cards">
    <article class="dashboard-card class-list-card">
      <div class="plan-header">
        <h2>Your Class List</h2>
        <p class="credits-chip" aria-live="polite">{totalCredits} credits</p>
      </div>

      <CourseListSection
        title="Required Classes"
        courses={selectedCourses}
        listAriaLabel="Selected classes"
        emptyMessage="Add classes from the search panel to start planning your schedule."
        onOpenCourse={openCourseModal}
        onRemoveCourse={removeCourse}
      />

      <CourseListSection
        title="Optional Classes"
        courses={optionalCourses}
        listAriaLabel="Optional classes"
        emptyMessage="Add optional classes from the class details modal."
        emptyStyle="placeholder"
        onOpenCourse={openCourseModal}
        onRemoveCourse={removeOptionalCourse}
      />
    </article>

    <article class="dashboard-card scheduler-card">
      <h2>Schedule Constraints</h2>

      <section class="constraint-group">
        <h3>Credit Range</h3>
        <div class="credits-range-grid">
          <div class="max-credits-control">
            <label class="field-label" for="min-credits-select"
              >Minimum credits</label
            >
            <select
              id="min-credits-select"
              class="max-credits-select"
              bind:value={minCreditsInput}
            >
              <option value="none">No minimum</option>
              {#each maxCreditsOptions as creditsOption (creditsOption)}
                <option value={String(creditsOption)}>{creditsOption}</option>
              {/each}
            </select>
          </div>

          <div class="max-credits-control">
            <label class="field-label" for="max-credits-select"
              >Maximum credits</label
            >
            <select
              id="max-credits-select"
              class="max-credits-select"
              bind:value={maxCreditsInput}
            >
              {#each maxCreditsOptions as creditsOption (creditsOption)}
                <option value={String(creditsOption)}>{creditsOption}</option>
              {/each}
            </select>
          </div>
        </div>
      </section>

      <section class="constraint-group">
        <h3>Section Availability</h3>
        <label class="seat-filter-control" for="only-open-seats-toggle">
          <input
            id="only-open-seats-toggle"
            type="checkbox"
            bind:checked={onlyOpenSeatsSections}
          />
          <span>Only include sections with open seats</span>
        </label>
      </section>

      <section class="constraint-group">
        <div class="constraint-group-header">
          <h3>Time Restrictions</h3>
          <p class="restriction-count" aria-live="polite">
            {restrictedTimes.length} active time restriction{restrictedTimes.length ===
            1
              ? ""
              : "s"}
          </p>
        </div>
        {#if restrictedTimes.length === 0}
          <div class="placeholder-block preference-placeholder">
            Create restricted time intervals from the top bar button.
          </div>
        {:else}
          <ul
            class="restriction-list"
            aria-label="Activated restricted intervals"
          >
            {#each restrictedTimes as slot (slot.key)}
              <li class="restriction-chip">
                <span>{slot.label}</span>
                <button
                  class="chip-remove"
                  type="button"
                  onclick={() => removeRestriction(slot.key)}
                  aria-label={`Remove ${slot.label}`}
                >
                  ×
                </button>
              </li>
            {/each}
          </ul>
        {/if}
      </section>

      <section class="constraint-group">
        <div class="constraint-group-header">
          <h3>Prohibited Professors</h3>
          <p class="restriction-count" aria-live="polite">
            {restrictedTimes.length} prohibited professor{restrictedTimes.length ===
            1
              ? ""
              : "s"}
          </p>
        </div>
        {#if prohibitedProfessors.length === 0}
          <div class="placeholder-block preference-placeholder">
            Add prohibited professors from the class details modal.
          </div>
        {:else}
          <ul class="preference-chip-list" aria-label="Prohibited professors">
            {#each prohibitedProfessors as professor (professor)}
              <li class="preference-chip">
                <span>{professor}</span>
                <button
                  class="chip-remove"
                  type="button"
                  aria-label={`Allow professor ${professor}`}
                  onclick={() => allowProfessor(professor)}
                >
                  ×
                </button>
              </li>
            {/each}
          </ul>
        {/if}
      </section>
    </article>
  </section>

  {#if hasGeneratedSchedules}
    <section class="schedule-results-card" aria-label="Generated schedules">
      <div class="schedule-results-header">
        <h2>Generated Schedules</h2>
        <p class="restriction-count" aria-live="polite">
          {generatedSchedules.length} schedule{generatedSchedules.length === 1
            ? ""
            : "s"}
        </p>
      </div>

      {#if schedulesLoadError}
        <div class="modal-state">{schedulesLoadError}</div>
      {:else if isLoadingSchedules}
        <div class="modal-state">Building conflict-free schedules…</div>
      {:else if generatedSchedules.length === 0}
        <div class="placeholder-block schedule-placeholder">
          No valid schedules found for the current requirements and constraints.
        </div>
      {:else}
        <ol class="schedule-results-list">
          {#each generatedSchedules as schedule, index (schedule.scheduleKey)}
            <li class="schedule-result-item">
              <header class="schedule-result-header">
                <div>
                  <p class="course-id">Schedule #{index + 1}</p>
                  <h3>{schedule.total_credits} total credits</h3>
                </div>
                <p class="schedule-rating-chip">
                  Avg rating: {formatScheduleAverageRating(
                    schedule.average_professor_rating,
                  )}
                </p>
              </header>

              {#if schedule.included_optional_courses?.length}
                <p class="modal-item-copy">
                  Includes optional courses:
                  {schedule.included_optional_courses.join(", ")}
                </p>
              {/if}

              <ScheduleCalendar
                {schedule}
                {weekdays}
                {formatHour}
                onEntrySelect={openScheduleEntryModal}
              />
            </li>
          {/each}
        </ol>
      {/if}
    </section>
  {/if}

  <RestrictionModal
    isOpen={isRestrictionModalOpen}
    onClose={closeRestrictionModal}
    {weekdays}
    {startHours}
    {selectedRestrictedDays}
    {selectedRestrictedStartHours}
    {selectedRestrictionLabel}
    {selectedRestrictionCount}
    {formatHour}
    onToggleRestrictedDay={toggleRestrictedDay}
    onToggleRestrictedStartHour={toggleRestrictedStartHour}
    onActivateRestriction={activateRestriction}
  />

  <CourseDetailModal
    isOpen={isCourseModalOpen}
    onClose={closeCourseModal}
    {activeCourseSummary}
    {isLoadingCourseDetail}
    {courseDetailError}
    {activeCourseDetail}
    {activeCourseAverageGpa}
    {isLoadingActiveCourseAverageGpa}
    {activeCourseGenedCodes}
    {activeCourseProfessors}
    {professorRatingsByName}
    {isLoadingProfessorRatings}
    {prohibitedProfessors}
    {isSectionsExpanded}
    {sortedActiveCourseSections}
    {isActiveCourseOptional}
    {isActiveCourseRequired}
    {formatAverageGpa}
    {formatProfessorRating}
    {getProfessorReviewUrl}
    onAddOptional={addActiveCourseAsOptional}
    onAddRequired={addActiveCourseAsRequired}
    onAllowProfessor={allowProfessor}
    onProhibitProfessor={prohibitProfessor}
    onToggleSectionsExpanded={toggleSectionsExpanded}
  />

  <ScheduleEntryModal
    isOpen={isScheduleEntryModalOpen}
    onClose={closeScheduleEntryModal}
    {activeScheduleEntrySummary}
    {isLoadingScheduleEntryDetail}
    {scheduleEntryDetailError}
    {activeScheduleEntry}
    {activeScheduleEntrySection}
    {activeScheduleEntryCourseDetail}
    {activeScheduleEntrySectionGpa}
    {isLoadingActiveScheduleEntrySectionGpa}
    {activeScheduleEntryProfessors}
    {isLoadingScheduleEntryRatings}
    {scheduleEntryProfessorRatingsByName}
    {formatAverageGpa}
    {formatProfessorRating}
    {getScheduleEntryProfessorReviewUrl}
    {getMeetingLocation}
  />
</main>
