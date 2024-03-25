<script setup lang="ts">

</script>


<template>

    <div class="center">
      <button @click="getPosts">Get posts</button>
      <h6 v-if="posts">Posts: {{ posts }}</h6>
    </div>
</template>

<script lang="ts">

export default {
  data() {
    return {
      posts: "null"
    }
  },
  methods: {
    async getPosts() {
      const input_data = {
        'wanted_classes': ['MATH240', 'CMSC216', 'CMSC250', "JOUR150"],
        'restrictions': {
          'minSeats': 0,
          'prohibitedInstructors': ['Wiseley Wong', 'Raluca Rosca', 'Paul Kline', 'Mohammad Nayeem Teli', 'Ilchul Yoon'],
          'prohibitedTimes': {},
          'required_classes': []
        }
      }
      const { data } = await this.axios.post('http://127.0.0.1:5000/schedule', input_data, {
        headers: {
          'Content-Type': 'application/json'
        }
      })
      console.log(data)
    }
  }
}
</script>

<style>
.center {
  margin: auto;
  text-align: center;
  width: 50%;
  border: 3px solid green;
  padding: 10px;
}

button {
  margin: auto;
  background-color: lightblue;
  color: black;
  font-size: 25px;
  margin: auto;
}
</style>