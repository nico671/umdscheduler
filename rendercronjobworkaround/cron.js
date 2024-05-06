const cron = require('node-cron');
const https = require('https');

const backendURL = 'https://umdscheduler.onrender.com';

const job = cron.schedule('*/14 * * * *', async () => {

    console.log('Running cron job');
    https.get(backendURL, (res) => {
        console.log('Backend pinged');
    });

}
);

module.exports = { job };