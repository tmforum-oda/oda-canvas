/**
 * DataLoader - Utility for loading and watching JSON data files
 * Supports real-time file watching and callbacks on data changes
 */

const fs = require('fs');
const path = require('path');
const logger = require('../logger');

class DataLoader {
  /**
   * Initialize DataLoader with a file path
   * @param {string} filePath - Path to the JSON data file
   */
  constructor(filePath) {
    this.filePath = filePath;
    this.data = [];
    this.watchers = [];
    this.fileWatcher = null;
  }

  /**
   * Load data from the JSON file
   * @returns {Array} The loaded data
   */
  load() {
    try {
      if (!fs.existsSync(this.filePath)) {
        logger.warn(`Data file not found: ${this.filePath}`);
        this.data = [];
        return this.data;
      }

      const fileContent = fs.readFileSync(this.filePath, 'utf-8');
      this.data = JSON.parse(fileContent);
      logger.info(`Data loaded from ${path.basename(this.filePath)}: ${this.data.length} records`);
      return this.data;
    } catch (error) {
      logger.error(`Error loading data file: ${error.message}`);
      this.data = [];
      return this.data;
    }
  }

  /**
   * Get current data
   * @returns {Array} The current data
   */
  getData() {
    return this.data;
  }

  /**
   * Register a callback to be called when data changes
   * @param {Function} callback - Function to call with new data
   */
  onChange(callback) {
    if (typeof callback === 'function') {
      this.watchers.push(callback);
    }
  }

  /**
   * Start watching the file for changes
   */
  watch() {
    if (this.fileWatcher) {
      return; // Already watching
    }

    try {
      // Use fs.watch for file system monitoring
      this.fileWatcher = fs.watch(this.filePath, (eventType, filename) => {
        if (eventType === 'change') {
          // Debounce rapid changes
          this.debounceReload();
        }
      });

      logger.info(`Watching file for changes: ${path.basename(this.filePath)}`);
    } catch (error) {
      logger.error(`Error setting up file watcher: ${error.message}`);
    }
  }

  /**
   * Debounce file reload to avoid rapid successive reloads
   */
  debounceReload() {
    if (this.reloadTimeout) {
      clearTimeout(this.reloadTimeout);
    }

    this.reloadTimeout = setTimeout(() => {
      const previousLength = this.data.length;
      this.load();

      // Notify all watchers of the change
      this.watchers.forEach((callback) => {
        try {
          callback(this.data);
        } catch (error) {
          logger.error(`Error in onChange callback: ${error.message}`);
        }
      });

      logger.info(`File reloaded: ${previousLength} -> ${this.data.length} records`);
    }, 500); // 500ms debounce delay
  }

  /**
   * Stop watching the file
   */
  unwatch() {
    if (this.fileWatcher) {
      this.fileWatcher.close();
      this.fileWatcher = null;
      logger.info('Stopped watching file');
    }

    if (this.reloadTimeout) {
      clearTimeout(this.reloadTimeout);
      this.reloadTimeout = null;
    }
  }

  /**
   * Destroy the DataLoader and clean up resources
   */
  destroy() {
    this.unwatch();
    this.watchers = [];
    this.data = [];
  }
}

module.exports = DataLoader;
