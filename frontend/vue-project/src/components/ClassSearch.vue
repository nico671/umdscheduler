<script setup lang="ts">
import axios from 'axios';
</script>

<template>

    <div class="center">
        <h2>Search for Classes</h2>
        <input type="text" v-model="searchInput" placeholder="Search for classes..." />
        <li v-for=" message in filteredClasses" v-if="searching">
            <button @click="addClass(message)">{{ message }}</button>
        </li>
        <div class="item error" v-if="classInput && !filteredClasses.length">
            <p>No results found!</p>
        </div>

    </div>
    <div class="center">
        <h2>Selected Classes</h2>
        <div v-for="classInput in addedClasses">
            <button @click="removeClass(classInput)">{{ classInput }}</button>
        </div>
    </div>
    <div class="center">
        <h2>Click to generate Schedules</h2>
        <button @click="loadSchedules">Generate Schedules</button>
    </div>
    <div class="center">
        <h2>Generated Schedules</h2>
        <div v-if="generatedSchedules.length > 0" v-for="schedule in generatedSchedules">
                <button>{{ schedule }}</button>
        </div>
    </div>
   
</template>

<script lang="ts">

export default {
    computed: {
        filteredClasses(): string[] {
            return this.availableClassesUMD.filter((searchInput) => {
                return searchInput.toLowerCase().includes(this.searchInput.toLowerCase()) && !this.addedClasses.includes(searchInput);
            });
        },
        searching(): boolean {
            return this.searchInput.length > 0;
        }
    },
    data() {
        return {
            generatedSchedules: [] as any[],
            searchInput: '',
            addedClasses: [] as string[],
            classInput: '',
            availableClassesUMD: [] as any[],
        }
    },
    methods: {
        addClass: function(classInput: string) {
            this.addedClasses.push(classInput);
            this.searchInput = '';
        },
        removeClass(classInput: string) {
            const index = this.addedClasses.indexOf(classInput, 0);
            if (index > -1) {
                this.addedClasses.splice(index, 1);
            }
        },
        loadSchedules() {
            console.log(this.addedClasses)
            axios.post("http://127.0.0.1:5000/schedule", {
                wanted_classes: this.addedClasses,
                restrictions: {
                    'minSeats': 0,
                    'prohibitedInstructors': ["Mengyuan Chen", "Denitsa Yotova", 'Wiseley Wong', 'Raluca Rosca', 'Ilchul Yoon'],
                    'prohibitedTimes': [{ "day": "Th", "start": "8:00am", "end": "9:00am" }, { "day": "F", "start": "8:00am", "end": "11:00am" }, { "day": "W", "start": "8:00am", "end": "9:00am" }],
                    'required_classes': []
                },
            })
                .then((res) => {
                    const classes = res.data
                    this.generatedSchedules = classes;
                });
        },
        async loadClassList() {
            axios.get("https://api.umd.io/v1/courses/list", {
                params: {
                    sort: "sort=course_id,-credits",
                    semester: "202408"
                }
            })
                .then((res) => {
                    const classes = res.data.map((classObj: any) => classObj.course_id);
                    this.availableClassesUMD = classes;
                });
        }
    },
    beforeMount() {
        this.loadClassList();
    },
}
</script>