const DEFAULT_WEEKDAY_TOKENS = {
    M: "Monday",
    T: "Tuesday",
    W: "Wednesday",
    R: "Thursday",
    F: "Friday",
};

function formatTimeFromMinutes(totalMinutes) {
    const hour = Math.floor(totalMinutes / 60);
    const minute = totalMinutes % 60;
    const period = hour >= 12 ? "PM" : "AM";
    const hour12 = hour % 12 === 0 ? 12 : hour % 12;
    return `${hour12}:${String(minute).padStart(2, "0")} ${period}`;
}

function parseTimeToMinutes(value) {
    if (!value || typeof value !== "string") return null;

    const normalized = value.trim().toLowerCase().replace(/\./g, "");
    const ampmMatch = normalized.match(/^(\d{1,2}):(\d{2})\s*(am|pm)$/);

    if (ampmMatch) {
        let hour = Number(ampmMatch[1]);
        const minute = Number(ampmMatch[2]);
        const period = ampmMatch[3];

        if (Number.isNaN(hour) || Number.isNaN(minute) || minute > 59) {
            return null;
        }

        if (period === "pm" && hour < 12) hour += 12;
        if (period === "am" && hour === 12) hour = 0;

        return hour * 60 + minute;
    }

    const twentyFourHourMatch = normalized.match(
        /^(\d{1,2}):(\d{2})(?::\d{2})?$/,
    );

    if (!twentyFourHourMatch) return null;

    const hour = Number(twentyFourHourMatch[1]);
    const minute = Number(twentyFourHourMatch[2]);

    if (
        Number.isNaN(hour) ||
        Number.isNaN(minute) ||
        hour < 0 ||
        hour > 23 ||
        minute < 0 ||
        minute > 59
    ) {
        return null;
    }

    return hour * 60 + minute;
}

function withNonOverlappingLanes(entries) {
    if (entries.length === 0) return [];

    const sortedEntries = [...entries].sort((left, right) => {
        if (left.startMinutes !== right.startMinutes) {
            return left.startMinutes - right.startMinutes;
        }

        return left.endMinutes - right.endMinutes;
    });

    const clusters = [];
    let activeCluster = [];
    let activeClusterMaxEnd = -1;

    for (const entry of sortedEntries) {
        if (activeCluster.length === 0 || entry.startMinutes < activeClusterMaxEnd) {
            activeCluster.push(entry);
            activeClusterMaxEnd = Math.max(activeClusterMaxEnd, entry.endMinutes);
            continue;
        }

        clusters.push(activeCluster);
        activeCluster = [entry];
        activeClusterMaxEnd = entry.endMinutes;
    }

    if (activeCluster.length > 0) {
        clusters.push(activeCluster);
    }

    const laidOutEntries = [];

    for (const cluster of clusters) {
        const laneEndTimes = [];
        const clusterEntries = [];

        for (const entry of cluster) {
            let laneIndex = laneEndTimes.findIndex(
                (laneEnd) => laneEnd <= entry.startMinutes,
            );

            if (laneIndex === -1) {
                laneIndex = laneEndTimes.length;
                laneEndTimes.push(entry.endMinutes);
            } else {
                laneEndTimes[laneIndex] = entry.endMinutes;
            }

            clusterEntries.push({
                ...entry,
                laneIndex,
            });
        }

        const laneCount = Math.max(1, laneEndTimes.length);
        const laneWidthPercent = 100 / laneCount;

        for (const entry of clusterEntries) {
            laidOutEntries.push({
                ...entry,
                laneCount,
                leftPercent: entry.laneIndex * laneWidthPercent,
                widthPercent: laneWidthPercent,
            });
        }
    }

    return laidOutEntries;
}

export function getCourseColor(courseCode) {
    const seedSource = String(courseCode ?? "");
    let hash = 0;

    for (let index = 0; index < seedSource.length; index += 1) {
        hash = (hash << 5) - hash + seedSource.charCodeAt(index);
        hash |= 0;
    }

    const hue = Math.abs(hash) % 360;
    return `hsl(${hue} 68% 46%)`;
}

export function getMeetingLocation(meeting) {
    const buildingCode = String(meeting?.building_code ?? "").trim();
    const room = String(meeting?.room ?? "").trim();

    if (!buildingCode && !room) return "";

    const combined = `${buildingCode} ${room}`.trim().toUpperCase();
    if (combined.includes("ONLINE")) return "Online";

    if (buildingCode && room) return `${buildingCode} ${room}`;
    if (buildingCode) return buildingCode;
    if (room) return room;

    return "";
}

function parseMeetingDaysToWeekdays(daysText, weekdayTokens) {
    if (!daysText || typeof daysText !== "string") return [];

    const compact = daysText.toUpperCase().replace(/\s+/g, "");
    const parsedTokens = [];

    for (let index = 0; index < compact.length; index += 1) {
        const current = compact[index];
        const next = compact[index + 1] ?? "";

        if (current === "T" && next === "H") {
            parsedTokens.push("R");
            index += 1;
            continue;
        }

        if (weekdayTokens[current]) {
            parsedTokens.push(current);
        }
    }

    return Array.from(new Set(parsedTokens.map((token) => weekdayTokens[token])));
}

export function buildScheduleSignature(schedule) {
    if (!Array.isArray(schedule?.sections)) {
        return `schedule-${Math.random().toString(36).slice(2)}`;
    }

    return schedule.sections
        .map((section) => `${section.course_code}-${section.section_code}`)
        .sort((left, right) => left.localeCompare(right))
        .join("|");
}

export function mapScheduleToCalendar(
    schedule,
    {
        weekdays,
        weekdayTokens = DEFAULT_WEEKDAY_TOKENS,
        minimumStartMinutes = 6 * 60,
        maximumEndMinutes = 22 * 60,
    },
) {
    const dayColumns = weekdays.map((day) => ({ day, entries: [] }));
    const entries = [];

    for (const section of schedule.sections ?? []) {
        for (const meeting of section.meetings ?? []) {
            const meetingStartMinutes = parseTimeToMinutes(meeting.start_time);
            const meetingEndMinutes = parseTimeToMinutes(meeting.end_time);
            const meetingDays = parseMeetingDaysToWeekdays(meeting.days, weekdayTokens);
            const meetingLocation = getMeetingLocation(meeting);

            if (
                meetingStartMinutes === null ||
                meetingEndMinutes === null ||
                meetingEndMinutes <= meetingStartMinutes ||
                meetingDays.length === 0
            ) {
                continue;
            }

            for (const day of meetingDays) {
                const dayIndex = weekdays.indexOf(day);
                if (dayIndex === -1) continue;

                entries.push({
                    dayIndex,
                    day,
                    courseCode: section.course_code,
                    sectionCode: section.section_code,
                    instructors: section.instructors ?? [],
                    avgProfGpaInClass:
                        typeof section.avg_prof_gpa_in_class === "number"
                            ? section.avg_prof_gpa_in_class
                            : null,
                    location: meetingLocation,
                    color: getCourseColor(section.course_code),
                    startMinutes: meetingStartMinutes,
                    endMinutes: meetingEndMinutes,
                    label: `${formatTimeFromMinutes(meetingStartMinutes)} - ${formatTimeFromMinutes(meetingEndMinutes)}`,
                });
            }
        }
    }

    const earliestStartMinutes = Math.min(
        ...entries.map((entry) => entry.startMinutes),
    );
    const latestEndMinutes = Math.max(...entries.map((entry) => entry.endMinutes));

    const visibleStartMinutes = entries.length
        ? Math.max(minimumStartMinutes, earliestStartMinutes - 60)
        : 8 * 60;
    const visibleEndMinutes = entries.length
        ? Math.min(maximumEndMinutes, latestEndMinutes + 60)
        : 18 * 60;

    const totalVisibleMinutes = Math.max(60, visibleEndMinutes - visibleStartMinutes);
    const startHour = Math.floor(visibleStartMinutes / 60);
    const endHour = Math.ceil(visibleEndMinutes / 60);
    const hourMarkers = Array.from(
        { length: endHour - startHour + 1 },
        (_, idx) => startHour + idx,
    );

    for (const entry of entries) {
        const clampedStartMinutes = Math.max(visibleStartMinutes, entry.startMinutes);
        const clampedEndMinutes = Math.min(visibleEndMinutes, entry.endMinutes);

        if (clampedEndMinutes <= clampedStartMinutes) continue;

        const topPercent =
            ((clampedStartMinutes - visibleStartMinutes) / totalVisibleMinutes) * 100;
        const heightPercent =
            (Math.max(20, clampedEndMinutes - clampedStartMinutes) /
                totalVisibleMinutes) *
            100;

        dayColumns[entry.dayIndex].entries.push({
            ...entry,
            topPercent,
            heightPercent,
        });
    }

    for (const column of dayColumns) {
        column.entries = withNonOverlappingLanes(column.entries);
    }

    return {
        startMinutes: visibleStartMinutes,
        endMinutes: visibleEndMinutes,
        hourMarkers,
        dayColumns,
    };
}
