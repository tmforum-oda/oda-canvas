/* eslint-disable no-unused-vars */
const Service = require('./Service');
const logger = require('../logger');
const path = require('path');
const DataLoader = require('../utils/dataLoader');

// Initialize data loader with file watching
const dataPath = path.join(__dirname, '..', 'data', 'carbon-intensity-data.json');
const dataLoader = new DataLoader(dataPath);

// Load initial data
dataLoader.load();

// Start watching for file changes (hot-reload)
const ENABLE_FILE_WATCH = process.env.ENABLE_FILE_WATCH !== 'false'; // Default true
if (ENABLE_FILE_WATCH) {
  dataLoader.watch();
  logger.info('File watching enabled for real-time data updates');
} else {
  logger.info('File watching disabled');
}

// Log when data is reloaded
dataLoader.onChange((newData) => {
  logger.info(`Data reloaded: ${newData.length} PerformanceMeasurement records`);
});

// Helper function to get current data
const getData = () => dataLoader.getData();

/**
 * List or find PerformanceMeasurement objects (Carbon Intensity measurements)
 *
 * fields String Comma-separated properties to be provided in response (optional)
 * offset Integer Requested index for start of resources to be provided in response (optional)
 * limit Integer Requested number of resources to be provided in response (optional)
 * validForTimestamp String ISO 8601 timestamp to filter measurements by validFor period (optional)
 * region String Filter measurements by region tag (optional)
 * returns List
 **/
const listPerformanceMeasurement = (args, context) =>
  new Promise(
    async (resolve) => {
      try {
        let carbonIntensityData = getData();
        logger.info(`listPerformanceMeasurement: total ${carbonIntensityData.length} measurements`);

        // Extract query parameters (may be in args.dynamic from Controller)
        const validForTimestamp = args.validForTimestamp || (args.dynamic && args.dynamic.validForTimestamp);
        const region = args.region || (args.dynamic && args.dynamic.region);
        const fields = args.fields || (args.dynamic && args.dynamic.fields);
        const offset = args.offset || (args.dynamic && args.dynamic.offset);
        const limit = args.limit || (args.dynamic && args.dynamic.limit);

        logger.info(`Received parameters: validForTimestamp=${validForTimestamp}, region=${region}`);

        // Apply time-based filtering if validForTimestamp is provided
        if (validForTimestamp) {
          try {
            const targetTime = new Date(validForTimestamp);
            if (isNaN(targetTime.getTime())) {
              throw new Error('Invalid timestamp format');
            }

            // First try exact date/time match
            let filteredData = carbonIntensityData.filter(measurement => {
              const validFor = measurement.validFor;
              if (!validFor || !validFor.startDateTime || !validFor.endDateTime) {
                return false;
              }
              
              const startTime = new Date(validFor.startDateTime);
              const endTime = new Date(validFor.endDateTime);
              
              // Check if targetTime falls within the validFor period
              return targetTime >= startTime && targetTime < endTime;
            });

            logger.info(`Filtered by exact timestamp ${validForTimestamp}: ${filteredData.length} measurements`);

            // If no exact match found, try time-of-day matching (ignore date)
            if (filteredData.length === 0) {
              logger.info(`No exact date match found, attempting time-of-day matching`);
              
              const targetHour = targetTime.getUTCHours();
              const targetMinute = targetTime.getUTCMinutes();
              const targetSecond = targetTime.getUTCSeconds();

              // Find measurements that match by time-of-day
              const timeMatchedData = carbonIntensityData.filter(measurement => {
                const validFor = measurement.validFor;
                if (!validFor || !validFor.startDateTime || !validFor.endDateTime) {
                  return false;
                }
                
                const startTime = new Date(validFor.startDateTime);
                const endTime = new Date(validFor.endDateTime);
                
                // Extract time components from the measurement's time range
                const startHour = startTime.getUTCHours();
                const startMinute = startTime.getUTCMinutes();
                const endHour = endTime.getUTCHours();
                const endMinute = endTime.getUTCMinutes();
                
                // Create time-only comparisons (minutes since midnight)
                const targetTimeOfDay = targetHour * 60 + targetMinute;
                const startTimeOfDay = startHour * 60 + startMinute;
                const endTimeOfDay = endHour * 60 + endMinute;
                
                // Check if target time-of-day falls within the measurement's time-of-day range
                return targetTimeOfDay >= startTimeOfDay && targetTimeOfDay < endTimeOfDay;
              });

              if (timeMatchedData.length > 0) {
                logger.info(`Found ${timeMatchedData.length} measurements by time-of-day matching`);
                
                // Adjust the dates to match the requested date
                filteredData = timeMatchedData.map(measurement => {
                  const originalStart = new Date(measurement.validFor.startDateTime);
                  const originalEnd = new Date(measurement.validFor.endDateTime);
                  
                  // Calculate date offset between target and original
                  const targetDate = new Date(targetTime);
                  targetDate.setUTCHours(0, 0, 0, 0);
                  const originalDate = new Date(originalStart);
                  originalDate.setUTCHours(0, 0, 0, 0);
                  const dayOffset = Math.floor((targetDate - originalDate) / (24 * 60 * 60 * 1000));
                  
                  // Create adjusted copy with updated dates
                  const adjustedStart = new Date(originalStart);
                  adjustedStart.setUTCDate(adjustedStart.getUTCDate() + dayOffset);
                  const adjustedEnd = new Date(originalEnd);
                  adjustedEnd.setUTCDate(adjustedEnd.getUTCDate() + dayOffset);
                  
                  return {
                    ...measurement,
                    validFor: {
                      startDateTime: adjustedStart.toISOString(),
                      endDateTime: adjustedEnd.toISOString()
                    }
                  };
                });
                
                logger.info(`Adjusted dates to match requested date: ${targetTime.toISOString().split('T')[0]}`);
              } else {
                logger.info(`No time-of-day match found for ${targetHour}:${targetMinute.toString().padStart(2, '0')}`);
              }
            }

            carbonIntensityData = filteredData;
          } catch (err) {
            resolve(Service.rejectResponse(
              `Invalid validForTimestamp parameter: ${err.message}`,
              400
            ));
            return;
          }
        }

        // Apply region filtering if region is provided
        if (region) {
          carbonIntensityData = carbonIntensityData.filter(measurement => {
            const tag = measurement.tag || {};
            return tag.region === region;
          });
          logger.info(`Filtered by region ${region}: ${carbonIntensityData.length} measurements`);
        }

        // Apply pagination and field filtering
        const queryResult = Service.applyQuery(carbonIntensityData, { 
          fields: fields,
          offset: offset,
          limit: limit 
        });
        
        resolve(Service.createResponse(queryResult.data, queryResult.headerParams));

      } catch (e) {
        logger.error("listPerformanceMeasurement: error=" + e);
        resolve(Service.rejectResponse(
          e.message || 'Invalid input',
          e.status || 500,
        ));
      }
    }
  );

/**
 * Retrieves a PerformanceMeasurement by ID
 *
 * id String Identifier of the PerformanceMeasurement
 * fields String Comma-separated properties to be provided in response (optional)
 * returns PerformanceMeasurement
 **/
const retrievePerformanceMeasurement = (args, context) =>
  new Promise(
    async (resolve) => {
      try {
        logger.info(`retrievePerformanceMeasurement: id=${args.id}`);

        const carbonIntensityData = getData();
        
        // Find the measurement by ID
        const measurement = carbonIntensityData.find(m => m.id === args.id);

        if (!measurement) {
          const error = new Error(`PerformanceMeasurement with id ${args.id} not found`);
          error.statusCode = 404;
          resolve(Service.rejectResponse(error, 404));
          return;
        }

        // Apply field filtering if specified
        const filteredMeasurement = Service.applyFields(measurement, args.fields);
        
        resolve(Service.createResponse(filteredMeasurement));

      } catch (e) {
        logger.error("retrievePerformanceMeasurement: error=" + e);
        resolve(Service.rejectResponse(
          e.message || 'Invalid input',
          e.status || 500,
        ));
      }
    }
  );

/**
 * Update (PATCH) a PerformanceMeasurement by ID
 * Updates specific fields of an existing measurement in memory
 *
 * id String Identifier of the PerformanceMeasurement
 * performanceMeasurement Object Partial PerformanceMeasurement data to update
 * returns PerformanceMeasurement
 **/
const updatePerformanceMeasurement = (args, context) =>
  new Promise(
    async (resolve) => {
      try {
        logger.info(`updatePerformanceMeasurement: id=${args.id}`);

        const carbonIntensityData = getData();
        
        // Find the measurement by ID
        const index = carbonIntensityData.findIndex(m => m.id === args.id);

        if (index === -1) {
          const error = new Error(`PerformanceMeasurement with id ${args.id} not found`);
          error.statusCode = 404;
          resolve(Service.rejectResponse(error, 404));
          return;
        }

        // Get the update payload from request body
        const updateData = args.body || args.performanceMeasurement || {};

        // Merge the update data with existing measurement (shallow merge for top-level fields)
        carbonIntensityData[index] = {
          ...carbonIntensityData[index],
          ...updateData,
          id: args.id, // Ensure ID doesn't change
          href: carbonIntensityData[index].href // Preserve href
        };

        logger.info(`Updated PerformanceMeasurement ${args.id} successfully`);
        
        resolve(Service.createResponse(carbonIntensityData[index]));

      } catch (e) {
        logger.error("updatePerformanceMeasurement: error=" + e);
        resolve(Service.rejectResponse(
          e.message || 'Invalid input',
          e.status || 500,
        ));
      }
    }
  );

/**
 * Reload data from file
 * Admin operation to reload carbon-intensity-data.json into memory
 *
 * returns Object Status message
 **/
const reloadDataFromFile = (args, context) =>
  new Promise(
    async (resolve) => {
      try {
        logger.info('reloadDataFromFile: Reloading data from file');

        const previousCount = getData().length;
        
        // Use DataLoader's reload method
        dataLoader.load();
        
        const newCount = getData().length;

        const message = `Successfully reloaded ${newCount} measurements from file (previous: ${previousCount})`;
        logger.info(message);
        
        resolve(Service.createResponse({
          status: 'success',
          message: message,
          measurementCount: newCount,
          previousCount: previousCount
        }));

      } catch (e) {
        logger.error("reloadDataFromFile: error=" + e);
        resolve(Service.rejectResponse(
          e.message || 'Failed to reload data from file',
          e.status || 500,
        ));
      }
    }
  );

/**
 * Get data statistics
 * Admin operation to get information about loaded data
 *
 * returns Object Statistics
 **/
const getDataStatistics = (args, context) =>
  new Promise(
    async (resolve) => {
      try {
        logger.info('getDataStatistics: Getting data statistics');

        const carbonIntensityData = getData();

        const stats = {
          totalMeasurements: carbonIntensityData.length,
          dataFilePath: dataPath,
          fileWatchEnabled: ENABLE_FILE_WATCH,
          sampleIds: carbonIntensityData.slice(0, 5).map(m => m.id),
          locations: [...new Set(carbonIntensityData.map(m => m.tag?.location).filter(Boolean))],
          dateRange: {
            earliest: carbonIntensityData.reduce((min, m) => {
              const start = m.validFor?.startDateTime;
              return !min || (start && start < min) ? start : min;
            }, null),
            latest: carbonIntensityData.reduce((max, m) => {
              const end = m.validFor?.endDateTime;
              return !max || (end && end > max) ? end : max;
            }, null)
          }
        };

        resolve(Service.createResponse(stats));

      } catch (e) {
        logger.error("getDataStatistics: error=" + e);
        resolve(Service.rejectResponse(
          e.message || 'Failed to get statistics',
          e.status || 500,
        ));
      }
    }
  );

module.exports = {
  listPerformanceMeasurement,
  retrievePerformanceMeasurement,
  updatePerformanceMeasurement,
  reloadDataFromFile,
  getDataStatistics,
};
