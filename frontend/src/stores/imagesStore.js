import { defineStore } from 'pinia'
import { apiService, handleApiError, createUploadProgressHandler } from '../services/api.js'

export const useImagesStore = defineStore('images', {
  state: () => ({
    // Images data
    images: [],
    currentImage: null,
    totalImages: 0,

    // Pagination
    currentPage: 1,
    perPage: 20,
    totalPages: 0,

    // Filtering and sorting
    filters: {
      status: null,
      startDate: null,
      endDate: null,
      hasFaces: null,
      hasLocation: null,
      hasText: null
    },
    sortBy: 'created_at',
    sortOrder: 'desc',

    // Search
    searchQuery: '',
    searchResults: [],
    searchType: 'semantic',

    // Statistics
    stats: {
      totalImages: 0,
      processing: 0,
      withFaces: 0,
      withLocation: 0,
      withText: 0,
      totalSize: 0,
      avgProcessingTime: 0
    },

    // UI state
    loading: false,
    uploading: false,
    uploadProgress: 0,
    error: null
  }),

  getters: {
    // Get images list
    getImages: (state) => state.images,

    // Get current image
    getCurrentImage: (state) => state.currentImage,

    // Get statistics
    getStats: (state) => state.stats,

    // Check if loading
    isLoading: (state) => state.loading,

    // Check if uploading
    isUploading: (state) => state.uploading,

    // Get filtered and sorted images
    filteredImages: (state) => {
      let filtered = [...state.images]

      // Apply filters
      if (state.filters.status) {
        filtered = filtered.filter(img => img.status === state.filters.status)
      }

      if (state.filters.hasFaces !== null) {
        filtered = filtered.filter(img =>
          state.filters.hasFaces ? (img.metrics?.face_count > 0) : (img.metrics?.face_count === 0)
        )
      }

      if (state.filters.hasLocation !== null) {
        filtered = filtered.filter(img =>
          state.filters.hasLocation ? img.location : !img.location
        )
      }

      if (state.filters.hasText !== null) {
        filtered = filtered.filter(img =>
          state.filters.hasText ? img.extracted_text : !img.extracted_text
        )
      }

      return filtered
    }
  },

  actions: {
    // Load images with pagination and filters
    async loadImages(page = 1, resetList = false) {
      this.loading = true
      this.error = null

      try {
        const params = {
          page,
          per_page: this.perPage,
          sort_by: this.sortBy,
          sort_order: this.sortOrder,
          ...this.filters
        }

        const response = await apiService.images.list(params)
        const data = response.data.data

        if (resetList || page === 1) {
          this.images = data.items
        } else {
          // Append for infinite scroll
          this.images.push(...data.items)
        }

        this.currentPage = data.page
        this.totalPages = data.pages
        this.totalImages = data.total

        return data.items
      } catch (error) {
        const errorInfo = handleApiError(error)
        this.error = errorInfo.message
        throw new Error(errorInfo.message)
      } finally {
        this.loading = false
      }
    },

    // Load single image
    async loadImage(imageId) {
      this.loading = true
      this.error = null

      try {
        const response = await apiService.images.get(imageId)
        this.currentImage = response.data.data

        return this.currentImage
      } catch (error) {
        const errorInfo = handleApiError(error)
        this.error = errorInfo.message
        throw new Error(errorInfo.message)
      } finally {
        this.loading = false
      }
    },

    // Upload images
    async uploadImages(files, options = {}) {
      this.uploading = true
      this.uploadProgress = 0
      this.error = null

      try {
        const formData = new FormData()

        // Add files - v1 endpoint format
        files.forEach(file => {
          formData.append('files', file)
        })

        // V2 endpoint - add boolean options explicitly
        formData.append('extract_text', options.extractText !== false ? 'true' : 'false')
        formData.append('detect_faces', options.detectFaces !== false ? 'true' : 'false')
        formData.append('generate_embeddings', options.generateEmbeddings !== false ? 'true' : 'false')

        // Add metadata as JSON string
        if (options.metadata && Object.keys(options.metadata).length > 0) {
          formData.append('metadata', JSON.stringify(options.metadata))
        }

        // Debug: Log form data contents
        console.log('FormData contents:');
        for (let [key, value] of formData.entries()) {
          console.log(`${key}:`, value);
        }

        // Create progress handler
        const progressHandler = createUploadProgressHandler((progress) => {
          this.uploadProgress = progress
        })

        const response = await apiService.images.upload(formData, progressHandler)
        const uploadedImages = response.data.data

        // Add uploaded images to the list
        this.images.unshift(...uploadedImages)

        return uploadedImages
      } catch (error) {
        const errorInfo = handleApiError(error)
        this.error = errorInfo.message
        throw new Error(errorInfo.message)
      } finally {
        this.uploading = false
        this.uploadProgress = 0
      }
    },

    // Delete image
    async deleteImage(imageId) {
      this.loading = true
      this.error = null

      try {
        await apiService.images.delete(imageId)

        // Remove from local list
        this.images = this.images.filter(img => img.id !== imageId)

        // Clear current image if it was deleted
        if (this.currentImage?.id === imageId) {
          this.currentImage = null
        }

        return true
      } catch (error) {
        const errorInfo = handleApiError(error)
        this.error = errorInfo.message
        throw new Error(errorInfo.message)
      } finally {
        this.loading = false
      }
    },

    // Search images
    async searchImages(query, searchType = 'semantic', options = {}) {
      this.loading = true
      this.error = null

      try {
        const searchData = {
          query,
          search_type: searchType,
          limit: options.limit || 20,
          similarity_threshold: options.similarityThreshold || 0.8,
          filters: options.filters || {}
        }

        const response = await apiService.images.search(searchData)
        this.searchResults = response.data.data
        this.searchQuery = query
        this.searchType = searchType

        return this.searchResults
      } catch (error) {
        const errorInfo = handleApiError(error)
        this.error = errorInfo.message
        throw new Error(errorInfo.message)
      } finally {
        this.loading = false
      }
    },

    // Load user statistics
    async loadStats() {
      try {
        const response = await apiService.images.getStats()
        this.stats = response.data.data

        return this.stats
      } catch (error) {
        const errorInfo = handleApiError(error)
        console.warn('Failed to load stats:', errorInfo.message)
        return null
      }
    },

    // Reprocess image
    async reprocessImage(imageId) {
      this.loading = true
      this.error = null

      try {
        await apiService.images.reprocess(imageId)

        // Update image status in local list
        const imageIndex = this.images.findIndex(img => img.id === imageId)
        if (imageIndex !== -1) {
          this.images[imageIndex].status = 'pending'
        }

        // Update current image if it's the same
        if (this.currentImage?.id === imageId) {
          this.currentImage.status = 'pending'
        }

        return true
      } catch (error) {
        const errorInfo = handleApiError(error)
        this.error = errorInfo.message
        throw new Error(errorInfo.message)
      } finally {
        this.loading = false
      }
    },

    // Update filters
    setFilters(newFilters) {
      this.filters = { ...this.filters, ...newFilters }
    },

    // Update sorting
    setSorting(sortBy, sortOrder = 'desc') {
      this.sortBy = sortBy
      this.sortOrder = sortOrder
    },

    // Clear search results
    clearSearch() {
      this.searchResults = []
      this.searchQuery = ''
    },

    // Clear error
    clearError() {
      this.error = null
    },

    // Reset pagination
    resetPagination() {
      this.currentPage = 1
      this.totalPages = 0
    },

    // Load more images (for infinite scroll)
    async loadMore() {
      if (this.currentPage < this.totalPages && !this.loading) {
        await this.loadImages(this.currentPage + 1, false)
      }
    }
  }
})