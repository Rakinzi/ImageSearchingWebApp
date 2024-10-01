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
        console.log('Loading face data...');
        this.isLoading = true;
        this.faceData = null;
        
        // Introduce a delay of 10 seconds before making the request
        await new Promise(resolve => setTimeout(resolve, 5000)); // 10,000ms = 10 seconds
    
        try {
          const response = await axios.get('http://127.0.0.1:5000/faces/process');
          this.faceData = response.data; // Store the response in Pinia state
          console.log('Face data loaded successfully');
        } catch (error) {
          console.error('Error fetching face data:', error);
        } finally {
          this.isLoading = false;
        }
      }
    }
    
  },
});
