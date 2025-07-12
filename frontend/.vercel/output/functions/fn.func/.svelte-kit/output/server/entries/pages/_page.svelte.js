import { G as fallback, I as bind_props, C as pop, z as push, J as attr, K as ensure_array_like, F as escape_html, M as attr_style, N as stringify, O as store_get, P as unsubscribe_stores } from "../../chunks/index.js";
import "clsx";
import { w as writable, g as get } from "../../chunks/index2.js";
function ClassModal($$payload, $$props) {
  push();
  let className = $$props["className"];
  let showModal = $$props["showModal"];
  let prohibitedProfessors2 = fallback($$props["prohibitedProfessors"], () => [], true);
  let showProfessorModals2 = fallback($$props["showProfessorModals"], () => [], true);
  let index = $$props["index"];
  let closeModal = $$props["closeModal"];
  let removeClasses2 = $$props["removeClasses"];
  let prohibitProf2 = $$props["prohibitProf"];
  let reAddProfessor2 = $$props["reAddProfessor"];
  $$payload.out += `<dialog class="modal svelte-1iml2y7"><div class="modal-content svelte-1iml2y7">`;
  {
    $$payload.out += "<!--[-->";
    $$payload.out += `<div class="loading svelte-1iml2y7"><div class="spinner svelte-1iml2y7"></div> <p class="svelte-1iml2y7">Loading course information...</p></div>`;
  }
  $$payload.out += `<!--]--></div></dialog>`;
  bind_props($$props, {
    className,
    showModal,
    prohibitedProfessors: prohibitedProfessors2,
    showProfessorModals: showProfessorModals2,
    index,
    closeModal,
    removeClasses: removeClasses2,
    prohibitProf: prohibitProf2,
    reAddProfessor: reAddProfessor2
  });
  pop();
}
function AddClassModal($$payload, $$props) {
  push();
  let filteredClasses;
  let showAddClassModal2 = $$props["showAddClassModal"];
  let availableClasses2 = fallback($$props["availableClasses"], () => [], true);
  let addedClasses2 = fallback($$props["addedClasses"], () => [], true);
  let classInput = "";
  filteredClasses = availableClasses2.filter((x) => x.includes(classInput.toUpperCase())).slice(0, 50);
  $$payload.out += `<dialog class="modal svelte-1j02xbn"><div class="modal-content svelte-1j02xbn"><div class="modal-header svelte-1j02xbn"><h1 class="svelte-1j02xbn">Add A Class</h1> <button class="close-btn svelte-1j02xbn"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg></button></div> <div id="search-column" class="svelte-1j02xbn"><input class="class-search-bar svelte-1j02xbn"${attr("value", classInput)} placeholder="Search for classes (e.g. CMSC131)" autofocus> `;
  if (classInput.length) {
    $$payload.out += "<!--[-->";
    $$payload.out += `<div class="filtered-class-list svelte-1j02xbn">`;
    if (filteredClasses.length === 0) {
      $$payload.out += "<!--[-->";
      $$payload.out += `<div class="no-results svelte-1j02xbn">No matches found</div>`;
    } else {
      $$payload.out += "<!--[!-->";
      const each_array = ensure_array_like(filteredClasses);
      $$payload.out += `<!--[-->`;
      for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
        let value = each_array[$$index];
        $$payload.out += `<button class="filtered-class-list-item svelte-1j02xbn">${escape_html(value)}</button>`;
      }
      $$payload.out += `<!--]-->`;
    }
    $$payload.out += `<!--]--></div>`;
  } else {
    $$payload.out += "<!--[!-->";
  }
  $$payload.out += `<!--]--></div></div></dialog>`;
  bind_props($$props, {
    showAddClassModal: showAddClassModal2,
    availableClasses: availableClasses2,
    addedClasses: addedClasses2
  });
  pop();
}
function TimeSelectionModal($$payload, $$props) {
  push();
  let hasDaySelected;
  let showTimeSelectionModal2 = fallback($$props["showTimeSelectionModal"], false);
  const prohibitedTimes2 = [];
  let selectedDays = {
    Monday: false,
    Tuesday: false,
    Wednesday: false,
    Thursday: false,
    Friday: false
  };
  const dayNames = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday"
  ];
  const hours = Array.from({ length: 12 }, (_, i) => String(i + 1));
  const minutes = ["00", "15", "30", "45"];
  const ampm = ["AM", "PM"];
  hasDaySelected = Object.values(selectedDays).some((selected) => selected);
  const each_array = ensure_array_like(dayNames);
  const each_array_1 = ensure_array_like(hours);
  const each_array_2 = ensure_array_like(minutes);
  const each_array_3 = ensure_array_like(ampm);
  const each_array_4 = ensure_array_like(hours);
  const each_array_5 = ensure_array_like(minutes);
  const each_array_6 = ensure_array_like(ampm);
  $$payload.out += `<dialog class="modal svelte-lrxo2l"><div class="modal-content svelte-lrxo2l" role="dialog"><div class="modal-header svelte-lrxo2l"><h1 class="svelte-lrxo2l">Add Time Restriction</h1> <button class="close-btn svelte-lrxo2l"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg></button></div> <form><div class="form-group svelte-lrxo2l"><label class="form-label svelte-lrxo2l">Select Days</label> <div class="days-grid svelte-lrxo2l"><!--[-->`;
  for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
    let day = each_array[$$index];
    $$payload.out += `<label class="day-checkbox svelte-lrxo2l"><input type="checkbox"${attr("checked", selectedDays[day], true)} class="svelte-lrxo2l"> <span class="checkbox-display svelte-lrxo2l">${escape_html(day.substring(0, 3))}</span></label>`;
  }
  $$payload.out += `<!--]--></div> <div class="day-actions svelte-lrxo2l"><button type="button" class="btn-link svelte-lrxo2l">Select All</button> <button type="button" class="btn-link svelte-lrxo2l">Clear All</button></div></div> <div class="time-container svelte-lrxo2l"><div class="time-section svelte-lrxo2l"><label class="form-label svelte-lrxo2l">Start Time</label> <div class="time-inputs svelte-lrxo2l"><select class="time-select svelte-lrxo2l"><!--[-->`;
  for (let $$index_1 = 0, $$length = each_array_1.length; $$index_1 < $$length; $$index_1++) {
    let hour = each_array_1[$$index_1];
    $$payload.out += `<option${attr("value", hour)}>${escape_html(hour)}</option>`;
  }
  $$payload.out += `<!--]--></select> <span class="time-separator svelte-lrxo2l">:</span> <select class="time-select svelte-lrxo2l"><!--[-->`;
  for (let $$index_2 = 0, $$length = each_array_2.length; $$index_2 < $$length; $$index_2++) {
    let minute = each_array_2[$$index_2];
    $$payload.out += `<option${attr("value", minute)}>${escape_html(minute)}</option>`;
  }
  $$payload.out += `<!--]--></select> <select class="ampm-select svelte-lrxo2l"><!--[-->`;
  for (let $$index_3 = 0, $$length = each_array_3.length; $$index_3 < $$length; $$index_3++) {
    let period = each_array_3[$$index_3];
    $$payload.out += `<option${attr("value", period)}>${escape_html(period)}</option>`;
  }
  $$payload.out += `<!--]--></select></div></div> <div class="time-section svelte-lrxo2l"><label class="form-label svelte-lrxo2l">End Time</label> <div class="time-inputs svelte-lrxo2l"><select class="time-select svelte-lrxo2l"><!--[-->`;
  for (let $$index_4 = 0, $$length = each_array_4.length; $$index_4 < $$length; $$index_4++) {
    let hour = each_array_4[$$index_4];
    $$payload.out += `<option${attr("value", hour)}>${escape_html(hour)}</option>`;
  }
  $$payload.out += `<!--]--></select> <span class="time-separator svelte-lrxo2l">:</span> <select class="time-select svelte-lrxo2l"><!--[-->`;
  for (let $$index_5 = 0, $$length = each_array_5.length; $$index_5 < $$length; $$index_5++) {
    let minute = each_array_5[$$index_5];
    $$payload.out += `<option${attr("value", minute)}>${escape_html(minute)}</option>`;
  }
  $$payload.out += `<!--]--></select> <select class="ampm-select svelte-lrxo2l"><!--[-->`;
  for (let $$index_6 = 0, $$length = each_array_6.length; $$index_6 < $$length; $$index_6++) {
    let period = each_array_6[$$index_6];
    $$payload.out += `<option${attr("value", period)}>${escape_html(period)}</option>`;
  }
  $$payload.out += `<!--]--></select></div></div></div> <div class="form-footer svelte-lrxo2l"><button type="button" class="btn btn-outline svelte-lrxo2l">Cancel</button> <button type="submit" class="btn btn-primary svelte-lrxo2l"${attr("disabled", !hasDaySelected, true)}>Add Restriction${escape_html(selectedDays && Object.values(selectedDays).filter(Boolean).length > 1 ? "s" : "")}</button></div></form></div></dialog>`;
  bind_props($$props, { showTimeSelectionModal: showTimeSelectionModal2, prohibitedTimes: prohibitedTimes2 });
  pop();
}
function ProfessorModal($$payload, $$props) {
  push();
  let addedClasses2 = $$props["addedClasses"];
  let showModal = $$props["showModal"];
  let profName = $$props["profName"];
  let index = $$props["index"];
  let closeModal = $$props["closeModal"];
  let reAddProfessor2 = $$props["reAddProfessor"];
  let isViewOnly = fallback($$props["isViewOnly"], false);
  let returnTo = fallback($$props["returnTo"], null);
  $$payload.out += `<dialog class="modal svelte-zb7ob1"><div class="modal-content svelte-zb7ob1">`;
  {
    $$payload.out += "<!--[-->";
    $$payload.out += `<div class="loading svelte-zb7ob1"><div class="spinner svelte-zb7ob1"></div> <p class="svelte-zb7ob1">Loading professor information...</p></div>`;
  }
  $$payload.out += `<!--]--></div></dialog>`;
  bind_props($$props, {
    addedClasses: addedClasses2,
    showModal,
    profName,
    index,
    closeModal,
    reAddProfessor: reAddProfessor2,
    isViewOnly,
    returnTo
  });
  pop();
}
const availableClasses = writable([]);
const addedClasses = writable([]);
const prohibitedTimes = writable([]);
const prohibitedProfessors = writable([]);
const generatedSchedules = writable([]);
const colorMap = writable(/* @__PURE__ */ new Map());
const showTimeSelectionModal = writable(false);
const showAddClassModal = writable(false);
const generatingSchedules = writable(false);
const showClassModals = writable([]);
const showProfessorModals = writable([]);
const schedules = writable([]);
const sortOption = writable("rating");
const error = writable(null);
const viewProfessorInfo = writable([]);
const classProfessors = writable({});
const currentSemester = writable("");
const availableSemesters = writable([]);
function generateColor(index) {
  const hues = [210, 180, 120, 330, 270, 30, 150, 300, 60, 240];
  const hue = hues[index % hues.length];
  return `hsl(${hue}, 70%, 85%)`;
}
function formatTimeRestriction(timeMap) {
  const map = timeMap instanceof Map ? timeMap : new Map(Object.entries(timeMap));
  const days = map.get("days") || "";
  const start = formatTimeForDisplay(map.get("start_time") || "");
  const end = formatTimeForDisplay(map.get("end_time") || "");
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
  return `${dayDisplay}:${start}-${end}`;
}
function formatTimeForDisplay(timeString) {
  const match = timeString.match(/^(\d{1,2}):(\d{2})(am|pm)$/i);
  if (!match) return timeString;
  const [_, hour, minute, period] = match;
  const hourNum = parseInt(hour);
  const periodChar = period.charAt(0).toUpperCase();
  const hourDisplay = hourNum.toString();
  const minuteDisplay = minute === "00" ? "" : minute;
  return `${hourDisplay}${minuteDisplay}${periodChar}`;
}
function removeClasses(value) {
  let currentAddedClasses = [];
  let currentAvailableClasses = [];
  let currentMap = /* @__PURE__ */ new Map();
  let currentClassProfs = {};
  let currentProhibitedProfs = [];
  addedClasses.subscribe((c) => currentAddedClasses = c)();
  availableClasses.subscribe((c) => currentAvailableClasses = c)();
  colorMap.subscribe((c) => currentMap = c)();
  classProfessors.subscribe((c) => currentClassProfs = c)();
  prohibitedProfessors.subscribe((p) => currentProhibitedProfs = p)();
  const index = currentAddedClasses.indexOf(value);
  if (index !== -1) {
    currentAddedClasses.splice(index, 1);
    addedClasses.set([...currentAddedClasses]);
    currentMap.delete(value);
    colorMap.set(currentMap);
    showClassModals.set(new Array(currentAddedClasses.length).fill(false));
    if (!currentAvailableClasses.includes(value)) {
      currentAvailableClasses.push(value);
      currentAvailableClasses.sort();
      availableClasses.set(currentAvailableClasses);
    }
    const profsToKeep = /* @__PURE__ */ new Set();
    Object.entries(currentClassProfs).forEach(([className, profs]) => {
      if (className !== value && currentAddedClasses.includes(className)) {
        profs.forEach((prof) => profsToKeep.add(prof));
      }
    });
    currentProhibitedProfs = currentProhibitedProfs.filter(
      (prof) => profsToKeep.has(prof)
    );
    prohibitedProfessors.set(currentProhibitedProfs);
    showProfessorModals.set(
      new Array(currentProhibitedProfs.length).fill(false)
    );
    delete currentClassProfs[value];
    classProfessors.set(currentClassProfs);
  }
}
async function prohibitProf(prof) {
  let currentProfs = [];
  prohibitedProfessors.subscribe((p) => currentProfs = p)();
  if (currentProfs.includes(prof)) {
    return;
  }
  currentProfs.push(prof);
  prohibitedProfessors.set([...currentProfs]);
  showProfessorModals.set(new Array(currentProfs.length).fill(false));
}
function reAddProfessor(prof) {
  let currentProfs = [];
  prohibitedProfessors.subscribe((p) => currentProfs = p)();
  if (!currentProfs.includes(prof)) {
    return;
  }
  const index = currentProfs.indexOf(prof);
  currentProfs.splice(index, 1);
  prohibitedProfessors.set([...currentProfs]);
  showProfessorModals.set(new Array(currentProfs.length).fill(false));
}
function closeClassModal(index) {
  let modals = [];
  showClassModals.subscribe((m) => modals = m)();
  modals[index] = false;
  showClassModals.set([...modals]);
}
function closeProfModal(index) {
  let modals = [];
  showProfessorModals.subscribe((m) => modals = m)();
  modals[index] = false;
  showProfessorModals.set([...modals]);
}
function closeViewProfessorModal(index, event) {
  let profInfos = [];
  viewProfessorInfo.subscribe((p) => profInfos = p)();
  const profInfo = profInfos[index];
  if (profInfo) {
    const returnToData = profInfo.returnTo;
    profInfo.showModal = false;
    viewProfessorInfo.set([...profInfos]);
    setTimeout(() => {
      profInfos = profInfos.filter((_, i) => i !== index);
      viewProfessorInfo.set(profInfos);
      if (returnToData && event?.detail?.returnTo) {
        if (returnToData.type === "class") {
          let classModals = [];
          showClassModals.subscribe((m) => classModals = m)();
          classModals[returnToData.index] = true;
          showClassModals.set([...classModals]);
        }
      }
    }, 300);
  }
}
function sortSchedules(scheduleList) {
  let option = "";
  sortOption.subscribe((o) => option = o)();
  if (option === "rating") {
    return [...scheduleList].sort(
      (a, b) => b["prof_weight"] - a["prof_weight"]
    );
  } else {
    return scheduleList;
  }
}
function shade(color, percent) {
  const match = color.match(/hsl\((\d+),\s*(\d+)%,\s*(\d+)%\)/);
  if (!match) return color;
  const h = parseInt(match[1], 10);
  const s = parseInt(match[2], 10);
  const l = Math.max(parseInt(match[3], 10) - percent, 0);
  return `hsl(${h}, ${s}%, ${l}%)`;
}
function formatSemester(semesterCode) {
  if (!semesterCode || semesterCode.length !== 6) {
    return "Unknown Semester";
  }
  const year = semesterCode.substring(0, 4);
  const month = semesterCode.substring(4, 6);
  let season = "Unknown";
  switch (month) {
    case "01":
      season = "Spring";
      break;
    case "05":
      season = "Summer";
      break;
    case "08":
      season = "Fall";
      break;
    case "12":
      season = "Winter";
      break;
  }
  return `${season} ${year}`;
}
async function fetchAvailableClasses(semester) {
  try {
    const url = new URL("https://api.umd.io/v1/courses/list");
    url.searchParams.set("sort", "course_id,-credits");
    url.searchParams.set("semester", semester);
    console.log(
      `Fetching available classes for semester: ${semester} (${formatSemester(semester)})`
    );
    const response = await fetch(url);
    const data = await response.json();
    availableClasses.set(data.map(
      (item) => item.course_id
    ));
  } catch (err) {
    error.set(
      err instanceof Error ? err.message : "Failed to fetch classes"
    );
    console.error("Error fetching classes:", err);
  }
}
function handleSemesterChange() {
  schedules.set([]);
  generatedSchedules.set([]);
  error.set(null);
  addedClasses.set([]);
  showClassModals.set([]);
  const semester = get(currentSemester);
  fetchAvailableClasses(semester);
}
function ScheduleView($$payload, $$props) {
  push();
  let dayLabels = [[], [], [], [], []];
  let daysCodes = ["M", "Tu", "W", "Th", "F"];
  let dayNames = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday"
  ];
  let colorMap2 = fallback($$props["colorMap"], () => /* @__PURE__ */ new Map(), true);
  let scheduleData = $$props["scheduleData"];
  let scheduleIndex = fallback($$props["scheduleIndex"], 0);
  const hourHeight = 60;
  const dayHeaderHeight = 50;
  let earliestStart = 480;
  let latestEnd = 1200;
  const totalHours = (latestEnd - earliestStart) / 60;
  const scheduleHeight = totalHours * hourHeight;
  let timeLabels = [];
  for (let i = earliestStart; i <= latestEnd; i += 60) {
    const hour = Math.floor(i / 60);
    const meridiem = hour >= 12 ? "PM" : "AM";
    const displayHour = hour > 12 ? hour - 12 : hour === 0 ? 12 : hour;
    timeLabels.push(`${displayHour}:00 ${meridiem}`);
  }
  function formatSlots(day) {
    return day.sort((a, b) => a.startPixels - b.startPixels);
  }
  function calculateAverageRating() {
    if (!scheduleData) return "N/A";
    let totalRating = 0;
    let countRated = 0;
    Object.keys(scheduleData).forEach((className) => {
      if (scheduleData[className] && scheduleData[className]["prof_weight"]) {
        totalRating += parseFloat(scheduleData[className]["prof_weight"]);
        countRated++;
      }
    });
    if (countRated === 0) return "N/A";
    return (totalRating / countRated).toFixed(2);
  }
  const avgProfRating = calculateAverageRating();
  const each_array = ensure_array_like(timeLabels);
  const each_array_1 = ensure_array_like(dayNames);
  const each_array_2 = ensure_array_like(timeLabels);
  const each_array_3 = ensure_array_like(daysCodes);
  $$payload.out += `<div class="schedule-wrapper"><div class="schedule-header"><div class="schedule-info"><div class="schedule-number"><span class="schedule-badge">#${escape_html(scheduleIndex + 1)}</span> <h3>Schedule</h3></div> <div class="rating-badge"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg> <span class="rating-value">${escape_html(avgProfRating)}</span> <span class="rating-label">Avg. Professor Rating</span></div></div></div> <div class="schedule-container"><div class="time-labels"${attr_style(`padding-top: ${stringify(dayHeaderHeight)}px;`)}><!--[-->`;
  for (let i = 0, $$length = each_array.length; i < $$length; i++) {
    let time = each_array[i];
    $$payload.out += `<div class="time-label"${attr_style(`height: ${stringify(hourHeight)}px;`)}>${escape_html(time)}</div>`;
  }
  $$payload.out += `<!--]--></div> <div class="schedule-content"><div class="day-headers"${attr_style(`height: ${stringify(dayHeaderHeight)}px;`)}><!--[-->`;
  for (let i = 0, $$length = each_array_1.length; i < $$length; i++) {
    let day = each_array_1[i];
    $$payload.out += `<div class="day-header">${escape_html(day)}</div>`;
  }
  $$payload.out += `<!--]--></div> <div class="grid-area"${attr_style(`height: ${stringify(scheduleHeight)}px;`)}><div class="grid-lines"><!--[-->`;
  for (let i = 0, $$length = each_array_2.length; i < $$length; i++) {
    each_array_2[i];
    $$payload.out += `<div class="grid-line"${attr_style(`top: ${stringify(i * hourHeight)}px; height: ${stringify(hourHeight)}px;`)}></div>`;
  }
  $$payload.out += `<!--]--></div> <div class="day-columns"><!--[-->`;
  for (let i = 0, $$length = each_array_3.length; i < $$length; i++) {
    each_array_3[i];
    const each_array_4 = ensure_array_like(formatSlots(dayLabels[i] || []));
    $$payload.out += `<div class="schedule-column"><!--[-->`;
    for (let $$index_3 = 0, $$length2 = each_array_4.length; $$index_3 < $$length2; $$index_3++) {
      let slot = each_array_4[$$index_3];
      $$payload.out += `<div class="schedule-slot"${attr_style(` top: ${stringify(slot.startPixels)}px; height: ${stringify(slot.heightPixels)}px; background: ${stringify(colorMap2.get(slot.class) || "#f0f0f0")}; ${stringify(slot.horizontalPosition !== void 0 ? `left: calc(${slot.horizontalPosition * (100 / slot.totalOverlap)}%); 
												width: calc(${100 / slot.totalOverlap}%);` : "left: 0; right: 0;")} `)}><div class="slot-content"><div class="class-row"><span class="class-name">${escape_html(slot.class)}</span> <span class="section-number">§${escape_html(slot.sectionCode)}</span></div> <div class="info-row"><span class="slot-location">${escape_html(slot.location)}</span> <span class="slot-time">${escape_html(slot.startTime.replace(":00", ""))}-${escape_html(slot.endTime.replace(":00", ""))}</span></div></div> <div class="slot-tooltip"${attr_style(` background: ${stringify(colorMap2.get(slot.class) || "#f0f0f0")}; border-color: ${stringify(colorMap2.get(slot.class) ? "rgba(0, 0, 0, 0.1)" : "rgba(0, 0, 0, 0.1)")}; `)}><div class="tooltip-professor">${escape_html(slot.professor)} `;
      if (slot.prof_rating) {
        $$payload.out += "<!--[-->";
        $$payload.out += `<span class="tooltip-rating">(${escape_html(Number(slot.prof_rating).toFixed(1))} ⭐)</span>`;
      } else {
        $$payload.out += "<!--[!-->";
      }
      $$payload.out += `<!--]--></div></div></div>`;
    }
    $$payload.out += `<!--]--></div>`;
  }
  $$payload.out += `<!--]--></div></div></div></div></div> `;
  {
    $$payload.out += "<!--[!-->";
  }
  $$payload.out += `<!--]-->`;
  bind_props($$props, { colorMap: colorMap2, scheduleData, scheduleIndex });
  pop();
}
function SemesterSelector($$payload, $$props) {
  push();
  var $$store_subs;
  let onChange = fallback($$props["onChange"], null);
  $$payload.out += `<div class="semester-selector svelte-amq68y"><select aria-label="Select semester" class="svelte-amq68y">`;
  if (store_get($$store_subs ??= {}, "$availableSemesters", availableSemesters).length === 0) {
    $$payload.out += "<!--[-->";
    $$payload.out += `<option value="202508">Loading semesters...</option>`;
  } else {
    $$payload.out += "<!--[!-->";
    const each_array = ensure_array_like(store_get($$store_subs ??= {}, "$availableSemesters", availableSemesters));
    $$payload.out += `<!--[-->`;
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let semester = each_array[$$index];
      $$payload.out += `<option${attr("value", semester)}>${escape_html(formatSemester(semester))}</option>`;
    }
    $$payload.out += `<!--]-->`;
  }
  $$payload.out += `<!--]--></select></div>`;
  if ($$store_subs) unsubscribe_stores($$store_subs);
  bind_props($$props, { onChange });
  pop();
}
function _page($$payload, $$props) {
  push();
  var $$store_subs;
  let sortedSchedules;
  sortedSchedules = sortSchedules(store_get($$store_subs ??= {}, "$schedules", schedules));
  {
    store_get($$store_subs ??= {}, "$addedClasses", addedClasses).forEach((className, index) => {
      if (!store_get($$store_subs ??= {}, "$colorMap", colorMap).has(className)) {
        store_get($$store_subs ??= {}, "$colorMap", colorMap).set(className, generateColor(index));
      }
    });
  }
  const each_array = ensure_array_like(store_get($$store_subs ??= {}, "$addedClasses", addedClasses));
  const each_array_1 = ensure_array_like(store_get($$store_subs ??= {}, "$prohibitedProfessors", prohibitedProfessors));
  const each_array_2 = ensure_array_like(store_get($$store_subs ??= {}, "$prohibitedTimes", prohibitedTimes));
  const each_array_4 = ensure_array_like(store_get($$store_subs ??= {}, "$addedClasses", addedClasses));
  const each_array_5 = ensure_array_like(store_get($$store_subs ??= {}, "$viewProfessorInfo", viewProfessorInfo));
  const each_array_6 = ensure_array_like(store_get($$store_subs ??= {}, "$prohibitedProfessors", prohibitedProfessors));
  $$payload.out += `<div class="app-container"><header class="app-header"><div class="header-content"><div class="header-left"><h1 class="app-title">UMD Scheduler</h1> `;
  SemesterSelector($$payload, { onChange: handleSemesterChange });
  $$payload.out += `<!----></div> <div class="header-actions"><button class="btn btn-outline"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg> Add Time Restriction</button> <button class="btn btn-outline"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"></path></svg> Add Class</button> <button class="btn btn-primary"${attr("disabled", store_get($$store_subs ??= {}, "$generatingSchedules", generatingSchedules), true)}><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6l9 6 9-6M3 12l9 6 9-6"></path></svg> ${escape_html(store_get($$store_subs ??= {}, "$generatingSchedules", generatingSchedules) ? "Generating..." : "Generate Schedules")}</button></div></div></header> <main class="app-main"><div class="restrictions-container"><div class="restriction-box"><h2 class="restriction-title">Selected Classes</h2> <div class="restriction-items"><!--[-->`;
  for (let i = 0, $$length = each_array.length; i < $$length; i++) {
    let className = each_array[i];
    $$payload.out += `<button class="restriction-button"${attr_style(`background-color: ${stringify(store_get($$store_subs ??= {}, "$colorMap", colorMap).get(className) || "#f5f5f5")}; color: ${stringify(store_get($$store_subs ??= {}, "$colorMap", colorMap).get(className) ? "#333" : "#666")}; border-color: ${stringify(store_get($$store_subs ??= {}, "$colorMap", colorMap).get(className) ? shade(store_get($$store_subs ??= {}, "$colorMap", colorMap).get(className) ?? "#646464", 20) : "#e0e0e0")};`)}>${escape_html(className)}</button>`;
  }
  $$payload.out += `<!--]--></div></div> <div class="restriction-box"><h2 class="restriction-title">Professor Restrictions</h2> <div class="restriction-items"><!--[-->`;
  for (let i = 0, $$length = each_array_1.length; i < $$length; i++) {
    let prof = each_array_1[i];
    $$payload.out += `<button class="restriction-button professor-restriction">${escape_html(prof)}</button>`;
  }
  $$payload.out += `<!--]--></div></div> <div class="restriction-box"><h2 class="restriction-title">Time Restrictions</h2> <div class="restriction-items"><!--[-->`;
  for (let i = 0, $$length = each_array_2.length; i < $$length; i++) {
    let time = each_array_2[i];
    $$payload.out += `<div class="restriction-button time-restriction"><span class="restriction-text">${escape_html(formatTimeRestriction(time))}</span> <button class="remove-btn" aria-label="Remove time restriction"><svg class="remove-icon" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg></button></div>`;
  }
  $$payload.out += `<!--]--></div></div></div> `;
  if (store_get($$store_subs ??= {}, "$error", error)) {
    $$payload.out += "<!--[-->";
    $$payload.out += `<div class="error-message" role="alert"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg> ${escape_html(store_get($$store_subs ??= {}, "$error", error))}</div>`;
  } else {
    $$payload.out += "<!--[!-->";
  }
  $$payload.out += `<!--]--> `;
  if (store_get($$store_subs ??= {}, "$generatingSchedules", generatingSchedules)) {
    $$payload.out += "<!--[-->";
    $$payload.out += `<div class="loading-container"><div class="spinner"></div> <p>Generating schedules, please wait...</p></div>`;
  } else if (sortedSchedules.length === 0) {
    $$payload.out += "<!--[1-->";
    $$payload.out += `<div class="empty-state"><div class="empty-state-icon"><svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg></div> <h2>No schedules generated yet</h2> <p>Add some classes and click "Generate Schedules" to get
					started</p></div>`;
  } else {
    $$payload.out += "<!--[!-->";
    const each_array_3 = ensure_array_like(sortedSchedules);
    $$payload.out += `<div class="schedules-header"><h2>Generated Schedules</h2> <div class="schedules-count"><span class="badge">${escape_html(store_get($$store_subs ??= {}, "$generatedSchedules", generatedSchedules).length)}</span> possible
					schedules found</div></div> <div class="schedules-container"><!--[-->`;
    for (let i = 0, $$length = each_array_3.length; i < $$length; i++) {
      let schedule = each_array_3[i];
      ScheduleView($$payload, {
        scheduleData: schedule,
        colorMap: store_get($$store_subs ??= {}, "$colorMap", colorMap),
        scheduleIndex: i
      });
    }
    $$payload.out += `<!--]--></div>`;
  }
  $$payload.out += `<!--]--></main></div> `;
  if (store_get($$store_subs ??= {}, "$showTimeSelectionModal", showTimeSelectionModal)) {
    $$payload.out += "<!--[-->";
    TimeSelectionModal($$payload, {
      prohibitedTimes: store_get($$store_subs ??= {}, "$prohibitedTimes", prohibitedTimes),
      showTimeSelectionModal: store_get($$store_subs ??= {}, "$showTimeSelectionModal", showTimeSelectionModal)
    });
  } else {
    $$payload.out += "<!--[!-->";
  }
  $$payload.out += `<!--]--> `;
  if (store_get($$store_subs ??= {}, "$showAddClassModal", showAddClassModal)) {
    $$payload.out += "<!--[-->";
    AddClassModal($$payload, {
      availableClasses: store_get($$store_subs ??= {}, "$availableClasses", availableClasses),
      addedClasses: store_get($$store_subs ??= {}, "$addedClasses", addedClasses),
      showAddClassModal: store_get($$store_subs ??= {}, "$showAddClassModal", showAddClassModal)
    });
  } else {
    $$payload.out += "<!--[!-->";
  }
  $$payload.out += `<!--]--> <!--[-->`;
  for (let i = 0, $$length = each_array_4.length; i < $$length; i++) {
    each_array_4[i];
    if (store_get($$store_subs ??= {}, "$showClassModals", showClassModals)[i]) {
      $$payload.out += "<!--[-->";
      ClassModal($$payload, {
        className: store_get($$store_subs ??= {}, "$addedClasses", addedClasses)[i],
        showModal: store_get($$store_subs ??= {}, "$showClassModals", showClassModals)[i],
        prohibitedProfessors: store_get($$store_subs ??= {}, "$prohibitedProfessors", prohibitedProfessors),
        index: i,
        showProfessorModals: store_get($$store_subs ??= {}, "$showProfessorModals", showProfessorModals),
        closeModal: closeClassModal,
        removeClasses,
        prohibitProf,
        reAddProfessor
      });
    } else {
      $$payload.out += "<!--[!-->";
    }
    $$payload.out += `<!--]-->`;
  }
  $$payload.out += `<!--]--> <!--[-->`;
  for (let i = 0, $$length = each_array_5.length; i < $$length; i++) {
    let profInfo = each_array_5[i];
    if (profInfo.showModal) {
      $$payload.out += "<!--[-->";
      ProfessorModal($$payload, {
        profName: profInfo.name,
        addedClasses: store_get($$store_subs ??= {}, "$addedClasses", addedClasses),
        showModal: profInfo.showModal,
        index: i,
        closeModal: closeViewProfessorModal,
        reAddProfessor,
        isViewOnly: true,
        returnTo: profInfo.returnTo
      });
    } else {
      $$payload.out += "<!--[!-->";
    }
    $$payload.out += `<!--]-->`;
  }
  $$payload.out += `<!--]--> <!--[-->`;
  for (let i = 0, $$length = each_array_6.length; i < $$length; i++) {
    let prof = each_array_6[i];
    if (store_get($$store_subs ??= {}, "$showProfessorModals", showProfessorModals)[i]) {
      $$payload.out += "<!--[-->";
      ProfessorModal($$payload, {
        profName: prof,
        addedClasses: store_get($$store_subs ??= {}, "$addedClasses", addedClasses),
        showModal: store_get($$store_subs ??= {}, "$showProfessorModals", showProfessorModals)[i],
        index: i,
        closeModal: closeProfModal,
        reAddProfessor
      });
    } else {
      $$payload.out += "<!--[!-->";
    }
    $$payload.out += `<!--]-->`;
  }
  $$payload.out += `<!--]-->`;
  if ($$store_subs) unsubscribe_stores($$store_subs);
  pop();
}
export {
  _page as default
};
