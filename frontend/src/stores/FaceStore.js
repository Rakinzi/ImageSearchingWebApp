import { defineStore } from 'pinia';
import axios from 'axios';


export const useFaceStore = defineStore('faceStore', {
  state: () => ({
    faceData: null,
    isLoading: false,
  }),

  actions: {
    async loadFaceData() {
      if (!this.faceData) {  // Check if the data is already loaded
        this.isLoading = true;
        try {
          const response = await axios.get('http://127.0.0.1:5000/faces/process');
          this.faceData = response.data; // Store the response in Pinia state
        } catch (error) {
          console.error('Error fetching face data:', error);
        } finally {
          this.isLoading = false;
        }
      }
    },
  },
});
