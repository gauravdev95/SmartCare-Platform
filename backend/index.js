const express = require("express");
const cors = require("cors");
const axios = require("axios");

require('dotenv').config();
const logger = require('./utils/logger'); 

// Routes
const AdminRoute = require('./routes/admin.routes');
const UserRoute = require('./routes/user.routes');
const DoctorRoute = require('./routes/doctor.routes');
const AppoinmentRoute = require('./routes/appointment.routes');
const PaymentRoute = require('./routes/payments.routes');
const RatingRoute = require('./routes/ratings.routes');
const emailRoute= require('./routes/email.routes');
const connectDB = require('./config/db');
const PredictRoute = require('./routes/predict.route');


const app = express();
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Database
connectDB()
  .then(() => logger.info('Database connected successfully'))
  .catch((err) => logger.error('Database connection failed:', err.message));


app.get('/', (req, res) => {
  res.send('Backend API is running');
});



// Use Routes
app.use('/api/admin', AdminRoute);
app.use('/api/users', UserRoute);
app.use('/api/doctors', DoctorRoute);
app.use('/api/appointments', AppoinmentRoute);
app.use('/api/paypal', PaymentRoute);
app.use('/api/ratings', RatingRoute);
app.use('/api/send', emailRoute);
app.use('/api/report', PredictRoute);


// Logger Middleware
app.use((req, res, next) => {
  logger.info(`${req.method} ${req.url}`);
  next();
});

// Error Handling Middleware
app.use((err, req, res, next) => {
  logger.error(`${err.message}`);
  res.status(500).json({ message: 'Something went wrong' });
});


const PORT = process.env.PORT || 5000;

// Start Server
app.listen(PORT, () => {
  logger.info(`Server running at http://localhost:${PORT}`);
});
