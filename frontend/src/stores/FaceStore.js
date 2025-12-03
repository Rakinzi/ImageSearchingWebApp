import { defineStore } from 'pinia';
import { apiService, handleApiError } from '../services/api.js';


export const useFaceStore = defineStore('faceStore', {
  state: () => ({
    faceData: null,
    allImages: null,
    clusters: null,
    persons: null,
    isLoading: false,
    isClustering: false,
    error: null,
    updatingFaces: {},
  }),

  actions: {
    async loadFaceData() {
      console.log('Loading face data...');
      this.isLoading = true;
      this.faceData = null;
      this.error = null;

      try {
        const response = await apiService.faces.list();
        this.faceData = response.data.data; // Extract inner data object
        console.log('Face data loaded:', this.faceData);
      } catch (error) {
        console.error('Error fetching face data:', error);
        const errorInfo = handleApiError(error);
        this.error = errorInfo.message;
      } finally {
        this.isLoading = false;
      }
    },

    async loadClusters() {
      console.log('Loading face clusters...');
      this.isLoading = true;
      this.clusters = null;
      this.error = null;

      try {
        const response = await apiService.faces.getClusters();
        this.clusters = response.data.data; // Extract inner data object
        console.log('Clusters loaded:', this.clusters);
      } catch (error) {
        console.error('Error fetching clusters:', error);
        const errorInfo = handleApiError(error);
        this.error = errorInfo.message;
      } finally {
        this.isLoading = false;
      }
    },

    async loadPersons() {
      console.log('Loading persons...');
      this.isLoading = true;
      this.persons = null;
      this.error = null;

      try {
        const response = await apiService.faces.getPersons();
        this.persons = response.data.data; // Extract inner data object
        console.log('Persons loaded:', this.persons);
      } catch (error) {
        console.error('Error fetching persons:', error);
        const errorInfo = handleApiError(error);
        this.error = errorInfo.message;
      } finally {
        this.isLoading = false;
      }
    },

    async triggerClustering() {
      console.log('Triggering face clustering...');
      this.isClustering = true;
      this.error = null;

      try {
        const response = await apiService.faces.cluster();
        console.log('Clustering triggered:', response.data);
        return response.data;
      } catch (error) {
        console.error('Error triggering clustering:', error);
        const errorInfo = handleApiError(error);
        this.error = errorInfo.message;
        throw error;
      } finally {
        this.isClustering = false;
      }
    },

    async loadImageData() {
      console.log('Loading image data...');
      this.isLoading = true;
      this.allImages = null;
      this.error = null;

      try {
        const response = await apiService.images.list();
        this.allImages = response.data.data; // Extract inner data object
        console.log('Images data loaded:', this.allImages);
      } catch (error) {
        console.error('Error fetching images data:', error);
        const errorInfo = handleApiError(error);
        this.error = errorInfo.message;
      } finally {
        this.isLoading = false;
      }
    },

    clearError() {
      this.error = null;
    },

    async assignPersonToFace(faceId, personName) {
      if (!faceId || !personName) {
        throw new Error('Face ID and person name are required');
      }

      this.error = null;
      this.updatingFaces = { ...this.updatingFaces, [faceId]: true };

      try {
        const payload = {
          person_name: personName,
          face_ids: [faceId],
        };

        const response = await apiService.faces.assignPerson(payload);
        const updatedFace = response.data?.updated_faces?.[0];

        if (updatedFace && this.faceData?.faces) {
          const faceIndex = this.faceData.faces.findIndex(face => face.id === faceId);
          if (faceIndex !== -1) {
            this.faceData.faces[faceIndex] = {
              ...this.faceData.faces[faceIndex],
              person_name: updatedFace.person_name,
              person_id: updatedFace.person_id,
              manual_verification: updatedFace.manual_verification,
              updated_at: updatedFace.updated_at,
            };
          }
        }

        return response.data;
      } catch (error) {
        const errorInfo = handleApiError(error);
        this.error = errorInfo.message;
        throw new Error(errorInfo.message);
      } finally {
        const { [faceId]: _, ...rest } = this.updatingFaces;
        this.updatingFaces = rest;
      }
    }
  },
});
