import { get, writable, type Writable } from "svelte/store";

// Type definitions
export interface Schedule {
  prof_weight: number;
  [key: string]: any; // Allow for other properties
}

export interface ReturnToModal {
  type: string;
  className?: string;
  index: number;
  timestamp?: number;
}

export interface ProfessorViewInfo {
  name: string;
  showModal: boolean;
  returnTo: ReturnToModal | null;
}

// Create stores for state management
export const availableClasses: Writable<string[]> = writable([]);
export const addedClasses: Writable<string[]> = writable([]);
export const prohibitedTimes: Writable<Map<string, string>[]> = writable([]);
export const prohibitedProfessors: Writable<string[]> = writable([]);
export const generatedSchedules: Writable<any[]> = writable([]);
export const colorMap: Writable<Map<string, string>> = writable(new Map());
export const showTimeSelectionModal: Writable<boolean> = writable(false);
export const showAddClassModal: Writable<boolean> = writable(false);
export const generatingSchedules: Writable<boolean> = writable(false);
export const currentAmountLoaded: Writable<number> = writable(0);
export const showClassModals: Writable<boolean[]> = writable([]);
export const showProfessorModals: Writable<boolean[]> = writable([]);
export const schedules: Writable<any[]> = writable([]);
export const sortOption: Writable<string> = writable("rating");
export const error: Writable<string | null> = writable(null);
export const viewProfessorInfo: Writable<ProfessorViewInfo[]> = writable([]);
export const classProfessors: Writable<Record<string, string[]>> = writable({});

// Add semester to store and initialize with current semester
export const currentSemester: Writable<string> = writable("");
export const availableSemesters: Writable<string[]> = writable([]);

// Theme colors
export const umdRed = "#e21833";
export const umdGold = "#FFD200";

// Color generator for classes
export function generateColor(index: number): string {
  const hues = [210, 180, 120, 330, 270, 30, 150, 300, 60, 240];
  const hue = hues[index % hues.length];
  return `hsl(${hue}, 70%, 85%)`;
}


// Generate schedules function - updated to always get latest semester
export async function generateSchedules(): Promise<void> {
  // Get current values directly using get() for simplicity
  const currentAddedClasses = get(addedClasses);
  const currentProhibitedTimes = get(prohibitedTimes);
  const currentProhibitedProfessors = get(prohibitedProfessors);
  const selectedSemester = get(currentSemester);

  // Validate minimum requirements
  if (currentAddedClasses.length < 2) {
    error.set("Please add at least two classes before generating schedules");
    return;
  }

  // Reset state
  generatedSchedules.set([]);
  schedules.set([]);
  error.set(null);
  generatingSchedules.set(true);

  try {
    // Format prohibited times consistently
    const formattedProhibitedTimes = currentProhibitedTimes.map(timeMap =>
      timeMap instanceof Map ? Object.fromEntries(timeMap) : timeMap
    );

    // Create request object
    const requestBody = {
      wanted_classes: currentAddedClasses,
      restrictions: {
        semester: selectedSemester || "202401",
        minSeats: 1,
        prohibitedInstructors: currentProhibitedProfessors,
        prohibitedTimes: formattedProhibitedTimes,
        required_classes: currentAddedClasses
      }
    };

    console.log(`Generating schedules for semester: ${selectedSemester} (${formatSemester(selectedSemester)})`);

    const response = await fetch("/api/schedule", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestBody),
      signal: AbortSignal.timeout(60000)
    });

    if (!response.ok) {
      const errorText = await response.text();
      let errorMsg = `Server returned ${response.status}`;
      try {
        const errorData = JSON.parse(errorText);
        if (errorData?.error) errorMsg = errorData.error;
      } catch {/* Use default error message if JSON parsing fails */ }

      throw new Error(errorMsg);
    }

    const data = await response.json();

    // Set data directly to both stores at once
    if (!data?.length) {
      error.set("No possible schedules found with your constraints");
    } else {
      generatedSchedules.set(data);
      schedules.set(data);
      currentAmountLoaded.set(data.length);
      console.log(`Loaded ${data.length} schedules`);
    }
  } catch (err) {
    console.error("Schedule generation failed:", err);

    // Simplified error handling
    if (err instanceof Error) {
      if (err.name === "AbortError") {
        error.set("Request timed out. The server might be overloaded.");
      } else {
        error.set(err.message);
      }
    } else {
      error.set("Failed to generate schedules. Please try again later.");
    }
  } finally {
    generatingSchedules.set(false);
  }
}

// Process schedule data - modified to load all schedules at once
export function processScheduleData(data: any): void {
  console.log(`Received ${data?.length || 0} schedules`);

  if (!Array.isArray(data) || data.length === 0) {
    error.set("No possible schedules found with your constraints");
  } else {
    // Load all schedules immediately instead of batching
    generatedSchedules.set(data);
    currentAmountLoaded.set(data.length);
    schedules.set(data);
    console.log(`Loaded all ${data.length} schedules at once`);
  }
}

// More utility functions for the page component
export function removeProhibitedTime(index: number): void {
  let currentTimes: Map<string, string>[] = [];
  prohibitedTimes.subscribe((value) => (currentTimes = value))();

  currentTimes.splice(index, 1);
  prohibitedTimes.set([...currentTimes]);
}

// Format time restriction for display - more compact version
export function formatTimeRestriction(
  timeMap: Map<string, string> | Record<string, string>,
): string {
  // Ensure we're working with a Map
  const map =
    timeMap instanceof Map ? timeMap : new Map(Object.entries(timeMap));

  const days = (map.get("days") || "") as string;
  const start = formatTimeForDisplay((map.get("start_time") || "") as string);
  const end = formatTimeForDisplay((map.get("end_time") || "") as string);

  // Make day display more compact
  let dayDisplay = "";
  switch (days) {
    case "M":
      dayDisplay = "M";
      break;
    case "Tu":
      dayDisplay = "Tu";
      break;
    case "W":
      dayDisplay = "W";
      break;
    case "Th":
      dayDisplay = "Th";
      break;
    case "F":
      dayDisplay = "F";
      break;
    default:
      dayDisplay = days;
  }

  // Even more compact time display
  return `${dayDisplay}:${start}-${end}`;
}

// Format time string for display - ultra-compact version
export function formatTimeForDisplay(timeString: string): string {
  // Extract hour and minute from format like "08:00am"
  const match = timeString.match(/^(\d{1,2}):(\d{2})(am|pm)$/i);
  if (!match) return timeString;

  const [_, hour, minute, period] = match;
  const hourNum = parseInt(hour);
  const periodChar = period.charAt(0).toUpperCase();

  // Skip leading zero on hours and only show minutes if not :00
  const hourDisplay = hourNum.toString();
  const minuteDisplay = minute === "00" ? "" : minute;

  return `${hourDisplay}${minuteDisplay}${periodChar}`;
}

// Fetch class details and update professor associations
export async function fetchClassDetails(className: string, semester?: string): Promise<void> {
  let currentClassProfs: Record<string, string[]> = {};

  // Get latest class professors data
  classProfessors.subscribe((value) => (currentClassProfs = value))();

  // Get the semester directly from the store for consistency
  const selectedSemester = get(currentSemester);

  // Use provided semester or fall back to selected semester
  const semesterToUse = semester || selectedSemester || "202401";

  console.log(`Fetching details for ${className} with semester: ${semesterToUse}`);

  try {
    const url = new URL(`https://api.umd.io/v1/courses/${className}`);
    url.searchParams.set("semester", semesterToUse);

    const response = await fetch(url);
    const data = await response.json();

    if (Array.isArray(data) && data.length > 0) {
      // Extract professors from sections
      const professors: string[] = [];
      if (data[0].sections) {
        data[0].sections.forEach((section: any) => {
          if (section.instructors) {
            section.instructors.forEach((instructor: string) => {
              if (
                instructor &&
                instructor !== "Instructor: TBA" &&
                !professors.includes(instructor)
              ) {
                professors.push(instructor);
              }
            });
          }
        });
      }

      // Store the professors for this class
      currentClassProfs[className] = professors;
      classProfessors.set(currentClassProfs);
    }
  } catch (error) {
    console.error(`Error fetching details for ${className}:`, error);
  }
}

// Remove classes function
export function removeClasses(value: string): void {
  let currentAddedClasses: string[] = [];
  let currentAvailableClasses: string[] = [];
  let currentMap = new Map<string, string>();
  let currentClassProfs: Record<string, string[]> = {};
  let currentProhibitedProfs: string[] = [];

  // Get current values
  addedClasses.subscribe((c) => (currentAddedClasses = c))();
  availableClasses.subscribe((c) => (currentAvailableClasses = c))();
  colorMap.subscribe((c) => (currentMap = c))();
  classProfessors.subscribe((c) => (currentClassProfs = c))();
  prohibitedProfessors.subscribe((p) => (currentProhibitedProfs = p))();

  const index = currentAddedClasses.indexOf(value);
  if (index !== -1) {
    // Remove the class
    currentAddedClasses.splice(index, 1);
    addedClasses.set([...currentAddedClasses]);

    // Remove the color from the map
    currentMap.delete(value);
    colorMap.set(currentMap);

    // Update modal array
    showClassModals.set(new Array(currentAddedClasses.length).fill(false));

    // Add back to available classes
    if (!currentAvailableClasses.includes(value)) {
      currentAvailableClasses.push(value);
      currentAvailableClasses.sort();
      availableClasses.set(currentAvailableClasses);
    }

    // Remove professors that were only associated with this class
    const profsToKeep = new Set<string>();

    // Collect all professors from remaining classes
    Object.entries(currentClassProfs).forEach(([className, profs]) => {
      if (className !== value && currentAddedClasses.includes(className)) {
        profs.forEach((prof) => profsToKeep.add(prof));
      }
    });

    // Filter out professors that are no longer needed
    currentProhibitedProfs = currentProhibitedProfs.filter((prof) =>
      profsToKeep.has(prof),
    );
    prohibitedProfessors.set(currentProhibitedProfs);

    // Update professor modals
    showProfessorModals.set(
      new Array(currentProhibitedProfs.length).fill(false),
    );

    // Remove the class from the classProfessors map
    delete currentClassProfs[value];
    classProfessors.set(currentClassProfs);
  }
}

// Professor prohibition and related functions
export async function prohibitProf(prof: string): Promise<void> {
  let currentProfs: string[] = [];
  prohibitedProfessors.subscribe((p) => (currentProfs = p))();

  if (currentProfs.includes(prof)) {
    return;
  }

  currentProfs.push(prof);
  prohibitedProfessors.set([...currentProfs]);

  // Update modal array
  showProfessorModals.set(new Array(currentProfs.length).fill(false));
}

export function reAddProfessor(prof: string): void {
  let currentProfs: string[] = [];
  prohibitedProfessors.subscribe((p) => (currentProfs = p))();

  if (!currentProfs.includes(prof)) {
    return;
  }

  const index = currentProfs.indexOf(prof);
  currentProfs.splice(index, 1);
  prohibitedProfessors.set([...currentProfs]);

  // Update modal array
  showProfessorModals.set(new Array(currentProfs.length).fill(false));
}

// Modal management functions
export function closeClassModal(index: number): void {
  let modals: boolean[] = [];
  showClassModals.subscribe((m) => (modals = m))();

  modals[index] = false;
  showClassModals.set([...modals]);
}

export function closeProfModal(index: number): void {
  let modals: boolean[] = [];
  showProfessorModals.subscribe((m) => (modals = m))();

  modals[index] = false;
  showProfessorModals.set([...modals]);
}

// Professor view handling
export function viewProfessorDetails(event: CustomEvent): void {
  const { professorName, returnTo } = event.detail;

  let profInfos: ProfessorViewInfo[] = [];
  viewProfessorInfo.subscribe((p) => (profInfos = p))();

  const existingIndex = profInfos.findIndex((p) => p.name === professorName);

  if (existingIndex >= 0) {
    profInfos[existingIndex].showModal = true;
    profInfos[existingIndex].returnTo = returnTo;
  } else {
    profInfos = [
      ...profInfos,
      {
        name: professorName,
        showModal: true,
        returnTo,
      },
    ];
  }

  viewProfessorInfo.set(profInfos);
}

export function closeViewProfessorModal(
  index: number,
  event?: CustomEvent,
): void {
  let profInfos: ProfessorViewInfo[] = [];
  viewProfessorInfo.subscribe((p) => (profInfos = p))();

  const profInfo = profInfos[index];
  if (profInfo) {
    // Store the returnTo data before updating the state
    const returnToData = profInfo.returnTo;

    // Update modal visibility
    profInfo.showModal = false;
    viewProfessorInfo.set([...profInfos]);

    // After a brief delay to allow animation to complete, completely remove the entry
    setTimeout(() => {
      // Remove the entry from the array to fully reset the state
      profInfos = profInfos.filter((_, i) => i !== index);
      viewProfessorInfo.set(profInfos);

      // Then handle return navigation if needed
      if (returnToData && event?.detail?.returnTo) {
        if (returnToData.type === "class") {
          let classModals: boolean[] = [];
          showClassModals.subscribe((m) => (classModals = m))();

          classModals[returnToData.index] = true;
          showClassModals.set([...classModals]);
        }
      }
    }, 300); // Wait for the modal close animation to complete
  }
}

// Schedule sorting function
export function sortSchedules(scheduleList: any[]): any[] {
  let option = "";
  sortOption.subscribe((o) => (option = o))();

  if (option === "rating") {
    return [...scheduleList].sort(
      (a, b) => b["prof_weight"] - a["prof_weight"],
    );
  } else {
    // Add more sorting options as needed
    return scheduleList;
  }
}

// Helper function to darken colors for borders
export function shade(color: string, percent: number): string {
  // Parse the HSL color
  const match = color.match(/hsl\((\d+),\s*(\d+)%,\s*(\d+)%\)/);
  if (!match) return color;

  const h = parseInt(match[1], 10);
  const s = parseInt(match[2], 10);
  // Darken the lightness by the given percentage
  const l = Math.max(parseInt(match[3], 10) - percent, 0);

  return `hsl(${h}, ${s}%, ${l}%)`;
}

// Helper function to check if two time restrictions are equal
export function areTimeRestrictionsEqual(
  restriction1: Map<string, string> | Record<string, string>,
  restriction2: Map<string, string> | Record<string, string>,
): boolean {
  // Convert both to Maps for consistent handling
  const map1 =
    restriction1 instanceof Map
      ? restriction1
      : new Map(Object.entries(restriction1));
  const map2 =
    restriction2 instanceof Map
      ? restriction2
      : new Map(Object.entries(restriction2));

  // Check if all relevant properties match
  return (
    map1.get("days") === map2.get("days") &&
    map1.get("start_time") === map2.get("start_time") &&
    map1.get("end_time") === map2.get("end_time")
  );
}

// Function to add time restriction checking for duplicates
export function addTimeRestriction(
  restriction: Map<string, string> | Record<string, string>,
  currentRestrictions: (Map<string, string> | Record<string, string>)[],
): (Map<string, string> | Record<string, string>)[] {
  // Check if an identical restriction already exists
  const isDuplicate = currentRestrictions.some((existingRestriction) =>
    areTimeRestrictionsEqual(existingRestriction, restriction),
  );

  // Only add if not a duplicate
  if (!isDuplicate) {
    return [...currentRestrictions, restriction];
  }

  // Return original array if duplicate found
  return currentRestrictions;
}

// Function to add multiple time restrictions checking for duplicates
export function addMultipleTimeRestrictions(
  newRestrictions: (Map<string, string> | Record<string, string>)[],
  currentRestrictions: (Map<string, string> | Record<string, string>)[],
): (Map<string, string> | Record<string, string>)[] {
  // Start with current restrictions
  let updatedRestrictions = [...currentRestrictions];

  // Add each new restriction checking for duplicates
  for (const restriction of newRestrictions) {
    updatedRestrictions = addTimeRestriction(restriction, updatedRestrictions);
  }

  return updatedRestrictions;
}

// Format semester code to display format (YYYYMM to "Season YYYY")
export function formatSemester(semesterCode: string): string {
  if (!semesterCode || semesterCode.length !== 6) {
    return "Unknown Semester";
  }

  const year = semesterCode.substring(0, 4);
  const month = semesterCode.substring(4, 6);

  let season = "Unknown";
  // Correct UMD semester codes: 01=Spring, 05=Summer, 08=Fall, 12=Winter
  switch (month) {
    case "01": season = "Spring"; break;
    case "05": season = "Summer"; break;
    case "08": season = "Fall"; break;
    case "12": season = "Winter"; break;
  }

  return `${season} ${year}`;
}

// Function to fetch available semesters with improved handling
export async function fetchSemesters(): Promise<void> {
  try {
    const response = await fetch("https://api.umd.io/v1/courses/semesters");
    if (!response.ok) {
      throw new Error(`Failed to fetch semesters: ${response.status}`);
    }

    const data = await response.json();

    if (Array.isArray(data)) {
      // Make sure all elements are strings before sorting
      const semestersAsStrings = data.map(item => String(item));

      // Sort semesters in descending order (newest first)
      const sortedSemesters = [...semestersAsStrings].sort((a, b) => String(b).localeCompare(String(a)));

      // Limit to only the 3 most recent semesters
      const recentSemesters = sortedSemesters.slice(0, 3);

      // Always select most recent semester by default (first in sorted list)
      const mostRecentSemester = recentSemesters[0] || "202401"; // Fallback if list is empty

      console.log(`Setting current semester to: ${mostRecentSemester} (${formatSemester(mostRecentSemester)})`);
      console.log(`Available semesters limited to the 3 most recent: ${recentSemesters.map(sem => formatSemester(sem)).join(', ')}`);

      // Update stores with limited semesters
      availableSemesters.set(recentSemesters);
      currentSemester.set(mostRecentSemester);
    } else {
      console.error("Unexpected response format from semesters API:", data);
      currentSemester.set("202401"); // Spring 2024 as fallback
    }
  } catch (error) {
    console.error("Error fetching semesters:", error);
    currentSemester.set("202401"); // Spring 2024 as fallback
  }
}

// Function to fetch available classes with semester parameter
export async function fetchAvailableClasses(semester: string): Promise<void> {
  try {
    const url = new URL("https://api.umd.io/v1/courses/list");
    url.searchParams.set("sort", "course_id,-credits");
    url.searchParams.set("semester", semester);

    console.log(
      `Fetching available classes for semester: ${semester} (${formatSemester(semester)})`,
    );

    const response = await fetch(url);
    const data = await response.json();
    availableClasses.set(data.map(
      (item: { course_id: string }) => item.course_id,
    ));
  } catch (err) {
    error.set(
      err instanceof Error ? err.message : "Failed to fetch classes"
    );
    console.error("Error fetching classes:", err);
  }
}

// Handle semester change to reload classes
export function handleSemesterChange(): void {
  // Clear current schedules and classes when semester changes
  schedules.set([]);
  generatedSchedules.set([]);
  error.set(null);

  // Clear added classes when semester changes to prevent conflicts
  addedClasses.set([]);
  showClassModals.set([]);

  // Refresh available classes for the new semester
  const semester = get(currentSemester);
  fetchAvailableClasses(semester);
}
