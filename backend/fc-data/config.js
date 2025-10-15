// Try to load .env in development if dotenv is installed. If not installed, continue silently.
try {
	// eslint-disable-next-line global-require
	require('dotenv').config();
} catch (e) {
	// dotenv not present; environment variables from OS/CI will still work
}


module.exports = {
	market: {
		HubUrl: "wss://fc-datahub.ssi.com.vn/",
		ApiUrl: "https://fc-data.ssi.com.vn/",
		ConsumerId: process.env.CONSUMER_ID,
		ConsumerSecret: process.env.CONSUMER_SECRET
	},
};
