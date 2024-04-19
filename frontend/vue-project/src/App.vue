<script lang="ts">
import ClassSearch from './components/ClassSearch.vue'
export default {
  components: {
    ClassSearch, 
  },
  data() {
    return {
      selectedClasses: [] as string[]
    }
  },
  methods: {
    addClass(value: string[]) {
      console.log(value)
      this.selectedClasses = value
    },
  }

}
</script>

<template>
  <div class="center">
    <ClassSearch ></ClassSearch>
  </div>
</template>

<style>
.center {
  margin: auto;
  text-align: center;
  width: 50%;
  border: 3px solid green;
  padding: 10px;
}
</style>