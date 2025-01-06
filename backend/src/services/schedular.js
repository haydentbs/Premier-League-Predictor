const cron = require('node-cron');
const understatService = require('./understatService');

class Scheduler {
    start() {
        // Update results every hour
        cron.schedule('0 * * * *', async () => {
            console.log('Running results update...');
            try {
                await understatService.updateResults();
            } catch (error) {
                console.error('Error updating results:', error);
            }
        });

        // Update fixtures daily
        cron.schedule('0 0 * * *', async () => {
            console.log('Running fixtures update...');
            try {
                await understatService.updateFixtures();
            } catch (error) {
                console.error('Error updating fixtures:', error);
            }
        });

        // Initial data fetch
        this.initialFetch();
    }

    async initialFetch() {
        try {
            await understatService.updateAllData();
        } catch (error) {
            console.error('Error in initial fetch:', error);
        }
    }
}

module.exports = new Scheduler();